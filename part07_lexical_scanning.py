from enum import Enum, auto
from dataclasses import dataclass
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


class TokenKind(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    OR = auto()
    XOR = auto()
    AND = auto()
    NOT = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    GREATER_THAN = auto()
    LESS_THAN = auto()

    LPAREN = auto()
    RPAREN = auto()

    NUMBER = auto()
    NAME = auto()

    IF = auto()
    ELSE = auto()
    END = auto()
    UNTIL = auto()
    BREAK = auto()

    EOF = auto()


# Maps operators to tokens
_operator_table = {
    "+": TokenKind.ADD,
    "-": TokenKind.SUB,
    "*": TokenKind.MUL,
    "/": TokenKind.DIV,
    "(": TokenKind.LPAREN,
    ")": TokenKind.RPAREN,
    "|": TokenKind.OR,
    "~": TokenKind.XOR,
    "&": TokenKind.AND,
    "!": TokenKind.NOT,
    "=": TokenKind.EQUAL,
    "#": TokenKind.NOT_EQUAL,
    ">": TokenKind.GREATER_THAN,
    "<": TokenKind.LESS_THAN,
}


@dataclass
class Token:
    kind: TokenKind
    value: str


class Compiler:
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0
        self.token = None
        self.output = output
        self.loopcount = 0

        self.advance_scanner()
        print('Initialized scanner, first token:', self.token)

    def cur_char(self) -> str:
        if self.pos < len(self.src):
            return self.src[self.pos]
        return ""  # End of input

    def advance_scanner(self):
        self.skip_white()
        if self.pos >= len(self.src):
            self.token = Token(TokenKind.EOF, "")
            return

        c = self.cur_char()
        op = _operator_table.get(c, None)
        if op is not None:
            self.token = Token(op, c)
            self.pos += 1
            return
        elif c.isalpha():
            name = ""
            while self.cur_char().isalnum():
                name += self.cur_char().upper()
                self.pos += 1
            self.token = Token(TokenKind.NAME, name)
            return
        elif c.isdigit():
            num = ""
            while self.cur_char().isdigit():
                num += self.cur_char()
                self.pos += 1
            self.token = Token(TokenKind.NUMBER, num)
            return

        self.abort(f"Unrecognized character: '{c}'")

    def abort(self, msg: str):
        raise Exception(f"Error: {msg}")

    def expected(self, s: str):
        self.abort(f"{s} expected")

    def skip_white(self):
        while self.cur_char().isspace():
            self.pos += 1

    def match(self, kind: TokenKind):
        if self.token.kind == kind:
            self.advance_scanner()
        else:
            self.expected(f"'{kind}'")

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
        name = self.token.value
        self.match(TokenKind.NAME) # TODO: make match return for convenience
        if self.token.kind == TokenKind.LPAREN:
            self.match(TokenKind.LPAREN)
            self.match(TokenKind.RPAREN)
            self.emit_ln(f"call ${name}")
        else:
            self.emit_ln(f"local.get ${name}")

    def signed_factor(self):
        if self.token.kind == TokenKind.ADD:
            self.match(TokenKind.ADD)
            self.factor()
        elif self.token.kind == TokenKind.SUB:
            self.match(TokenKind.SUB)
            if self.token.kind == TokenKind.NUMBER:
                self.emit_ln(f"i32.const -{self.token.value}")
            else:
                self.factor()
                self.emit_ln("i32.const -1")
                self.emit_ln("i32.mul")
        else:
            self.factor()

    def factor(self):
        if self.token.kind == TokenKind.LPAREN:
            self.match(TokenKind.LPAREN)
            self.bool_expression()
            self.match(TokenKind.RPAREN)
        elif self.token.kind == TokenKind.NAME:
            self.ident()
        else:
            s = self.token.value
            self.match(TokenKind.NUMBER)
            self.emit_ln(f"i32.const {s}")

    def multiply(self):
        self.match(TokenKind.MUL)
        self.factor()
        self.emit_ln("i32.mul")

    def divide(self):
        self.match(TokenKind.DIV)
        self.factor()
        self.emit_ln("i32.div_s")

    def term(self):
        self.signed_factor()
        while self.token.kind in (TokenKind.MUL, TokenKind.DIV):
            if self.token.kind == TokenKind.MUL:
                self.multiply()
            else:
                self.divide()

    def add(self):
        self.match(TokenKind.ADD)
        self.term()
        self.emit_ln("i32.add")

    def subtract(self):
        self.match(TokenKind.SUB)
        self.term()
        self.emit_ln("i32.sub")

    def expression(self):
        print('in expression, token=', self.token)
        self.term()
        while self.token.kind in (TokenKind.ADD, TokenKind.SUB):
            if self.token.kind == TokenKind.ADD:
                self.add()
            else:
                self.subtract()

    def bool_or(self):
        self.match(TokenKind.OR)
        self.bool_term()
        self.emit_ln("i32.or")

    def bool_xor(self):
        self.match(TokenKind.XOR)
        self.bool_term()
        self.emit_ln("i32.xor")

    def bool_expression(self):
        self.bool_term()
        while self.token.kind in (TokenKind.OR, TokenKind.XOR):
            if self.token.kind == TokenKind.OR:
                self.bool_or()
            else:
                self.bool_xor()

    def bool_term(self):
        self.not_factor()
        while self.token.kind == TokenKind.AND:
            self.match(TokenKind.AND)
            self.not_factor()
            self.emit_ln("i32.and")

    def not_factor(self):
        if self.token.kind == TokenKind.NOT:
            self.match(TokenKind.NOT)
            self.bool_factor()
            self.emit_ln("i32.eqz")
        else:
            self.bool_factor()

    def bool_factor(self):
        self.relation()

    def equals(self):
        self.match(TokenKind.EQUAL)
        self.expression()
        self.emit_ln("i32.eq")

    def not_equals(self):
        self.match(TokenKind.NOT_EQUAL)
        self.expression()
        self.emit_ln("i32.ne")

    def less_than(self):
        self.match(TokenKind.LESS_THAN)
        self.expression()
        self.emit_ln("i32.lt_s")

    def greater_than(self):
        self.match(TokenKind.GREATER_THAN)
        self.expression()
        self.emit_ln("i32.gt_s")

    def relation(self):
        self.expression()
        match self.token.kind:
            case TokenKind.EQUAL:
                self.equals()
            case TokenKind.NOT_EQUAL:
                self.not_equals()
            case TokenKind.LESS_THAN:
                self.less_than()
            case TokenKind.GREATER_THAN:
                self.greater_than()

    def assignment(self):
        name = self.token.value
        print('in assignment, token=', self.token)
        self.match(TokenKind.NAME)
        print('after matching name, token=', self.token)
        self.match(TokenKind.EQUAL)
        print('after matching equal, token=', self.token)
        self.bool_expression()
        self.emit_ln(f"local.set ${name}")

    def do_if(self, breakloop_label: str = ""):
        self.match(TokenKind.IF)
        self.bool_expression()
        self.emit_ln("if")
        self.block(breakloop_label)
        if self.token.kind == TokenKind.ELSE:
            self.match(TokenKind.ELSE)
            self.emit_ln("else")
            self.block(breakloop_label)
        self.match(TokenKind.END)
        self.emit_ln("end")

    def do_break(self, breakloop_label: str):
        if breakloop_label == "":
            self.abort("No loop to break from")
        self.match(TokenKind.BREAK)
        self.emit_ln(f"br {breakloop_label}")

    # def do_while(self):
    #     self.match("w")
    #     labels = self.generate_loop_labels()
    #     self.emit_ln(f"loop {labels['loop']}")
    #     self.emit_ln(f"block {labels['break']}")
    #     self.bool_expression()
    #     # For a while loop the break condition is the inverse of the loop
    #     # condition.
    #     self.emit_ln("i32.eqz")
    #     self.emit_ln(f"br_if {labels['break']}")
    #     self.block(labels["break"])
    #     self.emit_ln(f"br {labels['loop']}")
    #     self.match("e")
    #     self.emit_ln("end")  # end block
    #     self.emit_ln("end")  # end loop

    # def do_loop(self):
    #     self.match("p")
    #     labels = self.generate_loop_labels()
    #     self.emit_ln(f"loop {labels['loop']}")
    #     self.emit_ln(f"block {labels['break']}")
    #     self.block(labels["break"])
    #     self.emit_ln(f"br {labels['loop']}")
    #     self.match("e")
    #     self.emit_ln("end")  # end block
    #     self.emit_ln("end")  # end loop

    # def do_repeat(self):
    #     self.match("r")
    #     labels = self.generate_loop_labels()
    #     self.emit_ln(f"loop {labels['loop']}")
    #     self.emit_ln(f"block {labels['break']}")
    #     self.block(labels["break"])
    #     self.match("u")
    #     self.bool_expression()
    #     # The 'until' condition dictates when to break, so we just branch back
    #     # to the loop if the condition is false.
    #     self.emit_ln("i32.eqz")
    #     self.emit_ln(f"br_if {labels['loop']}")
    #     self.emit_ln("end")  # end block
    #     self.emit_ln("end")  # end loop

    # def do_do(self):
    #     self.match("d")
    #     self.expression()
    #     labels = self.generate_loop_labels()

    #     # The loopvar starts with the value of the expression.
    #     self.emit_ln(f"local.set {labels['var']}")
    #     self.emit_ln(f"loop {labels['loop']}")
    #     self.emit_ln(f"block {labels['break']}")
    #     self.emit_ln(f"local.get {labels['var']}")
    #     self.emit_ln("i32.const 1")
    #     self.emit_ln("i32.sub")
    #     self.emit_ln(f"local.set {labels['var']}")
    #     self.block(labels["break"])
    #     self.match("e")
    #     self.emit_ln(f"local.get {labels['var']}")
    #     self.emit_ln("i32.const 0")
    #     self.emit_ln("i32.gt_s")
    #     self.emit_ln(f"br_if {labels['loop']}")
    #     self.emit_ln("end")  # end block
    #     self.emit_ln("end")  # end loop

    # def do_for(self):
    #     self.match("f")
    #     labels = self.generate_loop_labels()
    #     self.get_name()  # loop variable name, ignored here
    #     self.match("=")

    #     # Loop var starts with initial_value - 1, per the tutorial (because
    #     # we increment it on each iteration before checking against the limit).
    #     self.expression()
    #     self.emit_ln("i32.const 1")
    #     self.emit_ln("i32.sub")
    #     self.emit_ln(f"local.set {labels['var']}")
    #     # NOTE: the original tutorial doesn't match "TO" here, so we won't
    #     # either.

    #     # Upper limit: compute expression once, save its value in the loop limit
    #     # variable.
    #     self.expression()
    #     self.emit_ln(f"local.set {labels['limit']}")
    #     self.emit_ln(f"loop {labels['loop']}")
    #     self.emit_ln(f"block {labels['break']}")

    #     # Fetch the loop variable, increment it and compare to the limit.
    #     self.emit_ln(f"local.get {labels['var']}")
    #     self.emit_ln("i32.const 1")
    #     self.emit_ln("i32.add")
    #     self.emit_ln(f"local.tee {labels['var']}")
    #     self.emit_ln(f"local.get {labels['limit']}")
    #     self.emit_ln("i32.ge_s")
    #     self.emit_ln(f"br_if {labels['break']}")

    #     self.block(labels["break"])
    #     self.emit_ln(f"br {labels['loop']}")
    #     self.match("e")
    #     self.emit_ln("end")  # end block
    #     self.emit_ln("end")  # end loop

    def block(self, breakloop_label: str = ""):
        # breakloop_label is used for emitting break statements inside loops.
        while self.token.kind not in (
            TokenKind.END,
            TokenKind.ELSE,
            TokenKind.UNTIL,
            TokenKind.EOF,
        ):
            match self.token.kind:
                case TokenKind.IF:
                    self.do_if(breakloop_label)
                # case "w":
                #     self.do_while()
                # case "p":
                #     self.do_loop()
                # case "r":
                #     self.do_repeat()
                # case "d":
                #     self.do_do()
                # case "f":
                #     self.do_for()
                # case "b":
                #     self.do_break(breakloop_label)
                case _:
                    self.assignment()
