import os
import pytest


from lils.ink import InkScript
from lils.ink import Text


@pytest.mark.parametrize("fixture,output",
    [
        (1, ["Hello, world!"]),
        (2, ["Hello, world!", "Hello?", "Hello, are you there?"]),
        (3, ['"What do you make of this?" she asked.', '"I couldn\'t possibly comment," I replied.']),
        (4, ["Hello, world!", Text(text="Hello?", tag="tag second line"), "Hello, are you there?"]),
    ]
)
def test_basic(fixture, output):
    path = os.path.join(os.path.dirname(__file__), "data",
                        f"basic-{fixture:02d}.ink")
    script = InkScript(path)
    script.run()

    assert script.output == output
