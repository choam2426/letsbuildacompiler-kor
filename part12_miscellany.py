from enum import Enum, auto
from dataclasses import dataclass
from typing import TextIO
import sys


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
    GREATER_EQUAL = auto()
    LESS_THAN = auto()
    LESS_EQUAL = auto()
    LPAREN = auto()
    RPAREN = auto()
    DOT = auto()
    COMMA = auto()
    SEMICOLON = auto()

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
    "<>": TokenKind.NOT_EQUAL,
    ">": TokenKind.GREATER_THAN,
    ">=": TokenKind.GREATER_EQUAL,
    "<": TokenKind.LESS_THAN,
    "<=": TokenKind.LESS_EQUAL,
    ".": TokenKind.DOT,
    ",": TokenKind.COMMA,
    ";": TokenKind.SEMICOLON,
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
        self.indent = 0
        self.loopcount = 0

        # Used only to avoid duplicate declarations for now.
        self.symtable = set()

        self.advance_scanner()

    def cur_char(self) -> str:
        if self.pos < len(self.src):
            return self.src[self.pos]
        return ""  # End of input

    def advance_scanner(self):
        self.skip_white()
        c = self.cur_char()
        if c == "":
            self.token = Token(TokenKind.EOF, "")
            return
        elif self.scan_op(c):
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

    def skip_white(self):
        while True:
            c = self.cur_char()
            if c.isspace():
                self.pos += 1
            elif c == "{":
                self.skip_comment()
            else:
                break

    def skip_comment(self):
        while self.cur_char() != "}":
            self.pos += 1
            if self.cur_char() == "{":
                self.skip_comment()
        self.pos += 1  # Skip the closing "}"

    def scan_op(self, c: str) -> bool:
        """Scans an operator, possibly multi-character.

        If successful, sets self.token and returns True; else returns False.
        """
        cc = c
        if c == ">":
            self.pos += 1
            if (nc := self.cur_char()) == "=":
                cc += nc
        elif c == "<":
            self.pos += 1
            if (nc := self.cur_char()) in ("=", ">"):
                cc += nc
        if (op := _operator_table.get(cc, None)) is not None:
            self.token = Token(op, cc)
            self.pos += 1
            return True
        else:
            return False

    def abort(self, msg: str):
        raise Exception(f"Error: {msg}")

    def expected(self, s: str):
        self.abort(f"{s} expected [has token '{self.token.value}']")

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

    def token_is_name(self, name: str) -> bool:
        return self.token.kind == TokenKind.NAME and self.token.value == name

    def semi(self):
        if self.token.kind == TokenKind.SEMICOLON:
            self.advance_scanner()

    def generate_loop_labels(self) -> dict[str, str]:
        self.loopcount += 1
        return {
            "loop": f"$loop{self.loopcount}",
            "break": f"$breakloop{self.loopcount}",
        }

    def emit_ln(self, s: str):
        self.output.write(" " * self.indent + s + "\n")

    def prolog(self):
        self.emit_ln("(module")
        self.emit_ln('  (func $read_i32 (import "" "read_i32") (result i32))')
        self.emit_ln('  (func $write_i32 (import "" "write_i32") (param i32))')

    def epilog(self):
        self.emit_ln(")")

    def alloc_global(self, name: str):
        if name in self.symtable:
            self.abort(f"Duplicate global variable {name}")
        self.symtable.add(name)
        value = "0"
        if self.token.kind == TokenKind.EQUAL:
            self.advance_scanner()
            if self.token.kind == TokenKind.SUB:
                self.advance_scanner()
                value = "-" + self.match(TokenKind.NUMBER)
            else:
                value = self.match(TokenKind.NUMBER)
        self.emit_ln(f"(global ${name} (mut i32) (i32.const {value}))")

    def undefined(self, name: str):
        self.abort(f"Undefined identifier {name}")

    def ident(self):
        name = self.match(TokenKind.NAME)
        if self.token.kind == TokenKind.LPAREN:
            self.advance_scanner()
            self.match(TokenKind.RPAREN)
            self.emit_ln(f"call ${name}")
        else:
            self.emit_ln(f"global.get ${name}")

    def prog(self):
        self.match_name("P")
        self.semi()
        self.prolog()
        self.indent += 2
        self.top_decls()
        self.main()
        self.match(TokenKind.DOT)
        self.indent -= 2
        self.epilog()

    # <main> ::= 'b' <block> 'e'
    def main(self):
        self.match_name("B")
        self.emit_ln('(func $main (export "main") (result i32)')
        self.indent += 2
        self.block()
        self.emit_ln("global.get $X")
        self.indent -= 2
        self.emit_ln(")")
        self.match_name("E")

    # <top-level decls> ::= <data declaration> ( ';' <data declaration> )*
    # <data declaration> ::= 'v' <var-list>
    def top_decls(self):
        while not self.token_is_name("B"):
            if self.token_is_name("V"):
                self.decl()
                self.semi()
            else:
                self.abort(f"unrecognized keyword '{self.token.value}'")

    # <var-list> ::= <var> (, <var> )*
    # <var> ::= <ident> [ = <num> ]
    def decl(self):
        self.match_name("V")
        self.alloc_global(self.match(TokenKind.NAME))
        while self.token.kind == TokenKind.COMMA:
            self.advance_scanner()
            self.alloc_global(self.match(TokenKind.NAME))

    # <if> ::= I <bool-expression> <block> [ L <block>] E
    # <while> ::= W <bool-expression> <block> E
    # <block> ::= <statement> ( ';' <statement> )*
    # <statement> ::= <if> | <while> | <assignment> | null
    def statement(self, breakloop_label: str = "") -> bool:
        """Handles a single statement starting at the current token.

        Returns True if the statement ends the block, False otherwise.
        """
        if self.token.kind != TokenKind.NAME:
            self.abort(f"expected a statement [got '{self.token.value}']")
        match self.token.value:
            case "E" | "L":
                return True
            case "I":
                self.do_if(breakloop_label)
            case "W":
                self.do_while()
            case "B":
                self.do_break(breakloop_label)
            case "READ":
                self.do_read()
            case "WRITE":
                self.do_write()
            case _:
                self.assignment()
        return False

    def block(self, breakloop_label: str = ""):
        # breakloop_label is used for emitting break statements inside loops.
        while self.token.kind != TokenKind.EOF:
            if self.statement(breakloop_label):
                break
            self.semi()

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
        name = self.match(TokenKind.NAME)
        self.match(TokenKind.EQUAL)
        self.bool_expression()
        self.emit_assignment(name)

    def emit_assignment(self, name: str):
        if name not in self.symtable:
            self.undefined(name)
        self.emit_ln(f"global.set ${name}")

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

    def neg_factor(self):
        self.match(TokenKind.SUB)
        if self.token.kind == TokenKind.NUMBER:
            self.emit_ln(f"i32.const -{self.match(TokenKind.NUMBER)}")
        else:
            self.factor()
            self.emit_ln("i32.const -1")
            self.emit_ln("i32.mul")

    def first_factor(self):
        match self.token.kind:
            case TokenKind.ADD:
                self.advance_scanner()
                self.factor()
            case TokenKind.SUB:
                self.neg_factor()
            case _:
                self.factor()

    def multiply(self):
        self.advance_scanner()
        self.factor()
        self.emit_ln("i32.mul")

    def divide(self):
        self.advance_scanner()
        self.factor()
        self.emit_ln("i32.div_s")

    def term1(self):
        # Common code for term and first_term
        while self.token.kind in (TokenKind.MUL, TokenKind.DIV):
            if self.token.kind == TokenKind.MUL:
                self.multiply()
            elif self.token.kind == TokenKind.DIV:
                self.divide()

    def term(self):
        self.factor()
        self.term1()

    def first_term(self):
        self.first_factor()
        self.term1()

    def add(self):
        self.advance_scanner()
        self.term()
        self.emit_ln("i32.add")

    def subtract(self):
        self.advance_scanner()
        self.term()
        self.emit_ln("i32.sub")

    def expression(self):
        self.first_term()
        while self.token.kind in (TokenKind.ADD, TokenKind.SUB):
            if self.token.kind == TokenKind.ADD:
                self.add()
            elif self.token.kind == TokenKind.SUB:
                self.subtract()

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

    def less_equal(self):
        self.advance_scanner()
        self.expression()
        self.emit_ln("i32.le_s")

    def greater_than(self):
        self.advance_scanner()
        self.expression()
        self.emit_ln("i32.gt_s")

    def greater_equal(self):
        self.advance_scanner()
        self.expression()
        self.emit_ln("i32.ge_s")

    def relation(self):
        self.expression()
        match self.token.kind:
            case TokenKind.EQUAL:
                self.equals()
            case TokenKind.NOT_EQUAL:
                self.not_equals()
            case TokenKind.LESS_THAN:
                self.less_than()
            case TokenKind.LESS_EQUAL:
                self.less_equal()
            case TokenKind.GREATER_THAN:
                self.greater_than()
            case TokenKind.GREATER_EQUAL:
                self.greater_equal()
            case _:
                pass

    def not_factor(self):
        if self.token.kind == TokenKind.NOT:
            self.advance_scanner()
            self.relation()
            self.emit_ln("i32.eqz")
        else:
            self.relation()

    def bool_term(self):
        self.not_factor()
        while self.token.kind == TokenKind.AND:
            self.advance_scanner()
            self.not_factor()
            self.emit_ln("i32.and")

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
            elif self.token.kind == TokenKind.XOR:
                self.bool_xor()

    def do_if(self, breakloop_label: str = ""):
        self.advance_scanner()
        self.bool_expression()
        self.emit_ln("if")
        self.indent += 2
        self.block(breakloop_label)
        self.indent -= 2
        if self.token_is_name("L"):
            self.advance_scanner()
            self.emit_ln("else")
            self.indent += 2
            self.block(breakloop_label)
            self.indent -= 2
        self.match_name("E")
        self.emit_ln("end")

    def do_break(self, breakloop_label: str):
        if breakloop_label == "":
            self.abort("No loop to break from")
        self.match_name("B")
        self.emit_ln(f"br {breakloop_label}")

    def do_while(self):
        self.match_name("W")
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
        self.match_name("E")
        self.indent -= 2
        self.emit_ln("end")  # end block
        self.indent -= 2
        self.emit_ln("end")  # end loop

    def do_read(self):
        self.advance_scanner()
        self.match(TokenKind.LPAREN)
        self.emit_ln("call $read_i32")
        name = self.match(TokenKind.NAME)
        self.emit_assignment(name)
        while self.token.kind == TokenKind.COMMA:
            self.advance_scanner()
            self.emit_ln("call $read_i32")
            name = self.match(TokenKind.NAME)
            self.emit_assignment(name)
        self.match(TokenKind.RPAREN)

    def do_write(self):
        self.advance_scanner()
        self.match(TokenKind.LPAREN)
        self.expression()
        self.emit_ln("call $write_i32")
        while self.token.kind == TokenKind.COMMA:
            self.advance_scanner()
            self.expression()
            self.emit_ln("call $write_i32")
        self.match(TokenKind.RPAREN)
