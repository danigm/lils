import re
import asyncio
import threading
import webbrowser


COMMANDRE = re.compile(r"^(?P<command>[^:]+):\s*(?P<args>([^\s]+\s*)+)$")
LISTENRE = re.compile(r"^wait-?(?P<command>[^:]*):\s*(?P<args>([^\s]+\s*)+)$")


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


# Listeners

def _start_listeners_loop():
    loop = asyncio.new_event_loop()
    t = threading.Thread(target=loop.run_forever)
    t.daemon = True
    t.start()
    return loop


_LOOP = _start_listeners_loop()
background_tasks = set()


async def wait_test(script, index, question, args):
    script.resolve(index, question)


async def wait_(script, index, question, args):
    t = int(args)
    await asyncio.sleep(t / 1000)
    script.resolve(index, question)


def run_listeners(command_line, script, index, question):
    if not command_line:
        return

    match = LISTENRE.match(command_line)
    if not match:
        return

    command = match.group("command")
    args = match.group("args")

    command = f"wait_{command}"
    if command in globals():
        fn = globals()[command]
        args = (script, index, question, args)
        task = asyncio.run_coroutine_threadsafe(fn(*args), _LOOP)
        task.add_done_callback(background_tasks.discard)
        background_tasks.add(task)
