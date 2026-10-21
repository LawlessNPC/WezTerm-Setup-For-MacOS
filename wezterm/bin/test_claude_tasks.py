"""Tests for claude-tasks: python3 -m unittest wezterm/bin/test_claude_tasks.py"""
import importlib.machinery
import importlib.util
import io
import json
import os
import re
import shutil
import struct
import tempfile
import time
import unittest
import zlib
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
loader = importlib.machinery.SourceFileLoader("claude_tasks", os.path.join(HERE, "claude-tasks"))
spec = importlib.util.spec_from_loader("claude_tasks", loader)
assert spec is not None
ct = importlib.util.module_from_spec(spec)
loader.exec_module(ct)


class CommandKeys(unittest.TestCase):
    def test_the_same_make_target_shares_a_key_across_log_paths(self):
        a = "cd ~/repos/x/apple && make check > /tmp/a/one.log 2>&1; echo $?"
        b = "cd /Users/me/repos/x/apple && make check > /private/tmp/b.log 2>&1"
        self.assertEqual(ct.command_key(a), ct.command_key(b))
        self.assertEqual(ct.command_key(a), "make check")

    def test_a_chain_keys_on_its_steps_in_order(self):
        c = "make check > a.log; echo; make test-watch > b.log"
        self.assertEqual(ct.steps(c), ["make check", "make test-watch"])

    def test_xcodebuild_keys_on_scheme_not_destination(self):
        a = "xcodebuild -project M.xcodeproj -scheme Momentum -destination 'platform=iOS Simulator,name=A' test"
        b = "xcodebuild -project M.xcodeproj -scheme Momentum -destination 'platform=macOS' test"
        self.assertEqual(ct.command_key(a), ct.command_key(b))

    def test_an_unrecognised_command_keys_with_paths_blanked(self):
        self.assertEqual(ct.command_key("sleep 60 > /tmp/x.log"), "sleep 60")
        self.assertEqual(ct.command_key("rsync -a ~/a /Volumes/b"), "rsync -a <path> <path>")


class Estimates(unittest.TestCase):
    def test_median_of_the_last_five_runs(self):
        b = ct.Board.__new__(ct.Board)
        b.history = {"make check": [(i, s) for i, s in enumerate([900, 300, 310, 320, 330, 340])]}
        self.assertEqual(b.estimate("make check > x.log"), 320)

    def test_a_chain_without_history_sums_its_parts(self):
        b = ct.Board.__new__(ct.Board)
        b.history = {"make check": [(1, 300)], "make test-watch": [(1, 60)]}
        self.assertEqual(b.estimate("make check; make test-watch"), 360)

    def test_no_history_is_no_estimate(self):
        b = ct.Board.__new__(ct.Board)
        b.history = {}
        self.assertIsNone(b.estimate("make audit"))


class TranscriptParsing(unittest.TestCase):
    def write(self, records):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False)
        for r in records:
            f.write(json.dumps(r) + "\n")
        f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def test_a_background_shell_gets_its_description_and_command(self):
        path = self.write([
            {"message": {"content": [{"type": "tool_use", "id": "tu1", "name": "Bash",
                                      "input": {"command": "make check", "description": "Run the gate",
                                                "run_in_background": True}}]}},
            {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu1",
                                      "content": "Command running in background with ID: babc123. Output…"}]}},
        ])
        t = ct.Transcript(path)
        t.refresh()
        self.assertEqual(t.info("babc123"), {"description": "Run the gate", "command": "make check", "kind": "shell"})

    def test_an_agent_and_its_completion(self):
        path = self.write([
            {"message": {"content": [{"type": "tool_use", "id": "tu2", "name": "Agent",
                                      "input": {"description": "Review", "prompt": "…"}}]}},
            {"message": {"content": [{"type": "tool_result", "tool_use_id": "tu2",
                                      "content": [{"type": "text", "text": "launched\nagentId: aff00 (internal)"}]}]}},
            {"message": {"content": "<task-notification>\n<task-id>aff00</task-id>\n<status>completed</status>"}},
        ])
        t = ct.Transcript(path)
        t.refresh()
        self.assertEqual(t.info("aff00")["description"], "Review")
        self.assertEqual(t.notes["aff00"], "completed")

    def test_a_foreground_command_is_pending_until_its_result(self):
        path = self.write([
            {"message": {"content": [{"type": "tool_use", "id": "tu3", "name": "Bash",
                                      "input": {"command": "ls", "description": "List files"}}]}},
        ])
        t = ct.Transcript(path)
        t.refresh()
        self.assertEqual(list(t.pending.values()), ["List files"])
        with open(path, "a") as f:
            f.write(json.dumps({"message": {"content": [{"type": "tool_result", "tool_use_id": "tu3", "content": "x"}]}}) + "\n")
        t.refresh()
        self.assertEqual(t.pending, {})

    def test_a_half_written_last_line_waits_for_the_next_refresh(self):
        path = self.write([])
        with open(path, "w") as f:
            f.write('{"message": {"content": "<task-notification><task-id>a1</task-id><status>comp')
        t = ct.Transcript(path)
        t.refresh()
        self.assertEqual(t.notes, {})
        with open(path, "a") as f:
            f.write('leted</status>"}}\n')
        t.refresh()
        self.assertEqual(t.notes, {"a1": "completed"})

    def test_notifications_queued_while_busy_are_read_too(self):
        path = self.write([
            {"type": "queue-operation", "timestamp": "2026-10-21T17:40:10.000Z", "operation": "enqueue",
             "content": "<task-notification>\n<task-id>a1</task-id>\n<status>completed</status>\n</task-notification>"},
            {"type": "attachment", "timestamp": "2026-10-21T17:41:00.000Z",
             "attachment": {"type": "queued_command", "prompt":
                            "<task-notification><task-id>b2</task-id><status>failed</status></task-notification>"}},
        ])
        t = ct.Transcript(path)
        t.refresh()
        self.assertEqual(t.notes, {"a1": "completed", "b2": "failed"})
        self.assertEqual(t.note_times["b2"] - t.note_times["a1"], 50)

    def test_notification_and_resume_times_are_recorded(self):
        path = self.write([
            {"timestamp": "2026-10-21T17:00:00.000Z", "message": {"content":
                "<task-notification><task-id>a1</task-id><status>completed</status></task-notification>"}},
            {"timestamp": "2026-10-21T17:05:00.000Z", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "s1",
                 "content": '{"success":true,"resumedAgentId":"a1"}'}]}},
        ])
        t = ct.Transcript(path)
        t.refresh()
        self.assertEqual(t.notes, {"a1": "completed"})
        self.assertEqual(t.resumes["a1"] - t.note_times["a1"], 300)

    def test_the_session_folder_is_remembered_for_the_project_label(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"cwd": "/Users/me/hilltop-war", "message": {"content": [
                {"type": "tool_use", "id": "t1", "name": "Agent", "input": {"description": "Review"}}]}}) + "\n")
            f.write(json.dumps({"cwd": "/Users/me/hilltop-war/sub", "message": {"content": [
                {"type": "tool_use", "id": "t2", "name": "Agent", "input": {"description": "Later"}}]}}) + "\n")
        t = ct.Transcript(f.name)
        t.refresh()
        os.unlink(f.name)
        self.assertEqual(t.cwd, "/Users/me/hilltop-war")


class Placement(unittest.TestCase):
    def test_the_idle_strip_takes_rows_never_columns(self):
        self.assertEqual(ct.placement(120, "strip"), ("bottom", ct.STRIP_ROWS))
        self.assertEqual(ct.placement(300, "strip"), ("bottom", ct.STRIP_ROWS))

    def test_the_full_panel_goes_right_only_when_claude_keeps_its_width(self):
        self.assertEqual(ct.placement(261, "auto"), ("right", ct.PANEL_COLS))
        wide_enough = ct.MIN_CLAUDE_COLS + ct.PANEL_COLS + 1
        self.assertEqual(ct.placement(wide_enough, "auto"), ("right", ct.PANEL_COLS))
        self.assertEqual(ct.placement(wide_enough - 1, "auto"), ("bottom", ct.PANEL_ROWS))

    def test_claude_never_drops_below_the_diff_panel_minimum(self):
        for cols in range(60, 400):
            direction, cells = ct.placement(cols, "auto")
            if direction == "right":
                self.assertGreaterEqual(cols - cells - 1, 144)


class Labels(unittest.TestCase):
    def test_project_label_prefers_the_session_folder(self):
        self.assertEqual(ct.project_label("-Users-me-hilltop-war", "/Users/me/hilltop-war"), "hilltop-war")

    def test_project_name_keeps_hyphenated_names_whole(self):
        home = os.path.expanduser("~").replace("/", "-")
        self.assertEqual(ct.project_name(home + "-hilltop-war"), "hilltop-war")
        self.assertEqual(ct.project_name(home), "~")

    def test_clock_is_twelve_hour_without_a_leading_zero(self):
        t = time.mktime((2026, 10, 21, 13, 4, 9, 0, 0, -1))
        self.assertEqual(ct.clock(t), "1:04 PM")
        self.assertEqual(ct.clock(t, seconds=True), "1:04:09 PM")

    def test_when_says_since_while_running_and_done_after(self):
        t = time.mktime((2026, 10, 21, 13, 0, 0, 0, 0, -1))
        self.assertEqual(ct.when({"state": "running", "start": t, "end": None}, t), "since 1:00 PM")
        self.assertEqual(ct.when({"state": "done", "start": t, "end": t + 240}, t), "done 1:04 PM")
        self.assertEqual(ct.when({"state": "failed", "start": t, "end": t + 60}, t), "failed 1:01 PM")


class AgentActivity(unittest.TestCase):
    def test_describe_tool_names_the_key_argument(self):
        self.assertEqual(ct.describe_tool({"name": "Read", "input": {"file_path": "/a/b/main.gd"}}), "Read: main.gd")
        self.assertEqual(ct.describe_tool({"name": "WebFetch", "input": {"url": "https://x.dev/a"}}), "WebFetch: https://x.dev/a")
        self.assertEqual(ct.describe_tool({"name": "TaskList", "input": {}}), "TaskList")

    def test_agent_detail_reads_the_latest_assistant_block(self):
        rows = [
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Grep", "input": {"pattern": "def scan"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
            {"type": "assistant", "message": {"content": [{"type": "thinking", "thinking": ""}]}},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write("\n".join(json.dumps(r) for r in rows) + "\n")
        try:
            self.assertEqual(ct.agent_detail(f.name), "thinking…")
            with open(f.name, "a") as g:
                g.write(json.dumps({"type": "assistant", "message": {"content": [
                    {"type": "text", "text": "Found it.\nMore."}]}}) + "\n")
            self.assertEqual(ct.agent_detail(f.name), "writing: Found it.")
            with open(f.name, "a") as g:
                g.write(json.dumps({"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "name": "SubagentHandback", "input": {}}]}}) + "\n")
            self.assertEqual(ct.agent_detail(f.name), "handed back its report")
        finally:
            os.unlink(f.name)


class TerminalSafety(unittest.TestCase):
    def test_control_sequences_from_transcripts_are_neutralised(self):
        osc52 = "\x1b]52;c;ZXZpbA==\x07"          # write the clipboard
        title = "\x1b]0;pwned\x07"                 # retitle the window
        c1 = "\x9b2J"                               # 8-bit CSI: clear screen
        for evil in (osc52, title, c1, "a\rb", "x\x00y"):
            out = ct.clip("Read: " + evil, 200)
            self.assertIsNone(ct.CONTROL_RE.search(out), repr(out))
        self.assertEqual(ct.clip("tab\there", 50), "tab here")

    def test_agent_activity_is_safe_once_drawn(self):
        block = {"name": "WebFetch", "input": {"url": "https://x.dev/\x1b]52;c;ZXZpbA==\x07"}}
        self.assertIsNone(ct.CONTROL_RE.search(ct.clip(ct.describe_tool(block), 200)))


class AgentState(unittest.TestCase):
    NOTE = 1000.0

    def test_a_finished_agent_stays_done(self):
        self.assertEqual(ct.agent_state("completed", self.NOTE, None, self.NOTE - 2, self.NOTE + 60), "done")

    def test_a_resumed_agent_is_running_again(self):
        self.assertEqual(ct.agent_state("completed", self.NOTE, self.NOTE + 30, self.NOTE + 31, self.NOTE + 40), "running")

    def test_log_writes_well_after_the_notification_mean_running(self):
        late = self.NOTE + ct.RESUME_SLACK + 5
        self.assertEqual(ct.agent_state("completed", self.NOTE, None, late, late + 1), "running")

    def test_it_is_done_again_once_a_newer_notification_arrives(self):
        second = self.NOTE + 120
        self.assertEqual(ct.agent_state("completed", second, self.NOTE + 30, second - 1, second + 5), "done")

    def test_without_a_notification_time_the_note_is_trusted(self):
        self.assertEqual(ct.agent_state("completed", None, None, self.NOTE + 999, self.NOTE + 1000), "done")


class Scope(unittest.TestCase):
    TASKS = [{"id": "a", "session": "s1"}, {"id": "b", "session": "s2"}]

    def test_a_docked_panel_shows_its_own_session(self):
        self.assertEqual([t["id"] for t in ct.in_scope(self.TASKS, "s1")], ["a"])

    def test_all_sessions_on_toggle_or_without_a_session(self):
        self.assertEqual(len(ct.in_scope(self.TASKS, "s1", show_all=True)), 2)
        self.assertEqual(len(ct.in_scope(self.TASKS, None)), 2)

    def test_only_background_work_counts_as_busy(self):
        self.assertTrue(ct.busy([{"state": "running", "kind": "agent"}]))
        self.assertTrue(ct.busy([{"state": "running", "kind": "shell"}]))
        self.assertFalse(ct.busy([{"state": "running", "kind": "shell", "foreground": True}]))
        self.assertFalse(ct.busy([{"state": "done", "kind": "shell"}]))


class FindingTheClaudePane(unittest.TestCase):
    PANES = [{"pane_id": 0, "tab_id": 0, "tty_name": "/dev/ttys000"},
             {"pane_id": 2, "tab_id": 1, "tty_name": "/dev/ttys005"}]

    def test_pane_for_tty(self):
        self.assertEqual(ct.pane_for_tty(self.PANES, "/dev/ttys005"), 2)
        self.assertIsNone(ct.pane_for_tty(self.PANES, "/dev/ttys099"))
        self.assertIsNone(ct.pane_for_tty(self.PANES, ""))

    def test_without_tmux_wezterm_pane_is_used_when_it_exists(self):
        self.assertEqual(ct.claude_pane(self.PANES, {"WEZTERM_PANE": "2"}), 2)

    def test_parse_args(self):
        self.assertEqual(ct.parse_args([]), {"mode": "manual", "pane": None, "session": None})
        self.assertEqual(ct.parse_args(["--strip", "--pane", "7", "--session", "abc"]),
                         {"mode": "strip", "pane": "7", "session": "abc"})
        self.assertEqual(ct.parse_args(["--auto"])["mode"], "auto")
        self.assertEqual(ct.parse_args(["--session-start"])["mode"], "session-start")


# A made-up palette and pattern: no real game image goes in the repo.
PALETTE = [(0x62, 0x9c, 0x83), (200, 30, 30), (30, 200, 30), (30, 30, 200)]


def pattern(w, h):
    """Palette indexes; the bottom half (frame 1) differs from the top."""
    return [[(x + y + (y >= 32)) % 4 for x in range(w)] for y in range(h)]


def indexed_png(w, h, pixels, trns=(0,)):
    """A 4bpp indexed PNG built by hand, cycling through all five row filters.
    tRNS is shorter than the palette, so only index 0 is transparent."""
    stride = (w + 1) // 2
    raw, prev = b"", bytes(stride)
    for y in range(h):
        row = pixels[y] + [0]
        line = bytes((row[x] << 4) | row[x + 1] for x in range(0, w, 2))
        kind, out = y % 5, bytearray()
        for x in range(stride):
            a, b = (line[x - 1] if x else 0), prev[x]
            c = prev[x - 1] if x else 0
            out.append((line[x] - (0, a, b, (a + b) // 2, ct.paeth(a, b, c))[kind]) & 255)
        raw += bytes([kind]) + bytes(out)
        prev = line

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    data = zlib.compress(raw)
    return (ct.PNG_SIG + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 4, 3, 0, 0, 0))
            + chunk(b"PLTE", bytes(v for rgb in PALETTE for v in rgb)) + chunk(b"tRNS", bytes(trns))
            + chunk(b"IDAT", data[:7]) + chunk(b"IDAT", data[7:]) + chunk(b"IEND", b""))


def rgba(index):
    return bytes(PALETTE[index]) + (b"\0" if index == 0 else b"\xff")


class PartyIcons(unittest.TestCase):
    def test_a_4bpp_indexed_png_decodes_and_round_trips(self):
        px = pattern(32, 64)
        w, h, rows = ct.png_decode(indexed_png(32, 64, px))
        self.assertEqual((w, h), (32, 64))
        self.assertEqual(rows, [b"".join(rgba(i) for i in r) for r in px])
        self.assertEqual(rows[0][:4], b"\x62\x9c\x83\x00")  # index 0: transparent teal
        self.assertEqual(ct.png_decode(ct.png_encode(rows)), (32, 64, rows))

    def test_an_odd_width_keeps_its_high_nibble_first_order(self):
        px = [[1, 2, 3, 0, 1], [3, 3, 2, 2, 1]]
        self.assertEqual(ct.png_decode(indexed_png(5, 2, px))[2],
                         [b"".join(rgba(i) for i in r) for r in px])

    def test_frames_split_and_scale_crisply(self):
        f0, f1 = ct.icon_frames(ct.png_decode(indexed_png(32, 64, pattern(32, 64))))
        self.assertNotEqual(f0, f1)
        big = ct.png_decode(ct.png_encode(ct.png_scale(f1, 2)))
        self.assertEqual(big[:2], (64, 64))
        for y in (0, 17, 31):
            for x in (0, 9, 31):
                pixel = f1[y][4 * x:4 * x + 4]
                for dy in (0, 1):
                    self.assertEqual(big[2][2 * y + dy][8 * x:8 * x + 8], pixel * 2)

    def test_a_sprite_is_centred_on_a_gutter_sized_canvas(self):
        f0 = ct.icon_frames(ct.png_decode(indexed_png(32, 64, pattern(32, 64))))[0]
        canvas = ct.png_place(f0, 1, 65, 58)
        self.assertEqual((len(canvas), len(canvas[0])), (58, 65 * 4))
        self.assertEqual(canvas[13][16 * 4:48 * 4], f0[0])
        self.assertEqual(canvas[0], b"\0" * 65 * 4)

    def test_anything_else_is_refused(self):
        for bad in (b"", b"GIF89a", ct.PNG_SIG + b"\0\0\0\0IEND"):
            with self.assertRaises(ValueError):
                ct.png_decode(bad)
        with self.assertRaises(ValueError):
            ct.icon_frames(ct.png_decode(indexed_png(5, 2, [[0] * 5] * 2)))

    def test_the_dex_has_386_folder_names(self):
        self.assertEqual(len(ct.DEX_NAMES), 386)
        self.assertEqual(len(set(ct.DEX_NAMES)), 386)
        self.assertEqual([ct.DEX_NAMES[n - 1] for n in (1, 29, 32, 83, 122, 201, 250, 386)],
                         ["bulbasaur", "nidoran_f", "nidoran_m", "farfetchd", "mr_mime",
                          "unown/a", "ho_oh", "deoxys"])

    def test_each_task_keeps_one_pokemon(self):
        self.assertEqual(ct.sprite_for("babc123"), ct.sprite_for("babc123"))
        seen = {ct.sprite_for("task%d" % i) for i in range(3000)}
        self.assertTrue(seen <= set(range(1, 387)))
        self.assertGreater(len(seen), 350)  # spread over the whole dex


class SpriteDrawing(unittest.TestCase):
    def test_it_bobs_while_running_and_stands_still_once_ended(self):
        run = {"state": "running"}
        self.assertEqual(ct.sprite_frame(run, 10.5 * ct.SPRITE_TICK), 0)
        self.assertEqual(ct.sprite_frame(run, 11.5 * ct.SPRITE_TICK), 1)
        for state in ("done", "failed", "killed", "stale"):
            self.assertEqual(ct.sprite_frame({"state": state}, 11.5 * ct.SPRITE_TICK), 0)

    def test_the_escape_keeps_the_cursor_still_and_carries_only_base64(self):
        esc = ct.image_escape(b"\x89PNG not really", 65, 58)
        self.assertTrue(esc.startswith("\x1b]1337;File=inline=1;"))
        self.assertIn(";width=65px;height=58px;preserveAspectRatio=0;doNotMoveCursor=1:", esc)
        self.assertTrue(esc.endswith("\x07"))
        self.assertRegex(esc.split(":", 1)[1][:-1], r"^[A-Za-z0-9+/=]+$")

    def test_the_scale_is_whole_and_fits_two_rows(self):
        self.assertEqual(ct.sprite_scale(8, 17), 1)
        self.assertEqual(ct.sprite_scale(13, 29), 2)  # 64x48 in a 65x58 gutter
        self.assertEqual(ct.sprite_scale(16, 34), 2)
        self.assertEqual(ct.sprite_scale(26, 58), 4)
        self.assertEqual(ct.sprite_scale(0, 0), 0)    # the terminal won't say
        self.assertEqual(ct.sprite_scale(6, 14), 0)   # too small for 32 px
        for cw, ch in ((8, 17), (13, 29), (26, 58)):
            k = ct.sprite_scale(cw, ch)
            self.assertLessEqual(k * ct.SHOWN_W, ct.GUTTER * cw)
            self.assertLessEqual(k * ct.SHOWN_H, 2 * ch)

    def test_icons_are_cut_to_what_they_draw_with_the_bob_kept(self):
        blank, dot = b"\0" * 4, b"\x10\x20\x30\xff"
        f0 = [blank * 32 for _ in range(32)]
        f1 = list(f0)
        for y in range(8, 20):
            f0[y] = blank * 10 + dot * 10 + blank * 12
            f1[y + 1] = f0[y]  # frame 1 sits a row lower
        c0, c1 = ct.icon_crop([f0, f1])
        self.assertEqual((len(c0), len(c0[0]) // 4), (13, 10))
        self.assertEqual((c0[0], c0[12]), (dot * 10, blank * 10))
        self.assertEqual((c1[0], c1[12]), (blank * 10, dot * 10))

    def test_sprites_only_in_wezterm_and_with_an_off_switch(self):
        self.assertTrue(ct.sprites_enabled({"TERM_PROGRAM": "WezTerm"}))
        self.assertFalse(ct.sprites_enabled({"TERM_PROGRAM": "WezTerm", "CLAUDE_TASKS_SPRITES": "0"}))
        self.assertFalse(ct.sprites_enabled({"TERM_PROGRAM": "tmux"}))
        self.assertFalse(ct.sprites_enabled({}))

    def test_the_cell_size_of_something_that_is_not_a_terminal_is_unknown(self):
        with tempfile.TemporaryFile() as f:
            self.assertEqual(ct.cell_px(f.fileno()), (0, 0))


class FakeArt:
    def fits(self):
        return True

    def escape(self, task, now):
        return "<sprite %s>" % task["id"]


def task(tid, description, state="running", detail="Read: main.gd"):
    now = time.time()
    return {"id": tid, "description": description, "state": state, "kind": "agent",
            "agent_type": "Explore", "label": "proj", "project": "-proj", "command": "",
            "start": now - 30, "end": None if state == "running" else now, "detail": detail}


def painted(fn, *args):
    """What a render wrote: ({row: plain text}, {row: sprite}, raw output)."""
    buf = io.StringIO()
    with mock.patch("sys.stdout", buf):
        fn(*args)
    out = buf.getvalue()
    parts = re.split(r"\x1b\[(\d+);(\d+)H", out)
    rows, sprites = {}, {}
    for y, x, seg in zip(parts[1::3], parts[2::3], parts[3::3]):
        assert x == "1", "every row and sprite starts at column 1"
        seg = seg.replace("\x1b[?2026l", "")
        if seg.startswith("<sprite"):
            sprites[int(y)] = seg
        else:
            rows[int(y)] = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", seg)
    return rows, sprites, out


class SpriteLayout(unittest.TestCase):
    def board(self):
        b = ct.Board.__new__(ct.Board)
        b.history = {}
        return b

    def test_task_text_never_starts_in_the_sprite_gutter(self):
        tasks = [task("a1", "alpha"), task("b2", "beta", "done", detail="")]
        rows, sprites, out = painted(ct.render, self.board(), tasks, 0, 60, 14, 0, "", "", FakeArt())
        alpha = next(y for y, t in rows.items() if "alpha" in t)
        beta = next(y for y, t in rows.items() if "beta" in t)
        self.assertEqual(sprites, {alpha: "<sprite a1>", beta: "<sprite b2>"})
        for y in range(alpha, beta + 2):  # both blocks: title, meta (and activity)
            self.assertEqual(rows[y][:ct.GUTTER], " " * ct.GUTTER, y)
            self.assertNotEqual(rows[y][ct.GUTTER:].strip(), "", y)
        self.assertTrue(rows[alpha][ct.GUTTER:].startswith(" ⠋ alpha"))
        self.assertGreater(out.index("<sprite"), out.rindex("\x1b[J"))  # sprites after all text

    def test_a_sprite_is_dropped_rather_than_overlap_the_footer(self):
        tasks = [task("t%d" % i, "task %d" % i) for i in range(5)]
        height = 14
        rows, sprites, _ = painted(ct.render, self.board(), tasks, 0, 60, height, 0, "", "", FakeArt())
        self.assertTrue(sprites)
        for y in sprites:
            self.assertLessEqual(y + 1, height - 2)
        self.assertIn("task 3", rows[12])           # its title made it
        self.assertNotIn(12, sprites)               # but not room for its sprite

    def test_without_sprites_the_layout_is_unchanged(self):
        rows, sprites, _ = painted(ct.render, self.board(), [task("a1", "alpha")], 0, 60, 14, 0, "", "")
        self.assertEqual(sprites, {})
        self.assertTrue(rows[3].startswith(" ⠋ alpha"))

    def test_the_strip_keeps_five_rows_with_two_tasks_beside_sprites(self):
        tasks = [task("a1", "alpha"), task("b2", "beta", "done"), task("c3", "gamma")]
        rows, sprites, _ = painted(ct.render_strip, tasks, 80, ct.STRIP_ROWS, 0, "", FakeArt())
        self.assertEqual(sorted(rows), [1, 2, 3, 4, 5])
        self.assertEqual(sprites, {2: "<sprite a1>", 4: "<sprite b2>"})
        for y in (2, 3, 4, 5):
            self.assertEqual(rows[y][:ct.GUTTER], " " * ct.GUTTER)
        self.assertIn("proj · Explore · since", rows[3])

    def test_the_strip_without_sprites_lists_one_task_per_line(self):
        tasks = [task("t%d" % i, "task %d" % i) for i in range(6)]
        rows, sprites, _ = painted(ct.render_strip, tasks, 80, ct.STRIP_ROWS, 0, "")
        self.assertEqual(sprites, {})
        self.assertEqual([("task %d" % (y - 2)) in rows[y] for y in (2, 3, 4, 5)], [True] * 4)


class SpriteLoading(unittest.TestCase):
    def setUp(self):
        self.src, self.cache = tempfile.mkdtemp(), tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.src)
        self.addCleanup(shutil.rmtree, self.cache)
        self.task = {"id": "babc123", "state": "running"}
        self.dex = ct.sprite_for(self.task["id"])

    def serve(self):
        """A stand-in for the icon host: a file:// URL with one synthetic icon."""
        folder = os.path.join(self.src, ct.DEX_NAMES[self.dex - 1])
        os.makedirs(folder)
        with open(os.path.join(folder, "icon.png"), "wb") as f:
            f.write(indexed_png(32, 64, pattern(32, 64)))
        return "file://" + self.src + "/%s/icon.png"

    def test_an_icon_loads_in_the_background_and_is_cached_on_disk(self):
        art = ct.Sprites(self.cache, self.serve())
        art.cell = (13, 29)
        self.assertEqual(art.escape(self.task, 0.0), "")  # not here yet: a blank gap
        deadline = time.time() + 5
        while not art.escape(self.task, 0.0) and time.time() < deadline:
            time.sleep(0.01)
        esc = art.escape(self.task, 0.0)
        self.assertIn("width=65px;height=58px", esc)
        self.assertNotEqual(esc, art.escape(self.task, ct.SPRITE_TICK * 1.5))  # it bobs
        self.assertTrue(os.path.exists(os.path.join(self.cache, "%03d.png" % self.dex)))
        offline = ct.Sprites(self.cache, "file:///nonexistent/%s.png")
        offline.load(self.dex)
        self.assertIn(self.dex, offline.frames)  # the second panel reads the cache

    def test_a_failed_load_is_no_sprite_and_is_retried_only_later(self):
        art = ct.Sprites(self.cache, "file:///nonexistent/%s.png")
        art.cell = (13, 29)
        art.load(self.dex)  # raises nothing
        self.assertNotIn(self.dex, art.frames)
        self.assertEqual(art.escape(self.task, 100.0), "")
        self.assertEqual(art.escape(self.task, 101.0), "")
        self.assertEqual(art.asked[self.dex], 100.0)
        art.escape(self.task, 100.0 + ct.SPRITE_RETRY)
        self.assertEqual(art.asked[self.dex], 100.0 + ct.SPRITE_RETRY)

    def test_a_damaged_cache_file_is_fetched_again(self):
        with open(os.path.join(self.cache, "%03d.png" % self.dex), "wb") as f:
            f.write(b"\x89PNG truncated")
        self.assertEqual(len(ct.load_icon(self.dex, self.cache, self.serve())), 2)


if __name__ == "__main__":
    unittest.main()
