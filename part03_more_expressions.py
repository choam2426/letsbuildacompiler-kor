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
        self.skip_white()

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

    def skip_white(self):
        while self.look.isspace():
            self.get_char()

    def match(self, x: str):
        if self.look == x:
            self.get_char()
            self.skip_white()
        else:
            self.expected(f"'{x}'")

    def get_name(self) -> str:
        if not self.look.isalpha():
            self.expected("Name")
        name = ""
        while self.look.isalnum():
            name += self.look.upper()
            self.get_char()
        self.skip_white()
        return name

    def get_num(self) -> str:
        if not self.look.isdigit():
            self.expected("Integer")
        num = ""
        while self.look.isdigit():
            num += self.look
            self.get_char()
        self.skip_white()
        return num

    def is_addop(self, c: str) -> bool:
        return c in ("+", "-")

    def emit(self, s: str):
        self.output.write("    " + s)

    def emit_ln(self, s: str):
        self.emit(s + "\n")

    def ident(self):
        name = self.get_name()
        if self.look == "(":
            self.match("(")
            self.match(")")
            self.emit_ln(f"call ${name}")
        else:
            self.emit_ln(f"local.get ${name}")

    def factor(self):
        if self.look == "(":
            self.match("(")
            self.expression()
            self.match(")")
        elif self.look.isalpha():
            self.ident()
        else:
            s = self.get_num()
            self.emit_ln(f"i32.const {s}")

    def multiply(self):
        self.match("*")
        self.factor()
        self.emit_ln("i32.mul")

    def divide(self):
        self.match("/")
        self.factor()
        self.emit_ln("i32.div_s")

    def term(self):
        self.factor()
        while self.look in ("*", "/"):
            if self.look == "*":
                self.multiply()
            elif self.look == "/":
                self.divide()

    def add(self):
        self.match("+")
        self.term()
        self.emit_ln("i32.add")

    def subtract(self):
        self.match("-")
        self.term()
        self.emit_ln("i32.sub")

    def expression(self):
        # For handling unary + and - operators, emit a zero first and then
        # proceed as usual.
        if self.is_addop(self.look):
            self.emit_ln("i32.const 0")
        else:
            self.term()
        while self.is_addop(self.look):
            if self.look == "+":
                self.add()
            elif self.look == "-":
                self.subtract()

    def assignment(self):
        name = self.get_name()
        self.match("=")
        self.emit_ln(f"(local ${name} i32)")
        self.expression()
        self.emit_ln(f"local.set ${name}")
