import os

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


class InkTransformer(Transformer):
    def text(self, s):
        lines = []
        for i in s:
            if i.type == 'SH_COMMENT':
                lines[-1].tag = i.value[1:].strip()
            else:
                lines.append(Text(text=i.value.strip(), tag=""))
        return lines


class InkScript:
    def __init__(self, path):
        self._ink_path = path
        self._step = 0
        self._output = ""
        self._parser = self._init_parser()
        self._transformer = InkTransformer()
        self._script = None

        with open(self._ink_path) as f:
            self._tree = self._parser.parse(f.read())
            self._script = self._transformer.transform(self._tree)

    def _init_parser(self):
        grammar = os.path.join(os.path.dirname(__file__), "ink.lark")
        return Lark.open(grammar)

    @property
    def output(self):
        return self._output

    def input(self, input=None):
        pass

    def run(self):
        self._output = self._script
