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


# In our scanner, all keywords map to TokenKind.NAME with value equal to
# the keyword string.
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

        # Current token.
        self.token = None
        self.output = output
        self.loopcount = 0

        self.advance_scanner()

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

    def match(self, kind: TokenKind) -> str:
        """Matches the current token's kind and returns its value.

        Advances to the next token if matched; otherwise, aborts.
        """
        if self.token.kind != kind:
            self.expected(f"'{kind}'")
        value = self.token.value
        self.advance_scanner()
        return value

    def match_name(self, name: str):
        if self.token.kind == TokenKind.NAME and self.token.value == name:
            self.advance_scanner()
        else:
            self.expected(f"'{name}'")

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
        name = self.match(TokenKind.NAME)
        if self.token.kind == TokenKind.LPAREN:
            self.advance_scanner()
            self.match(TokenKind.RPAREN)
            self.emit_ln(f"call ${name}")
        else:
            self.emit_ln(f"local.get ${name}")

    def signed_factor(self):
        if self.token.kind == TokenKind.ADD:
            self.advance_scanner()
            self.factor()
        elif self.token.kind == TokenKind.SUB:
            self.advance_scanner()
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
            self.advance_scanner()
            self.bool_expression()
            self.match(TokenKind.RPAREN)
        elif self.token.kind == TokenKind.NAME:
            self.ident()
        else:
            num = self.match(TokenKind.NUMBER)
            self.emit_ln(f"i32.const {num}")

    def multiply(self):
        self.advance_scanner()
        self.factor()
        self.emit_ln("i32.mul")

    def divide(self):
        self.advance_scanner()
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
        self.advance_scanner()
        self.term()
        self.emit_ln("i32.add")

    def subtract(self):
        self.advance_scanner()
        self.term()
        self.emit_ln("i32.sub")

    def expression(self):
        self.term()
        while self.token.kind in (TokenKind.ADD, TokenKind.SUB):
            if self.token.kind == TokenKind.ADD:
                self.add()
            else:
                self.subtract()

    def bool_or(self):
        self.advance_scanner()
        self.bool_term()
        self.emit_ln("i32.or")

    def bool_xor(self):
        self.advance_scanner()
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
            self.advance_scanner()
            self.not_factor()
            self.emit_ln("i32.and")

    def not_factor(self):
        if self.token.kind == TokenKind.NOT:
            self.advance_scanner()
            self.bool_factor()
            self.emit_ln("i32.eqz")
        else:
            self.bool_factor()

    def bool_factor(self):
        self.relation()

    def equals(self):
        self.advance_scanner()
        self.expression()
        self.emit_ln("i32.eq")

    def not_equals(self):
        self.advance_scanner()
        self.expression()
        self.emit_ln("i32.ne")

    def less_than(self):
        self.advance_scanner()
        self.expression()
        self.emit_ln("i32.lt_s")

    def greater_than(self):
        self.advance_scanner()
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
        name = self.match(TokenKind.NAME)
        self.match(TokenKind.EQUAL)
        self.bool_expression()
        self.emit_ln(f"local.set ${name}")

    def do_if(self, breakloop_label: str = ""):
        self.advance_scanner()
        self.bool_expression()
        self.emit_ln("if")
        self.block(breakloop_label)
        if self.token.kind == TokenKind.NAME and self.token.value == "ELSE":
            self.advance_scanner()
            self.emit_ln("else")
            self.block(breakloop_label)
        self.match_name("END")
        self.emit_ln("end")

    def do_break(self, breakloop_label: str):
        if breakloop_label == "":
            self.abort("No loop to break from")
        self.advance_scanner()
        self.emit_ln(f"br {breakloop_label}")

    def do_repeat(self):
        self.advance_scanner()
        labels = self.generate_loop_labels()
        self.emit_ln(f"loop {labels['loop']}")
        self.emit_ln(f"block {labels['break']}")
        self.block(labels["break"])
        self.match_name("UNTIL")
        self.bool_expression()
        # The 'until' condition dictates when to break, so we just branch back
        # to the loop if the condition is false.
        self.emit_ln("i32.eqz")
        self.emit_ln(f"br_if {labels['loop']}")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def block(self, breakloop_label: str = ""):
        # breakloop_label is used for emitting break statements inside loops.
        while self.token.kind != TokenKind.EOF:
            if self.token.kind != TokenKind.NAME:
                self.abort("Expected a statement")
            match self.token.value:
                case "ELSE" | "END" | "UNTIL":
                    break
                case "IF":
                    self.do_if(breakloop_label)
                case "REPEAT":
                    self.do_repeat()
                case "BREAK":
                    self.do_break(breakloop_label)
                case _:
                    self.assignment()
