from typing import TextIO
import sys


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output
        self.indent = 0
        self.loopcount = 0

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
            self.skip_white()
        else:
            self.expected(f"'{x}'")

    def generate_loop_labels(self) -> dict[str, str]:
        self.loopcount += 1
        return {
            "loop": f"$loop{self.loopcount}",
            "break": f"$breakloop{self.loopcount}",
        }

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

    def emit_ln(self, s: str):
        self.output.write(" " * self.indent + s + "\n")

    def prolog(self):
        self.emit_ln("(module")

    def epilog(self):
        self.emit_ln(")")

    def alloc_global(self, name: str):
        if name in self.symtable:
            self.abort(f"Duplicate global variable {name}")
        self.symtable.add(name)
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
        self.indent += 2
        self.top_decls()
        self.main()
        self.match(".")
        self.indent -= 2
        self.epilog()

    # <main> ::= 'b' <block> 'e'
    def main(self):
        self.match("b")
        self.emit_ln('(func $main (export "main") (result i32)')
        self.indent += 2
        self.block()
        self.emit_ln("global.get $X")
        self.indent -= 2
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
                    self.abort(f"unrecognized keyword '{self.look}'")

    # <var-list> ::= <var> (, <var> )*
    # <var> ::= <ident> [ = <num> ]
    def decl(self):
        self.match("v")
        self.alloc_global(self.get_name())
        while self.look == ",":
            self.match(",")
            self.alloc_global(self.get_name())

    # <if> ::= I <bool-expression> <block> [ L <block>] E
    # <while> ::= W <bool-expression> <block> E
    # <block> ::= ( <statement> )*
    # <statement> ::= <if> | <while> | <assignment>
    def block(self, breakloop_label: str = ""):
        # breakloop_label is used for emitting break statements inside loops.
        while self.look not in ("e", "l", ""):
            match self.look:
                case "i":
                    self.do_if(breakloop_label)
                case "w":
                    self.do_while()
                case "b":
                    self.do_break(breakloop_label)
                case _:
                    self.assignment()

    # <assignment> ::= <ident> '=' <bool-expression>
    # <expression> ::= <first term> ( <addop> <term> )*
    # <term> ::= <factor> ( <mulop> <factor> )*
    # <first term> ::= <first factor> ( <mulop> <factor> )*
    # <first factor> ::= [ <addop> ] <factor>
    # <factor> ::= <var> | <number> | ( <bool-expression> )

    # <bool-expression> ::= <bool-term> ( <orop> <bool-term> )*
    # <bool-term> ::= <not-factor> ( <andop> <not-factor> )*
    # <not-factor> ::= [ '!' ] <relation>
    # <relation> ::= <expression> [ <relop> <expression> ]
    def assignment(self):
        name = self.get_name()
        if name not in self.symtable:
            self.undefined(name)
        self.match("=")
        self.bool_expression()
        self.emit_ln(f"global.set ${name}")

    def factor(self):
        if self.look == "(":
            self.match("(")
            self.bool_expression()
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

    def equals(self):
        self.match("=")
        self.expression()
        self.emit_ln("i32.eq")

    def not_equals(self):
        self.match("#")
        self.expression()
        self.emit_ln("i32.ne")

    def less_than(self):
        self.match("<")
        self.expression()
        self.emit_ln("i32.lt_s")

    def greater_than(self):
        self.match(">")
        self.expression()
        self.emit_ln("i32.gt_s")

    def relation(self):
        self.expression()
        match self.look:
            case "=":
                self.equals()
            case "#":
                self.not_equals()
            case "<":
                self.less_than()
            case ">":
                self.greater_than()
            case _:
                pass

    def not_factor(self):
        if self.look == "!":
            self.match("!")
            self.relation()
            self.emit_ln("i32.eqz")
        else:
            self.relation()

    def bool_term(self):
        self.not_factor()
        while self.look == "&":
            self.match("&")
            self.not_factor()
            self.emit_ln("i32.and")

    def bool_or(self):
        self.match("|")
        self.bool_term()
        self.emit_ln("i32.or")

    def bool_xor(self):
        self.match("~")
        self.bool_term()
        self.emit_ln("i32.xor")

    def bool_expression(self):
        self.bool_term()
        while self.look in ("|", "~"):
            if self.look == "|":
                self.bool_or()
            elif self.look == "~":
                self.bool_xor()

    def do_if(self, breakloop_label: str = ""):
        self.match("i")
        self.bool_expression()
        self.emit_ln("if")
        self.indent += 2
        self.block(breakloop_label)
        self.indent -= 2
        if self.look == "l":
            self.match("l")
            self.emit_ln("else")
            self.indent += 2
            self.block(breakloop_label)
            self.indent -= 2
        self.match("e")
        self.emit_ln("end")

    def do_break(self, breakloop_label: str):
        if breakloop_label == "":
            self.abort("No loop to break from")
        self.match("b")
        self.emit_ln(f"br {breakloop_label}")

    def do_while(self):
        self.match("w")
        labels = self.generate_loop_labels()
        self.emit_ln(f"loop {labels['loop']}")
        self.indent += 2
        self.emit_ln(f"block {labels['break']}")
        self.indent += 2
        self.bool_expression()
        # For a while loop the break condition is the inverse of the loop
        # condition.
        self.emit_ln("i32.eqz")
        self.emit_ln(f"br_if {labels['break']}")
        self.block(labels["break"])
        self.emit_ln(f"br {labels['loop']}")
        self.match("e")
        self.indent -= 2
        self.emit_ln("end")  # end block
        self.indent -= 2
        self.emit_ln("end")  # end loop
