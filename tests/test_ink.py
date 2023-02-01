import pytest

from lils.ink import Text
from .utils import ink


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

    assert [i for i in script.output if i.text] == output
    assert len(script.options) == 0


def test_option():
    script = ink("option-01")
    script.run()

    assert script.output[0] == "Hello world!"
    assert len(script.options) == 1

    script.choose(0)
    assert script.output[0] == "Hello back!"
    assert script.output[1] == "Nice to hear from you!"


def test_option_suppress():
    script = ink("option-02")
    script.run()

    assert script.output[0] == "Hello world!"
    assert len(script.options) == 1

    script.choose(0)
    assert script.output[0] == "Nice to hear from you!"

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

    # Choose option 2
    script.run()
    assert script.output[0] == "\"What's that?\" my master asked."
    assert len(script.options) == 3

    script.choose(1)
    assert script.output[0] == "\"Nothing, Monsieur!\" I replied."
    assert script.output[1] == "\"Very good, then.\""

    # test that tags work in options
    assert opt1.tag == "option2"
    assert opt1.content[0].content[0].tag == "tag in text"
    assert script.output[1].tag == "tag in text"


def test_knots():
    script = ink("knot-01")
    script.run()

    assert script.output[0] == "The story starts here"
    assert script.output[1] == "We arrived into London at 9.45pm exactly."
    assert script.finished

def test_knots_options():
    script = ink("knot-02")
    script.run()

    assert script.output[0] == "Where do you want to go?"
    assert len(script.options) == 3

    script.choose(0)
    assert script.output[0] == "Paris"
    assert script.output[1] == "We arrived into Paris."
    assert script.output[2] == "Where do you want to go?"

    script.choose(1)
    assert script.output[0] == "We arrived into London."
    assert script.finished

    script.run()
    script.choose(2)
    assert script.output[0] == "Madrid"
    assert script.output[1] == "Noone wants to go there!"
    assert script.finished


def test_divert_and_glue():
    script = ink("divert-01")

    # normal divert
    script.run()
    script.choose(0)
    assert script.output == ["We hurried home to Savile Row", "as fast as we could."]

    # direct divert, no new line
    script.run()
    script.choose(1)
    assert script.output == ["We hurried home to - Savile Row as fast as we could."]

    # glue divert, no new line
    script.run()
    script.choose(2)
    assert script.output == ["We hurried home to Savile Row as fast as we could."]

    # glue divert 2, no new line
    script.run()
    script.choose(3)
    assert script.output == ["We hurried home to Savile Row as fast as we could."]

    # middle glue
    script.run()
    script.choose(4)
    assert script.output == ["We hurried home to Savile Row", "as fast as we could."]


def test_stitches():
    script = ink("stitch-01")

    # Default stitch
    script.run()
    script.choose(0)
    assert script.output == ["This is the default"]

    # Stitch divert
    script.run()
    script.choose(1)
    assert script.output == ["The second stitch"]

    # Stitch divert with default
    script.run()
    script.choose(2)
    assert script.output == ["This is the default"]

    # Local divert
    script.run()
    script.choose(3)
    assert script.output == ["Local divert The second stitch"]


def test_stitches_complex():
    script = ink("stitch-02")

    script.run()
    assert script.output[0] == "Where do you want to go?"
    assert len(script.options) == 3

    script.run()
    script.choose(0)
    assert script.output[0] == "Paris"
    assert script.output[1] == "We arrived into Paris."
    assert script.output[2] == "Where do you want to go?"

    script.run()
    script.choose(1)
    assert script.output[0] == "We arrived into London."
    assert script.finished

    script.run()
    script.choose(2)
    assert script.output[0] == "Madrid"
    assert script.output[1] == "Noone wants to go there!"


def test_empty_lines():
    script = ink("empty-lines")
    script.run()

    empty_lines = [i for i in script.output if not i.text]
    assert len(empty_lines) == 4


def test_include():
    script = ink("include-01")
    script.run()

    assert script.output[0] == "Hello, world!"
    assert len(script.options) == 0

    script = ink("include-02")
    script.run()
    assert script.output[0] == "Hello, world!"
    assert len(script.options) == 3


def test_vars():
    script = ink("vars-01")

    script.run()
    assert script.output[0] == "Hello, world!"
    assert len(script.options) == 3
    assert script.var("x") == 1.0
    assert script.var("y") == 3
    assert script.var("z") == 5
    assert script.var("background") == "Test"
    assert script.var("running") == True

    script.choose(0)
    assert script.output[0] == "op1"
    assert script.var("x") == 2.0
    assert script.var("background") == "Test-op1"

    script.run()
    assert script.output[0] == "Hello, world!"
    script.choose(1)
    assert script.output[0] == "op2"
    assert script.var("x") == 3.0
    assert script.var("y") == -23


def test_op_option():
    script = ink("vars-01")
    script.run()
    assert script.output[0] == "Hello, world!"
    script.choose(2)
    assert script.output[0] == "op3"
    assert script.var("x") == 2.5
