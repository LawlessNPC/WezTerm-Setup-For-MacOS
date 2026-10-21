"""Tests for claude-tasks: python3 -m unittest wezterm/bin/test_claude_tasks.py"""
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import time
import unittest

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


if __name__ == "__main__":
    unittest.main()
