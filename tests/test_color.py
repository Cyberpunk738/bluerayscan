"""Both report commands respect the terminal's colour preference."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

import fixtures
from bluerayscan import cli


class TestColor(unittest.TestCase):
    def check_output(self, value, *, no_color=False, terminal=True):
        with tempfile.TemporaryDirectory() as root:
            source = f'AWS_KEY = "{fixtures.REALISTIC_AWS_KEY_ID}"\n'
            with open(os.path.join(root, "app.py"), "w", encoding="utf-8") as handle:
                handle.write(source)
            diff = (
                "diff --git a/app.py b/app.py\n"
                "--- a/app.py\n+++ b/app.py\n@@ -0,0 +1 @@\n"
                f"+{source}"
            )
            for argv in (["scan", root], ["history"]):
                with self.subTest(command=argv[0], value=value, no_color=no_color):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with contextlib.ExitStack() as stack:
                        stack.enter_context(patch.dict(os.environ))
                        os.environ.pop("NO_COLOR", None)
                        if value is not None:
                            os.environ["NO_COLOR"] = value
                        stack.enter_context(patch.object(stdout, "isatty", return_value=terminal))
                        stack.enter_context(contextlib.redirect_stdout(stdout))
                        stack.enter_context(contextlib.redirect_stderr(stderr))
                        stack.enter_context(patch("sys.stdin", io.StringIO(diff)))
                        code = cli.main(argv + (["--no-color"] if no_color else []))
                    self.assertEqual(code, cli.EXIT_FINDINGS, stderr.getvalue())
                    self.assertIn("SEC001", stdout.getvalue())
                    expected_colour = terminal and not no_color and not value
                    self.assertEqual("\x1b[" in stdout.getvalue(), expected_colour)

    def test_unset_no_color_keeps_terminal_colours(self):
        self.check_output(None)

    def test_empty_no_color_keeps_terminal_colours(self):
        self.check_output("")

    def test_nonempty_no_color_disables_terminal_colours(self):
        for value in ("1", "0", "false"):
            self.check_output(value)

    def test_explicit_flag_disables_terminal_colours(self):
        for value in (None, "", "1"):
            self.check_output(value, no_color=True)

    def test_redirected_output_has_no_ansi_escapes(self):
        for value in (None, "", "1"):
            self.check_output(value, terminal=False)

