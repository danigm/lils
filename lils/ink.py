import os
import re

from lark import Lark
from lark import Transformer

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


class InkTransformer(Transformer):
    def text(self, s):
        lines = []
        for i in s:
            if i.type == "SH_COMMENT":
                lines[-1].tag = i.value[1:].strip()
            elif i.type == "NEWLINE":
                continue
            else:
                lines.append(Text(text=i.value.strip(), tag=""))
        return lines

    def opttext(self, s):
        display_text = ""
        pre = ""
        suppress = ""
        post = ""
        tag = ""

        for i in s:
            if i.type == "OPTSTRING":
                pre = i.value
            if i.type == "OPTSUPPRESS":
                suppress = i.value
            if i.type == "OPTPOST":
                post = i.value
            if i.type == "SH_COMMENT":
                tag = i.value[1:].strip()

        # Suppress text, option is the pre + suppress text and display_text is pre + post
        option = f"{pre}{suppress}"
        display_text = f"{pre}{post}"
        fulltext = f"{option}{display_text}"

        # TODO: handle tags
        return (fulltext.strip(), option.strip(), display_text.strip(), tag)

    def option(self, s):
        opttext, _newline, *content = s
        (fulltext, option, display_text, tag) = opttext
        text = Text(text=fulltext, tag=tag)
        if content:
            content = content[0]
        return Option(content=content, text=text, display_text=display_text, option=option)

    def options(self, s):
        return s

    def start(self, s):
        return s


class InkScript:
    def __init__(self, path):
        self._ink_path = path
        self._step = 0
        self._length = 0
        self._output = []
        self._options = []
        self._parser = self._init_parser()
        self._transformer = InkTransformer()
        self._script = None

        with open(self._ink_path) as f:
            self._tree = self._parser.parse(f.read())
            self._script = self._transformer.transform(self._tree)
            self._length = len(self._script)

    def _init_parser(self):
        grammar = os.path.join(os.path.dirname(__file__), "ink.lark")
        return Lark.open(grammar, parser='lalr')

    @property
    def output(self):
        return self._output

    @property
    def options(self):
        return self._options

    def choose(self, option=None):
        opt = self.options[option]
        if opt.display_text:
            self._output = [Text(text=opt.display_text, tag=opt.text.tag), *opt.content]
        else:
            self._output = opt.content
        # TODO: Handle finish!

    def run(self):
        self._step = 0
        return self._set_state()

    def next(self):
        self._step += 1
        if self._step >= self._length:
            return None
        return self._set_state()

    def _set_state(self):
        self._options = []
        self._output = self._script[self._step]
        # look for options
        nxt = self._step + 1
        if nxt >= self._length:
            return self.output

        nxt = self._script[nxt]
        if not nxt:
            return self.output

        if nxt and isinstance(nxt[0], Option):
            self._step += 1
            self._options = nxt

        return self.output
