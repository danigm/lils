import re
import asyncio
import threading
import subprocess

import pathlib


LISTENRE = re.compile(r"^wait-?(?P<command>[^:]*):\s*(?P<args>([^\s]+\s*)+)$")


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


async def wait_newfile(script, index, question, path):
    """
    Wait for file creation
    """

    p = pathlib.Path(path)

    while True:
        if script._question != question:
            return

        if p.exists():
            break
        await asyncio.sleep(0.2)
    script.resolve(index, question)


async def wait_infile(script, index, question, args):
    """
    Wait for text inside a file, the text should be literal
    """

    path, *rest = args.split(" ")
    line = " ".join(rest)
    p = pathlib.Path(path)

    while True:
        if script._question != question:
            return

        content = ""
        with open(path) as f:
            content = f.read()
        if p.exists() and line in content:
            break
        await asyncio.sleep(1)
    script.resolve(index, question)


async def wait_ps(script, index, question, args):
    """
    Wait for a line of text appearing in ps -eaf
    """

    while True:
        if script._question != question:
            return

        content = subprocess.check_output(["ps", "-eaf"])
        if args in content.decode():
            break
        await asyncio.sleep(1)

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
        task.add_done_callback(discard_task)
        background_tasks.add(task)


def discard_task(task):
    background_tasks.discard(task)
