import time
import pytest
from unittest.mock import patch

from .utils import ink


@patch("lils.commands.command_test")
@patch("lils.commands.command_url")
def test_basic_command(url, test):
    script = ink(f"command-01")
    script.run()

    script.output[0].run_command()
    assert test.call_count == 0
    script.output[1].run_command()
    assert test.call_count == 0
    script.output[3].run_command()
    assert test.call_count == 1
    assert test.call_args == (("arg1 arg2",), )

    script.choose(1)
    assert url.call_count == 1
    assert url.call_args == (("https://www.inklestudios.com/ink/web-tutorial/",), )


def test_wait_command():
    script = ink(f"wait-01")
    script.run()

    assert len(script.options) == 2
    assert script.output[0] != "opt1"
    time.sleep(600 / 1000)
    assert script.output[0] == "opt1"


def test_cancel():
    script = ink(f"wait-01")
    script.run()

    assert len(script.options) == 2
    assert script.output[0] != "opt1"
    script.choose(1)
    assert script.output[0] == "opt2"
    time.sleep(600 / 1000)
    assert script.output[0] != "opt1"


def test_wait_file():
    script = ink(f"wait-02")
    script.run()

    assert len(script.options) == 2
    assert script.output[0] != "opt1"

    with open("/tmp/lils.ink", "w") as fp:
        fp.write("This is a new line\n")
        fp.write("\n")

    assert script.output[0] == "opt1"

    with open("/tmp/lils.ink", "a") as fp:
        fp.write("second line\n")
    time.sleep(3)

    assert script.output[0] == "opt1.1"
