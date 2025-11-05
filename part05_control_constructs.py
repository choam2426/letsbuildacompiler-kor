from typing import TextIO
import sys


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output
        self.lcount = 0 # Label counter

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
        # Note: for part 5, we're back to only supporting single-letter names.
        if not self.look.isalpha():
            self.expected("Name")
        name = self.look.upper()
        self.get_char()
        self.skip_white()
        return name

    def get_num(self) -> str:
        # Note: for part 5, we're back to only supporting single-digit numbers.
        if not self.look.isdigit():
            self.expected("Integer")
        num = self.look
        self.get_char()
        self.skip_white()
        return num

    def emit(self, s: str):
        self.output.write("    " + s)

    def emit_ln(self, s: str):
        self.emit(s + "\n")
    
    def condition(self):
        self.emit_ln('<condition>')
    
    def expression(self):
        self.emit_ln('<expression>')

    def other(self):
        self.emit_ln(self.get_name())
    
    def block(self):
        while self.look not in ('e', 'l', 'u', ''):
            match self.look:
                case 'i':
                    self.do_if()
                case _:
                    self.other()

    def do_if(self):
        self.match('i')
        self.condition()
        self.emit_ln('if')
        self.block()
        if self.look == 'l':
            self.match('l')
            self.emit_ln('else')
            self.block()
        self.match('e')
        self.emit_ln('end')

