from typing import TextIO
import sys


# The interpreter doesn't emit code, it executes it directly. Here, output
# refers to the stdout used for the ! (output) command. inp refers to stdin
# used for the ? (input) command.
class Interpreter:
    def __init__(
        self, src: str, input: TextIO = sys.stdin, output: TextIO = sys.stdout
    ):
        self.src = src
        self.pos = 0
        self.look = ""
        self.input = input
        self.output = output

        # Table for holding variable values. Unassigned variables default to 0.
        self.table = {}

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

    def ident(self):
        name = self.get_name()
        return self.table.get(name, 0)

    def factor(self) -> int:
        result = 0
        if self.look == "(":
            self.match("(")
            result = self.expression()
            self.match(")")
        elif self.look.isalpha():
            result = self.ident()
        else:
            result = int(self.get_num())
        return result

    def term(self) -> int:
        result = self.factor()
        while self.look in ("*", "/"):
            if self.look == "*":
                self.match("*")
                result *= self.factor()
            elif self.look == "/":
                self.match("/")
                result //= self.factor()
        return result

    def expression(self) -> int:
        # Handling unary operators
        result = 0
        if not self.is_addop(self.look):
            result = self.term()

        while self.is_addop(self.look):
            if self.look == "+":
                self.match("+")
                result += self.term()
            elif self.look == "-":
                self.match("-")
                result -= self.term()
        return result

    def assignment(self):
        name = self.get_name()
        self.match("=")
        self.table[name] = self.expression()

    def interpret(self):
        while self.look != ".":
            match self.look:
                case "?":
                    self.match("?")
                    name = self.get_name()
                    self.table[name] = int(self.input.readline().strip())
                case "!":
                    self.match("!")
                    name = self.get_name()
                    self.output.write(f"{self.table.get(name, 0)}\n")
                case _:
                    self.assignment()
            self.skip_white()
