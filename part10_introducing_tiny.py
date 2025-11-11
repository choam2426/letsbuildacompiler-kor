from typing import TextIO
import sys


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output
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

    def skip_white(self):
        while self.look.isspace():
            self.get_char()

    def emit(self, s: str):
        self.output.write("    " + s)

    def emit_ln(self, s: str):
        self.emit(s + "\n")

    def prolog(self, name: str):
        self.emit_ln(f"; Module {name}")
        self.emit_ln("(module")

    def epilog(self):
        self.emit_ln(")")

    def alloc_global(self, name: str):
        # TODO: handle indentation levels properly?
        value = "0"
        if self.look == '=':
            self.match('=')
            if self.look == '-':
                self.match('-')
                value = '-' + self.get_num()
            else:
                value = self.get_num()
        self.emit_ln(f"(global ${name} (mut i32) (i32.const {value}))")

    def prog(self):
        self.match("p")
        self.prolog('main')
        # TODO: need header, or not??
        self.top_decls()
        self.main()
        self.match(".")
        self.epilog()

    def main(self):
        self.match('b')
        self.match('e')
    
    # <top-level decls> ::= ( <data declaration> )*
    # <data declaration> ::= 'v' <var-list>
    def top_decls(self):
        while self.look != 'b':
            match self.look:
                case 'v':
                    self.decl()
                case _:
                    self.abort(f"unrecognized keyword {self.look}")

    # <var-list> ::= <var> (, <var> )*
    # <var> ::= <ident> [ = <num> ]
    def decl(self):
        self.match('v')
        self.alloc_global(self.get_name())
        while self.look == ',':
            self.match(',')
            self.alloc_global(self.get_name())
