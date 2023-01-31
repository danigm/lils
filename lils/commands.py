import re
import webbrowser


COMMANDRE = re.compile(r"^(?P<command>[^:]+):\s*(?P<args>([^\s]+\s*)+)$")


# Commands

def command_test(args):
    return ["test"] + args.split(" ")


def command_url(args):
    webbrowser.open_new(args)


def run_command(command_line):
    if not command_line:
        return

    match = COMMANDRE.match(command_line)
    if not match:
        return

    command = match.group("command")
    args = match.group("args")

    command = f"command_{command}"
    if command in globals():
        globals()[command](args)
