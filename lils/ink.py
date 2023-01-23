import os
import re

from lark import Lark
from lark import Transformer
from lark.visitors import Discard

from dataclasses import dataclass


@dataclass
class Text:
    text: str
    tag: str

    def __str__(self):
        return self.text

    def __eq__(self, other):
        if isinstance(other, Text):
            return self.text == other.text and self.tag == other.tag

        return str(self) == str(other)


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
class Knot:
    name: str
    content: list

    def __str__(self):
        return f"=== {self.name} ==="

    def __getitem__(self, i):
        return self.content[i]

    def __len__(self):
        return len(self.content)


@dataclass
class Divert:
    to: str

    def __str__(self):
        return f"-> {self.to}"


class InkTransformer(Transformer):
    def text(self, s):
        lines = []
        for i in s:
            if i.type == "SH_COMMENT":
                lines[-1].tag = i.value[1:].strip()
            else:
                lines.append(Text(text=i.value.strip(), tag=""))
        return lines

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
        opttext, *content = s
        (fulltext, option, display_text, tag, divert) = opttext
        text = Text(text=fulltext, tag=tag)
        # content can be:
        # * text
        # * divert
        # * text, divert
        match content:
            case [[Text()]]:
                content = content[0]
            case [Divert()]:
                content = [content[0]]
            case [[Text()], Divert()]:
                content = content[0] + [content[1]]

        if divert:
            content = [divert]
        return Option(content=content, text=text, display_text=display_text, option=option)

    def options(self, s):
        return s

    def start(self, s):
        return s

    def knotheader(self, s):
        (s, ) = s
        return s.value.strip()

    def knot(self, s):
        header, content = s
        return Knot(content=content, name=header)

    def divert(self, s):
        (knot, ) = s
        return Divert(to=knot.value.strip())

    def ndivert(self, s):
        return s[0]

    def NEWLINE(self, token):
        return Discard

    def WS_INLINE(self, token):
        return Discard


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

        # All script knots will go here, the default one has no name
        self._knots = {
            "": Knot(name="", content=[]),
            "END": Knot(name="END", content=[]),
        }

        with open(self._ink_path) as f:
            self._tree = self._parser.parse(f.read())
            self._script = self._transformer.transform(self._tree)
            self._parse_knots(self._script)
            self._current_knot = self._knots[""]

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

    def choose(self, option=None):
        # TODO: Remove option for next runs
        # https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md#choices-can-only-be-used-once
        opt = self.options[option]
        text = [i for i in opt.content if not isinstance(i, Divert)]
        if opt.display_text:
            self._output = [Text(text=opt.display_text, tag=opt.text.tag), *text]
        else:
            self._output = text

        if opt.content and isinstance(opt.content[-1], Divert):
            self._go_to_divert(opt.content[-1])
        else:
            self._go_next()

    def run(self):
        self._step = 0
        self._output = []
        self._current_knot = self._knots[""]
        return self._go_next()

    def _go_to_divert(self, divert):
        # TODO: store the prev knot somewhere to be able to go back?
        self._step = 0
        self._current_knot = self._knots[divert.to]
        return self._go_next()

    def _go_next(self):
        """
        Recursive function that loads the next state until it requires user
        input
        """

        self._options = []

        # No more steps in this knot, so it's completed
        if self._step >= len(self._current_knot):
            self.finished = True
            return self.output

        step = self._current_knot[self._step]
        match step:
            case Divert():
                return self._go_to_divert(step)
            case [Option(), *others]:
                self._options = step
                return self.output
            case [Text(), *others]:
                self._output += step
            case Text():
                self._output += [step]

        self._step += 1
        return self._go_next()
