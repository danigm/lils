import os
import pytest


from lils.ink import InkScript
from lils.ink import Text


def ink(name):
    path = os.path.join(os.path.dirname(__file__), "data",
                        f"{name}.ink")
    return InkScript(path)


@pytest.mark.parametrize("fixture,output",
    [
        (1, ["Hello, world!"]),
        (2, ["Hello, world!", "Hello?", "Hello, are you there?"]),
        (3, ['"What do you make of this?" she asked.', '"I couldn\'t possibly comment," I replied.']),
        (4, ["Hello, world!", Text(text="Hello?", tag="tag second line"), "Hello, are you there?"]),
    ]
)
def test_basic(fixture, output):
    script = ink(f"basic-{fixture:02d}")
    script.run()

    assert script.output == output
    assert len(script.options) == 0


def test_option():
    script = ink("option-01")
    script.run()

    assert script.output[0] == "Hello world!"
    assert len(script.options) == 1

    script.choose(0)
    assert script.output[0] == "Hello back!"
    assert script.output[1] == "Nice to hear from you!"
    assert script.next() is None


def test_option_suppress():
    script = ink("option-02")
    script.run()

    assert script.output[0] == "Hello world!"
    assert len(script.options) == 1

    script.choose(0)
    assert script.output[0] == "Nice to hear from you!"
    assert script.next() is None

def test_option_suppress_complex():
    script = ink("option-03")
    script.run()

    assert script.output[0] == "\"What's that?\" my master asked."
    assert len(script.options) == 3

    opt0, opt1, opt2 = script.options
    assert opt0.display_text == "\"I am somewhat tired,\" I repeated."
    assert opt0.option == "\"I am somewhat tired.\""

    assert opt1.display_text == "\"Nothing, Monsieur!\" I replied."
    assert opt1.option == "\"Nothing, Monsieur!\""

    assert opt2.display_text == "\"I said, this journey is appalling and I want no more of it.\""
    assert opt2.option == "\"I said, this journey is appalling.\""

    # Choose option 1
    script.choose(0)
    assert script.output[0] == "\"I am somewhat tired,\" I repeated."
    assert script.output[1] == "\"Really,\" he responded. \"How deleterious.\""
    assert script.next() is None

    # Choose option 2
    script.run()
    assert script.output[0] == "\"What's that?\" my master asked."
    assert len(script.options) == 3

    script.choose(1)
    assert script.output[0] == "\"Nothing, Monsieur!\" I replied."
    assert script.output[1] == "\"Very good, then.\""
    assert script.next() is None

    # test that tags work in options
    assert opt1.tag == "option2"
    assert opt1.content[0].tag == "tag in text"
    assert script.output[1].tag == "tag in text"
