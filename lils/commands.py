import re
import webbrowser


COMMANDRE = re.compile(r"^(?P<command>[^:]+):\s*(?P<args>([^\s]+\s*)+)$")


def open_url(args):
    webbrowser.open_new(args)


def run_command(command_line):
    if not command_line:
        return

    match = COMMANDRE.match(command_line)
    if not match:
        return

    command = match.group("command")
    args = match.group("args")

    if command == "url":
        open_url(args)
