from typing import TextIO
import sys


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output

        # 'Init' from the tutorial: prime the parser by calling get_char.
        self.get_char()

    def get_char(self):
        if self.pos < len(self.src):
            self.look = self.src[self.pos]
            self.pos += 1
        else:
            self.look = ""  # End of input

    def abort(self, msg: str):
        raise Exception(f"Error: {msg}")

    def expected(self, s: str):
        self.abort(f"{s} expected")

    def match(self, x: str):
        if self.look == x:
            self.get_char()
        else:
            self.expected(f"'{x}'")

    def get_name(self) -> str:
        if not self.look.isalpha():
            self.expected("Name")
        name = self.look.upper()
        self.get_char()
        return name

    def emit(self, s: str):
        self.output.write("    " + s)

    def emit_ln(self, s: str):
        self.emit(s + "\n")

    # TODO: talk abuot these
    def prolog(self, name: str):
        self.emit_ln(f"; Module {name}")
        self.emit_ln("(module")

    def epilog(self):
        self.emit_ln(")")

    def prog(self):
        self.match("p")
        name = self.get_name()
        self.prolog(name)
        self.do_block(name)
        self.match(".")
        self.epilog()

    def do_block(self, name: str):
        self.declarations()
        self.statements()

    def declarations(self):
        while self.look in {"l", "c", "t", "v", "p", "f"}:
            match self.look:
                case "l":
                    self.labels()
                case "c":
                    self.constants()
                case "t":
                    self.types()
                case "v":
                    self.variables()
                case "p":
                    self.do_procedure()
                case "f":
                    self.do_function()

    def statements(self):
        self.match('b')
        while self.look != "e":
            self.get_char()
        self.match('e')

    def labels(self):
        self.match("l")

    def constants(self):
        self.match("c")

    def types(self):
        self.match("t")

    def variables(self):
        self.match("v")

    def do_procedure(self):
        self.match("p")

    def do_function(self):
        self.match("f")

