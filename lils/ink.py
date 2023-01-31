import os
import re
import webbrowser

from lark import Lark
from lark import Token
from lark import Transformer
from lark.visitors import Discard

from dataclasses import dataclass
from typing import Optional


COMMANDRE = re.compile(r"^(?P<command>[^:]+):\s*(?P<args>([^\s]+\s*)+)$")


@dataclass
class Text:
    text: str
    tag: Optional[str] = None
    glue_start: bool = False
    glue_end: bool = False
    reply: bool = False

    def __str__(self):
        return self.text

    def __eq__(self, other):
        if isinstance(other, Text):
            return self.text == other.text and self.tag == other.tag

        return str(self) == str(other)


@dataclass
class Divert:
    to: str
    stitch: Optional[str] = None
    inline: bool = False

    def __str__(self):
        to = f"-> {self.to}"
        if self.stitch:
            to = f"{to}.{self.stitch}"
        return to


@dataclass
class Texts:
    content: [Text]
    divert: Optional[Divert]

    def __str__(self):
        return "\n".join(str(i) for i in self.content)

    def __iter__(self):
        return iter(self.content)

    def __eq__(self, other):
        if isinstance(other, list):
            return self.content == other
        return self.content == other.content and self.divert == content.divert


@dataclass
class Option:
    text: Text
    option: str
    display_text: str
    content: [Text]

    def __str__(self):
        content = "\n\t".join(str(i) for i in self.content)
        return f"* {self.text}\n\t{content}"

    @property
    def tag(self):
        return self.text.tag


@dataclass
class Stitch:
    name: str
    content: list

    def __str__(self):
        return f"= {self.name}"

    def __getitem__(self, i):
        return self.content[i]

    def __len__(self):
        return len(self.content)


@dataclass
class Knot:
    name: str
    content: list
    stitches: dict[str, Stitch]

    def __str__(self):
        return f"=== {self.name} ==="

    def __getitem__(self, i):
        return self.content[i]

    def __len__(self):
        return len(self.content)

    @classmethod
    def empty(cls, name=""):
        return cls(name=name, content=[], stitches={})


class InkTransformer(Transformer):
    def tag(self, s):
        return s[0]

    def text(self, s):
        lines = []
        texts = Texts(content=lines, divert=None)
        glue_start = False
        newlines = 0

        for i in s:
            match i:
                case(Token(type="GLUESTART")):
                    glue_start = True
                case(Token(type="GLUEEND")):
                    lines[-1].glue_end = True
                case(Token(type="SH_COMMENT")):
                    lines[-1].tag = i.value[1:].strip()
                case(Divert()):
                    i.inline = True
                    texts.divert = i
                case(Token(type="NEWLINE")):
                    # paragraph
                    if newlines == 2:
                        lines.append(Text(text=""))
                        newlines = 0
                    else:
                        newlines += 1
                case(Token(type="STRING")):
                    text = i.value.strip()
                    if lines and lines[-1].glue_end:
                        lines[-1].text += f" {text}"
                        lines[-1].glue_end = False
                        continue

                    lines.append(Text(text=text, tag="", glue_start=glue_start))
                    glue_start = False
        return texts

    def opttext(self, s):
        display_text = ""
        pre = ""
        suppress = ""
        post = ""
        tag = ""
        divert = None

        for i in s:
            if isinstance(i, Divert):
                divert = i
            elif i.type == "OPTSTRING":
                pre = i.value
            elif i.type == "OPTSUPPRESS":
                suppress = i.value
            elif i.type == "OPTPOST":
                post = i.value
            elif i.type == "SH_COMMENT":
                tag = i.value[1:].strip()

        # Suppress text, option is the pre + suppress text and display_text is pre + post
        option = f"{pre}{suppress}"
        display_text = f"{pre}{post}"
        fulltext = f"{option}{display_text}"

        return (fulltext.strip(), option.strip(), display_text.strip(), tag, divert)

    def option(self, s):
        _opt, opttext, *content = self.discard_newlines(s)
        content = self.discard_newlines(content)
        (fulltext, option, display_text, tag, divert) = opttext
        text = Text(text=fulltext, tag=tag)
        # If there's a divert in the option, the followed content is ignored
        if divert:
            content = [divert]
        return Option(content=content, text=text, display_text=display_text, option=option)

    def options(self, s):
        return s

    def start(self, s):
        return s

    def knotheader(self, s):
        knot, name = s
        return name.value.strip()

    def content(self, s):
        return s

    def knot(self, s):
        header, content, *rest = self.discard_newlines(s)
        content = self.discard_newlines(content)
        rest = self.discard_newlines(rest)
        stitches = {}
        if isinstance(content, Stitch):
            default_stitch = content
            content = default_stitch.content
            stitches[default_stitch.name] = default_stitch
        if rest:
            stitches.update({i.name: i for i in rest})
        return Knot(content=content, name=header, stitches=stitches)

    def stitchheader(self, s):
        stitch, name = s
        return name.value.strip()

    def stitch(self, s):
        header, content = self.discard_newlines(s)
        content = self.discard_newlines(content)
        return Stitch(name=header, content=content)

    def divert(self, s):
        ((knot, stitch), ) = s
        return Divert(to=knot, stitch=stitch)

    def divert_stitch(self, s):
        _dot, stich_name = s
        return stich_name.value.strip()

    def divert_name(self, s):
        knot, *stitch = s
        stitch = stitch[0] if stitch else None
        return (knot.value.strip(), stitch)

    def ndivert(self, s):
        return s[0]

    def WS_INLINE(self, token):
        return Discard

    def is_newline(self, l):
        return isinstance(l, Token) and l.type == "NEWLINE"

    def discard_newlines(self, l):
        if not isinstance(l, list):
            return l
        return [i for i in l if not self.is_newline(i)]


class InkScript:
    def __init__(self, path):
        self._ink_path = path
        self._step = 0
        self._output = []
        self._options = []
        self._parser = self._init_parser()
        self._transformer = InkTransformer()
        self._script = None
        self.finished = False
        self.glue = False

        # All script knots will go here, the default one has no name
        self._knots = {
            "": Knot.empty(name=""),
            "END": Knot.empty(name="END"),
        }

        with open(self._ink_path) as f:
            self._tree = self._parser.parse(f.read())
            self._script = self._transformer.transform(self._tree)
            self._parse_knots(self._script)
            self._current_knot = self._knots[""]
            self._current_stitch = None

    def _init_parser(self):
        grammar = os.path.join(os.path.dirname(__file__), "ink.lark")
        return Lark.open(grammar, parser='lalr')

    def _parse_knots(self, script):
        """
        Fill the self._knots property with the content in the tree
        """

        self._current_knot = self._knots[""]
        for i in script:
            if isinstance(i, Knot):
                self._knots[i.name] = i
                self._current_knot = i
                continue

            self._current_knot.content.append(i)


    @property
    def output(self):
        return self._output

    @property
    def options(self):
        return self._options

    def open_url(self, args):
        webbrowser.open_new(args)

    def commands(self, command_line):
        match = COMMANDRE.match(command_line)
        if not match:
            return

        command = match.group("command")
        args = match.group("args")

        if command == "url":
            self.open_url(args)
        else:
            # Unknown command
            return

    def choose(self, option=None):
        # TODO: Remove option for next runs
        # https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md#choices-can-only-be-used-once
        opt = self.options[option]
        content = opt.content
        self.commands(opt.tag)

        self._output = []
        if opt.display_text:
            self._output += [Text(text=opt.display_text, tag=opt.text.tag, reply=True)]

        # [Texts, Divert] | [Texts] | [Divert]
        match content:
            case [Texts(content=content), divert]:
                self._output += content
                self._go_to_divert(divert)
            case [Texts(content=content)]:
                self._output += content
                self._go_next()
            case [divert]:
                self._go_to_divert(divert)

    def run(self):
        self._step = 0
        self._output = []
        self._current_knot = self._knots[""]
        self._current_stitch = None
        self.glue = False
        return self._go_next()

    def _add_output(self, texts):

        # check glue
        if self._output:
            last = self._output[-1]
            head, *texts = texts
            if self.glue or last.glue_end or head.glue_start:
                last.text += f" {head}"
                self.glue = False
            else:
                texts = [head, *texts]

        self._output += texts

    def _go_to_divert(self, divert):
        # TODO: store the prev knot somewhere to be able to go back?
        self._step = 0
        self._current_stitch = None
        if divert.to in self._knots:
            self._current_knot = self._knots[divert.to]
            self._current_stitch = divert.stitch
        else:
            # maybe a local divert to a stitch
            self._current_stitch = divert.to
        return self._go_next()

    def _go_next(self):
        """
        Recursive function that loads the next state until it requires user
        input
        """

        self._options = []

        if self._current_stitch:
            stitch = self._current_knot.stitches[self._current_stitch]
            # No more steps in this stitch, so it's completed
            if self._step >= len(stitch):
                self.finished = True
                return self.output
            step = stitch[self._step]
        else:
            # No more steps in this knot, so it's completed
            if self._step >= len(self._current_knot):
                self.finished = True
                return self.output
            step = self._current_knot[self._step]

        match step:
            case Divert():
                if step.inline:
                    self.glue = True
                return self._go_to_divert(step)
            case [Option(), *others]:
                self._options = step
                return self.output
            case Texts():
                self._add_output(step.content)
                if step.divert:
                    if step.divert.inline:
                        self.glue = True
                    return self._go_to_divert(step.divert)
            case Text():
                self._add_output([step])

        self._step += 1
        return self._go_next()
