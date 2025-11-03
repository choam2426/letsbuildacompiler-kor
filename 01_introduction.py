from typing import TextIO
import sys


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output

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

    def is_alpha(self, c: str) -> bool:
        return c.isalpha() if c else False

    def is_digit(self, c: str) -> bool:
        return c.isdigit() if c else False

    def get_name(self) -> str:
        if not self.is_alpha(self.look):
            self.expected("Name")
        name = self.look.toupper()
        self.get_char()
        return name

    def get_num(self) -> str:
        if not self.is_digit(self.look):
            self.expected("Integer")
        num = self.look
        self.get_char()
        return num
