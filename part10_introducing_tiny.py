from typing import TextIO
import sys


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output
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

    def prolog(self, name: str):
        self.emit_ln(f"; Module {name}")
        self.emit_ln("(module")

    def epilog(self):
        self.emit_ln(")")

    def alloc_global(self, name: str):
        # TODO: handle indentation levels properly?
        self.emit_ln(f"(global ${name} (mut i32) (i32.const 0))")

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

    def decl(self):
        self.match('v')
        self.alloc_global(self.look)
        self.get_char()
    
            