import os

from lark import Lark
from lark import Token
from lark import Transformer
from lark.visitors import Discard

from dataclasses import dataclass
from typing import Optional, Any

from .commands import run_command
from .listeners import run_listeners

from operator import add, sub, mul, truediv as div, neg
from operator import eq, lt, gt, le, ge, not_, and_, or_, truth


class Evaluable:
    pass


class Tagged:
    def run_command(self):
        run_command(self.tag)

    def run_listeners(self, script, index, question):
        run_listeners(self.tag, script, index, question)


@dataclass
class Text(Tagged):
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
class Condition(Evaluable):
    operator: Any
    item1: Any
    item2: Any

    def evaluate(self, context):
        i1 = self.item1
        if isinstance(i1, Evaluable):
            i1 = i1.evaluate(context)
        i2 = self.item2
        if isinstance(i2, Evaluable):
            i2 = i2.evaluate(context)
        ops = filter(lambda i: i is not None, (i1, i2))
        return self.operator(*ops)


@dataclass
class Option(Tagged):
    text: Text
    option: str
    display_text: str
    content: [Text]
    logic: Optional[Condition] = None

    def __str__(self):
        content = "\n\t".join(str(i) for i in self.content)
        return f"* {self.text}\n\t{content}"

    @property
    def tag(self):
        return self.text.tag

    def is_available(self, context):
        if not self.logic:
            return True
        return self.logic.evaluate(context)


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


@dataclass
class Assignment(Evaluable):
    var: str
    value: Optional[Any] = None
    declaration: bool = False

    def evaluate(self, context):
        v = self.value
        if isinstance(v, Evaluable):
            v = v.evaluate(context)
        return v


@dataclass
class Var(Evaluable):
    name: str

    def evaluate(self, context):
        return context.get(self.name)


@dataclass
class Op(Condition):
    pass


class InkTransformer(Transformer):
    const_none = lambda self, _: None
    const_true = lambda self, _: True
    const_false = lambda self, _: False

    def var(self, s):
        (s, ) = s
        return Var(s.value)

    def add(self, s):
        item1, _op, item2 = s
        return Op(add, item1, item2)

    def sub(self, s):
        item1, _op, item2 = s
        return Op(sub, item1, item2)

    def mul(self, s):
        item1, _op, item2 = s
        return Op(mul, item1, item2)

    def div(self, s):
        item1, _op, item2 = s
        return Op(div, item1, item2)

    def neg(self, s):
        _op, item1 = s
        return Op(neg, item1, None)

    def variable(self, s):
        assignment = s[1]
        assignment.declaration = True
        return assignment

    def operation(self, s):
        assignment = s[1]
        assignment.declaration = False
        return assignment

    def assignment(self, s):
        name, value = s
        return Assignment(var=name.value.strip(), value=value)

    def str(self, s):
        (s, ) = s
        return s.value[1:-1]

    def number(self, s):
        (s, ) = s
        return float(s.value)

    def include(self, s):
        _include, filename, *rest = self.discard_newlines(s)
        path = filename.value.strip()
        script = InkScript(path)
        return script

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
                    else:
                        newlines += 1
                        continue
                case(Token(type="STRING")):
                    text = i.value.strip()
                    if lines and lines[-1].glue_end:
                        lines[-1].text += f" {text}"
                        lines[-1].glue_end = False
                        continue

                    lines.append(Text(text=text, tag="", glue_start=glue_start))
                    glue_start = False

            newlines = 0
        return texts

    def eq(self, s):
        op1, _eq, op2 = s
        return Condition(operator=eq, item1=op1, item2=op2)

    def lt(self, s):
        op1, _op, op2 = s
        return Condition(operator=lt, item1=op1, item2=op2)

    def gt(self, s):
        op1, _op, op2 = s
        return Condition(operator=gt, item1=op1, item2=op2)

    def gte(self, s):
        op1, _op, op2 = s
        return Condition(operator=ge, item1=op1, item2=op2)

    def lte(self, s):
        op1, _op, op2 = s
        return Condition(operator=le, item1=op1, item2=op2)

    def and_(self, s):
        op1, _op, op2 = s
        return Condition(operator=and_, item1=op1, item2=op2)

    def or_(self, s):
        op1, _op, op2 = s
        return Condition(operator=or_, item1=op1, item2=op2)

    def not_(self, s):
        _op, op1 = s
        return Condition(operator=not_, item1=op1, item2=None)

    def logic(self, s):
        _start, operation, _end = s
        if not isinstance(operation, Condition):
            return Condition(operator=truth, item1=operation, item2=None)
        return operation

    def opttext(self, s):
        display_text = ""
        pre = ""
        suppress = ""
        post = ""
        tag = ""
        divert = None
        logic = None

        for i in s:
            if isinstance(i, Divert):
                divert = i
            elif isinstance(i, Condition):
                logic = i
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

        return (fulltext.strip(), option.strip(), display_text.strip(), tag, divert, logic)

    def option(self, s):
        _opt, opttext, *content = self.discard_newlines(s)
        content = self.discard_newlines(content)
        (fulltext, option, display_text, tag, divert, logic) = opttext
        text = Text(text=fulltext, tag=tag)
        # If there's a divert in the option, the followed content is ignored
        if divert:
            content = [divert]
        return Option(content=content, text=text, display_text=display_text, option=option, logic=logic)

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

    def NDIVERT(self, token):
        return Discard

    def WS_INLINE(self, token):
        return Discard

    def is_newline(self, l):
        return isinstance(l, Token) and l.type == "NEWLINE"

    def discard_newlines(self, l):
        if not isinstance(l, list):
            return l
        return [i for i in l if not self.is_newline(i)]


class InkScript:
    def __init__(self, path, on_change=None):
        self._ink_path = path
        self._step = 0
        self._output = []
        self._options = []
        self._allopts = []
        self._parser = self._init_parser()
        self._transformer = InkTransformer()
        self._script = None
        self._vars = {}
        self._question = 0
        self._on_change = on_change
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
            self._script = self._parse_include(self._script)
            self._parse_knots(self._script)
            self._init_vars()
            self._current_knot = self._knots[""]
            self._current_stitch = None

    def _parse_include(self, script):
        new_script = []
        for i in script:
            if isinstance(i, InkScript):
                new_script += i._script
            else:
                new_script.append(i)
        return new_script

    def _init_parser(self):
        grammar = os.path.join(os.path.dirname(__file__), "ink.lark")
        return Lark.open(grammar, parser='lalr')

    def _parse_knots(self, script):
        """
        Fill the self._knots property with the content in the tree
        """

        self._default_knot = self._knots[""]
        for i in script:
            match i:
                case Knot():
                    self._knots[i.name] = i
                    continue
            self._default_knot.content.append(i)

    def _init_vars(self):
        self._vars = {}
        for i in self._script:
            match i:
                case Assignment(var=n, value=v, declaration=True):
                    self._vars[n] = i.evaluate(self._vars)
        for k, v in self._knots.items():
            self._vars[k] = 0
            for s in v.stitches:
                self._vars[f"{k}.{s}"] = 0

    @property
    def output(self):
        return self._output

    @property
    def options(self):
        return self._options

    @property
    def vars(self):
        return self._vars

    def var(self, name, default=None):
        return self._vars.get(name, default)

    def set(self, name, value):
        self._vars[name] = value
        # Update options
        self._set_options(self._allopts)
        self._changed()

    def resolve(self, index, question):
        # Only choose the option if the question didn't change
        if self._question == question:
            self.choose(index)

    def _changed(self):
        if self._on_change:
            self._on_change(self.output)

    def choose(self, option=None):
        # TODO: Remove option for next runs
        # https://github.com/inkle/ink/blob/master/Documentation/WritingWithInk.md#choices-can-only-be-used-once
        opt = self.options[option]
        content = opt.content
        opt.run_command()

        self._output = []
        if opt.display_text:
            self._output += [Text(text=opt.display_text, tag=opt.text.tag, reply=True)]

        self._question += 1
        divert = None

        for i in content:
            match i:
                case Texts(content=content):
                    self._output += content
                case Assignment():
                    self._vars[i.var] = i.evaluate(self._vars)
                case Divert():
                    divert = i
                    break

        if divert:
            self._go_to_divert(divert)
        else:
            self._go_next()

        self._changed()

    def run(self):
        self._step = 0
        self._output = []
        self._current_knot = self._knots[""]
        self._current_stitch = None
        self.glue = False
        self._init_vars()
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
            self._vars[divert.to] += 1
            if divert.stitch:
                self._vars[f"{divert.to}.{divert.stitch}"] += 1
        else:
            # maybe a local divert to a stitch
            self._current_stitch = divert.to
            k = self._current_knot.name
            self._vars[f"{k}.{divert.to}"] += 1

        return self._go_next()

    def _set_options(self, options):
        self._allopts = options
        self._options = [opt for opt in options if opt.is_available(self._vars)]
        for i, option in enumerate(self._options):
            option.run_listeners(self, i, self._question)

    def _go_next(self):
        """
        Recursive function that loads the next state until it requires user
        input
        """

        self._allopts = []
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
                self._set_options(step)
                return self.output
            case Texts():
                self._add_output(step.content)
                if step.divert:
                    if step.divert.inline:
                        self.glue = True
                    return self._go_to_divert(step.divert)
            case Text():
                self._add_output([step])
            case Assignment(declaration=False):
                self._vars[step.var] = step.evaluate(self._vars)

        self._step += 1
        return self._go_next()
