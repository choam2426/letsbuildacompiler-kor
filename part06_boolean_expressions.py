from typing import TextIO
import sys

# BNF from the original tutorial
#
# <expression>      ::= <term> [<addop> <term>]*
# <term>            ::= <signed factor> [<mulop> <factor>]*
# <signed factor>   ::= [<addop>] <factor>
# <factor>          ::= <integer> | <variable> | (<b-expression>)
#
# <b-expression>    ::= <b-term> [<orop> <b-term>]*
# <b-term>          ::= <not-factor> [AND <not-factor>]*
# <not-factor>      ::= [NOT] <b-factor>
# <b-factor>        ::= <b-literal>
#                     | <b-variable>
#                     | <relation>
#
# <relation>        ::= <expression> [<relop> <expression>]


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.look = ""
        self.output = output
        self.loopcount = 0

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
        # Note: for part 6, we're back to only supporting single-letter names.
        if not self.look.isalpha():
            self.expected("Name")
        name = self.look.upper()
        self.get_char()
        self.skip_white()
        return name

    def get_num(self) -> str:
        # Note: for part 6, we're back to only supporting single-digit numbers.
        if not self.look.isdigit():
            self.expected("Integer")
        num = self.look
        self.get_char()
        self.skip_white()
        return num

    def get_boolean(self) -> bool:
        if not self.is_boolean(self.look):
            self.expected("Boolean")
        value = self.look.upper() == "T"
        self.get_char()
        self.skip_white()
        return value

    def is_addop(self, c: str) -> bool:
        return c in ("+", "-")

    def is_boolean(self, c: str) -> bool:
        return c.upper() in ("T", "F")

    def is_relop(self, c: str) -> bool:
        return c in ("=", "#", "<", ">")

    def emit(self, s: str):
        self.output.write("    " + s)

    def emit_ln(self, s: str):
        self.emit(s + "\n")

    def generate_loop_labels(self) -> dict[str, str]:
        self.loopcount += 1
        return {
            "loop": f"$loop{self.loopcount}",
            "break": f"$breakloop{self.loopcount}",
            "var": f"$loopvar{self.loopcount}",
            "limit": f"$looplimit{self.loopcount}",
        }

    def ident(self):
        name = self.get_name()
        if self.look == "(":
            self.match("(")
            self.match(")")
            self.emit_ln(f"call ${name}")
        else:
            self.emit_ln(f"local.get ${name}")

    def signed_factor(self):
        if self.look == "+":
            self.match("+")
            self.factor()
        elif self.look == "-":
            self.match("-")
            if self.look.isdigit():
                s = self.get_num()
                self.emit_ln(f"i32.const -{s}")
            else:
                self.factor()
                self.emit_ln("i32.const -1")
                self.emit_ln("i32.mul")
        else:
            self.factor()

    def factor(self):
        if self.look == "(":
            self.match("(")
            self.bool_expression()
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
        self.signed_factor()
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
        self.term()
        while self.is_addop(self.look):
            if self.look == "+":
                self.add()
            elif self.look == "-":
                self.subtract()

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

    def bool_term(self):
        self.not_factor()
        while self.look == "&":
            self.match("&")
            self.not_factor()
            self.emit_ln("i32.and")

    def not_factor(self):
        if self.look == "!":
            self.match("!")
            self.bool_factor()
            self.emit_ln("i32.eqz")
        else:
            self.bool_factor()

    def bool_factor(self):
        if self.is_boolean(self.look):
            value = self.get_boolean()
            val_int = 1 if value else 0
            self.emit_ln(f"i32.const {val_int}")
        else:
            self.relation()

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

    def assignment(self):
        name = self.get_name()
        self.match("=")
        self.bool_expression()
        self.emit_ln(f"local.set ${name}")

    def do_if(self, breakloop_label: str = ""):
        self.match("i")
        self.bool_expression()
        self.emit_ln("if")
        self.block(breakloop_label)
        if self.look == "l":
            self.match("l")
            self.emit_ln("else")
            self.block(breakloop_label)
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
        self.emit_ln(f"block {labels['break']}")
        self.bool_expression()
        # For a while loop the break condition is the inverse of the loop
        # condition.
        self.emit_ln("i32.eqz")
        self.emit_ln(f"br_if {labels['break']}")
        self.block(labels["break"])
        self.emit_ln(f"br {labels['loop']}")
        self.match("e")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def do_loop(self):
        self.match("p")
        labels = self.generate_loop_labels()
        self.emit_ln(f"loop {labels['loop']}")
        self.emit_ln(f"block {labels['break']}")
        self.block(labels["break"])
        self.emit_ln(f"br {labels['loop']}")
        self.match("e")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def do_repeat(self):
        self.match("r")
        labels = self.generate_loop_labels()
        self.emit_ln(f"loop {labels['loop']}")
        self.emit_ln(f"block {labels['break']}")
        self.block(labels["break"])
        self.match("u")
        self.bool_expression()
        # The 'until' condition dictates when to break, so we just branch back
        # to the loop if the condition is false.
        self.emit_ln("i32.eqz")
        self.emit_ln(f"br_if {labels['loop']}")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def do_do(self):
        self.match("d")
        self.expression()
        labels = self.generate_loop_labels()

        # The loopvar starts with the value of the expression.
        self.emit_ln(f"local.set {labels['var']}")
        self.emit_ln(f"loop {labels['loop']}")
        self.emit_ln(f"block {labels['break']}")
        self.emit_ln(f"local.get {labels['var']}")
        self.emit_ln("i32.const 1")
        self.emit_ln("i32.sub")
        self.emit_ln(f"local.set {labels['var']}")
        self.block(labels["break"])
        self.match("e")
        self.emit_ln(f"local.get {labels['var']}")
        self.emit_ln("i32.const 0")
        self.emit_ln("i32.gt_s")
        self.emit_ln(f"br_if {labels['loop']}")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def do_for(self):
        self.match("f")
        labels = self.generate_loop_labels()
        self.get_name()  # loop variable name, ignored here
        self.match("=")

        # Loop var starts with initial_value - 1, per the tutorial (because
        # we increment it on each iteration before checking against the limit).
        self.expression()
        self.emit_ln("i32.const 1")
        self.emit_ln("i32.sub")
        self.emit_ln(f"local.set {labels['var']}")
        # NOTE: the original tutorial doesn't match "TO" here, so we won't
        # either.

        # Upper limit: compute expression once, save its value in the loop limit
        # variable.
        self.expression()
        self.emit_ln(f"local.set {labels['limit']}")
        self.emit_ln(f"loop {labels['loop']}")
        self.emit_ln(f"block {labels['break']}")

        # Fetch the loop variable, increment it and compare to the limit.
        self.emit_ln(f"local.get {labels['var']}")
        self.emit_ln("i32.const 1")
        self.emit_ln("i32.add")
        self.emit_ln(f"local.tee {labels['var']}")
        self.emit_ln(f"local.get {labels['limit']}")
        self.emit_ln("i32.ge_s")
        self.emit_ln(f"br_if {labels['break']}")

        self.block(labels["break"])
        self.emit_ln(f"br {labels['loop']}")
        self.match("e")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def block(self, breakloop_label: str = ""):
        # breakloop_label is used for emitting break statements inside loops.
        while self.look not in ("e", "l", "u", ""):
            match self.look:
                case "i":
                    self.do_if(breakloop_label)
                case "w":
                    self.do_while()
                case "p":
                    self.do_loop()
                case "r":
                    self.do_repeat()
                case "d":
                    self.do_do()
                case "f":
                    self.do_for()
                case "b":
                    self.do_break(breakloop_label)
                case _:
                    self.assignment()
