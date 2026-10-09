"""Tests for claude-tasks: python3 -m unittest wezterm/bin/test_claude_tasks.py"""
import importlib.machinery
import importlib.util
import json
import os
import tempfile
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


if __name__ == "__main__":
    unittest.main()
