from typing import TextIO
import sys


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output

        # Used only to avoid duplicate declarations for now.
        self.symtable = set()

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

    def prolog(self):
        self.emit_ln("(module")

    def epilog(self):
        self.emit_ln(")")

    def alloc_global(self, name: str):
        if name in self.symtable:
            self.abort(f"Duplicate global variable {name}")
        self.symtable.add(name)
        # TODO: handle indentation levels properly?
        value = "0"
        if self.look == "=":
            self.match("=")
            if self.look == "-":
                self.match("-")
                value = "-" + self.get_num()
            else:
                value = self.get_num()
        self.emit_ln(f"(global ${name} (mut i32) (i32.const {value}))")

    def undefined(self, name: str):
        self.abort(f"Undefined identifier {name}")

    def prog(self):
        self.match("p")
        self.prolog()
        self.top_decls()
        self.main()
        self.match(".")
        self.epilog()

    # <main> ::= 'b' <block> 'e'
    def main(self):
        self.match("b")
        self.emit_ln('(func $main (export "main") (result i32)')
        self.block()
        self.emit_ln("global.get $X")
        self.emit_ln(")")
        self.match("e")

    # <top-level decls> ::= ( <data declaration> )*
    # <data declaration> ::= 'v' <var-list>
    def top_decls(self):
        while self.look != "b":
            match self.look:
                case "v":
                    self.decl()
                case _:
                    self.abort(f"unrecognized keyword {self.look}")

    # <var-list> ::= <var> (, <var> )*
    # <var> ::= <ident> [ = <num> ]
    def decl(self):
        self.match("v")
        self.alloc_global(self.get_name())
        while self.look == ",":
            self.match(",")
            self.alloc_global(self.get_name())

    # <block> ::= ( <assignment> )*
    def block(self):
        while self.look != "e":
            self.assignment()

    # <assignment> ::= <ident> '=' <expression>
    # <expression> ::= <first term> ( <addop> <term> )*
    # <term> ::= <factor> ( <mulop> <factor> )*
    # <first term> ::= <first factor> ( <mulop> <factor> )*
    # <first factor> ::= [ <addop> ] <factor>
    # <factor> ::= <var> | <number> | ( <expression> )
    def assignment(self):
        name = self.get_name()
        if name not in self.symtable:
            self.undefined(name)
        self.match("=")
        self.expression()
        self.emit_ln(f"global.set ${name}")

    def factor(self):
        if self.look == "(":
            self.match("(")
            self.expression()
            self.match(")")
        elif self.look.isalpha():
            name = self.get_name()
            if name not in self.symtable:
                self.undefined(name)
            self.emit_ln(f"global.get ${name}")
        else:
            self.emit_ln(f"i32.const {self.get_num()}")

    def neg_factor(self):
        self.match("-")
        if self.look.isdigit():
            self.emit_ln(f"i32.const -{self.get_num()}")
        else:
            self.factor()
            self.emit_ln("i32.const -1")
            self.emit_ln("i32.mul")

    def first_factor(self):
        match self.look:
            case "+":
                self.match("+")
                self.factor()
            case "-":
                self.neg_factor()
            case _:
                self.factor()

    def multiply(self):
        self.match("*")
        self.factor()
        self.emit_ln("i32.mul")

    def divide(self):
        self.match("/")
        self.factor()
        self.emit_ln("i32.div_s")

    def term1(self):
        # Common code for term and first_term
        while self.look in ("*", "/"):
            if self.look == "*":
                self.multiply()
            elif self.look == "/":
                self.divide()

    def term(self):
        self.factor()
        self.term1()

    def first_term(self):
        self.first_factor()
        self.term1()

    def add(self):
        self.match("+")
        self.term()
        self.emit_ln("i32.add")

    def subtract(self):
        self.match("-")
        self.term()
        self.emit_ln("i32.sub")

    def expression(self):
        self.first_term()
        while self.look in ("+", "-"):
            if self.look == "+":
                self.add()
            elif self.look == "-":
                self.subtract()
