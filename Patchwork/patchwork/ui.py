"""Terminal input/output."""

import sys

from . import textutil

try:  # line editing and history on Linux terminals
    import readline  # noqa: F401
except ImportError:  # pragma: no cover
    readline = None


class TerminalIO:
    def __init__(self, color=None, out=None):
        self.out = out or sys.stdout
        self.color = textutil.color_enabled(self.out) if color is None else color

    def write(self, text, kind=None, raw=False):
        if text is None:
            return
        if text == "":
            print("", file=self.out)
            return
        print(textutil.style(text if raw else textutil.wrap(text), kind, self.color), file=self.out)

    def ask(self, prompt="> "):
        """Read a line.  Raises EOFError on Ctrl-D."""
        p = textutil.style(prompt, "prompt", self.color)
        return input(p)

    def choose(self, prompt, options):
        if prompt:
            self.write(prompt)
        for idx, opt in enumerate(options, 1):
            self.write("  %d) %s" % (idx, opt))
        while True:
            try:
                ans = self.ask("choose> ").strip()
            except EOFError:
                return None
            if not ans or ans in ("0", "q", "cancel"):
                return None
            if ans.isdigit() and 1 <= int(ans) <= len(options):
                return int(ans) - 1
            for idx, opt in enumerate(options):
                if ans.lower() == opt.lower():
                    return idx
            self.write("Type a number from 1 to %d (or press Enter to cancel)." % len(options), "dim")


class ScriptIO:
    """Feeds pre-recorded input (for --script runs and tests) and records output."""

    def __init__(self, lines, echo=True, out=None):
        self.lines = list(lines)
        self.echo = echo
        self.out = out
        self.log = []

    def write(self, text, kind=None, raw=False):
        if text is None:
            return
        self.log.append(text)
        if self.echo:
            print(textutil.wrap(text) if text else "", file=self.out or sys.stdout)

    def ask(self, prompt="> "):
        if not self.lines:
            raise EOFError
        line = self.lines.pop(0)
        if self.echo:
            print(prompt + line, file=self.out or sys.stdout)
        return line

    def choose(self, prompt, options):
        if prompt:
            self.write(prompt)
        for idx, opt in enumerate(options, 1):
            self.write("  %d) %s" % (idx, opt))
        try:
            ans = self.ask("choose> ").strip()
        except EOFError:
            return None
        if ans.isdigit() and 1 <= int(ans) <= len(options):
            return int(ans) - 1
        return None

    def text(self):
        return "\n".join(self.log)
