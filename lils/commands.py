import re
import webbrowser
import subprocess


COMMANDRE = re.compile(r"^(?P<command>[^:]+):\s*(?P<args>([^\s]+\s*)+)$")


# Commands

def command_test(args):
    return ["test"] + args.split(" ")


def command_url(args):
    webbrowser.open_new(args)


def command_xdgopen(args):
    subprocess.run(["xdg-open", args])


def command_terminal(args):
    subprocess.run(["xdg-terminal"])


def command_launch(args):
    subprocess.run(["gtk-launch", f"{args}.desktop"])


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
