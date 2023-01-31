import os
import pytest

from lils.ink import InkScript


def ink(name):
    path = os.path.join(os.path.dirname(__file__), "data",
                        f"{name}.ink")
    return InkScript(path)
