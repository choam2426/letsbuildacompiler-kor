from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass
from typing import TextIO, NoReturn
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


class ValueType(Enum):
    TypeLong = auto()
    TypeQuad = auto()


# For this part, we're back to supporting just global variables, folding them
# into a single SymbolTableEntry type.
# Each entry has a type.
@dataclass
class SymbolTableEntry:
    typ: ValueType = ValueType.TypeQuad


@dataclass
class SymbolTable:
    entries: dict[str, SymbolTableEntry]


class Compiler:
    # After initialization, the entry point for this compiler is the
    # toplevel() method.
    def __init__(self, src: str, output: TextIO = sys.stdout):
        self.src = src
        self.pos = 0

        self.token = None
        self.output = output
        self.indent = 0
        self.loopcount = 0

        self.symtable = SymbolTable(entries={})

        self.advance_scanner()

    def cur_char(self) -> str:
        """Gets the current character without advancing the position.

        Returns an empty string if at end of input.
        """
        if self.pos < len(self.src):
            return self.src[self.pos]
        return ""

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

    def lookup_symbol(self, name: str) -> SymbolTableEntry:
        """Looks up a name in the symbol table."""
        if name in self.symtable.entries:
            return self.symtable.entries[name]
        self.abort(f"Undefined identifier {name}")

    def abort(self, msg: str) -> NoReturn:
        raise Exception(f"Error: {msg}")

    def expected(self, s: str) -> NoReturn:
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
        """Matches the current token as a NAME with the given value.

        Advances to the next token if matched; otherwise, aborts.
        """
        if self.token.kind == TokenKind.NAME and self.token.value == name:
            self.advance_scanner()
        else:
            self.expected(f"'{name}'")

    def token_is_name(self, name: str) -> bool:
        return self.token.kind == TokenKind.NAME and self.token.value == name

    def type_from_name(self, type_name: str) -> ValueType:
        match type_name:
            case "LONG":
                return ValueType.TypeLong
            case "QUAD":
                return ValueType.TypeQuad
            case _:
                self.abort(f"Unknown type {type_name}")

    def type_to_wasm(self, typ: ValueType) -> str:
        match typ:
            case ValueType.TypeLong:
                return "i32"
            case ValueType.TypeQuad:
                return "i64"
            case _:
                self.abort(f"Unknown type {typ}")

    def semi(self):
        """Optionally consume a semicolon. No-op for other tokens."""
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

    def module_prolog(self):
        self.emit_ln("(module")
        self.emit_ln("")

    def module_epilog(self):
        self.emit_ln(")")

    def add_symbol(self, name: str, entry: SymbolTableEntry):
        if name in self.symtable.entries:
            self.abort(f"Duplicate symbol {name}")
        self.symtable.entries[name] = entry

    def alloc_var(self, name: str, typ: ValueType):
        value = "0"
        if self.token.kind == TokenKind.EQUAL:
            self.advance_scanner()
            if self.token.kind == TokenKind.SUB:
                self.advance_scanner()
                value = "-" + self.match(TokenKind.NUMBER)
            else:
                value = self.match(TokenKind.NUMBER)
        self.add_symbol(name, SymbolTableEntry(typ=typ))
        wasmtype = self.type_to_wasm(typ)
        self.emit_ln(f"(global ${name} (mut {wasmtype}) ({wasmtype}.const {value}))")

    def convert_type(self, from_type: ValueType, to_type: ValueType):
        """Emit code to convert value on TOS from from_type to to_type."""
        if from_type == to_type:
            return
        match (from_type, to_type):
            case (ValueType.TypeLong, ValueType.TypeQuad):
                self.emit_ln("i64.extend_i32_s")
            case (ValueType.TypeQuad, ValueType.TypeLong):
                self.emit_ln("i32.wrap_i64")
            case _:
                self.abort(f"Cannot convert from {from_type} to {to_type}")

    def undefined(self, name: str):
        self.abort(f"Undefined identifier {name}")

    # For this part, many of the parsing methods now return ValueType to
    # indicate the type of the expression they've parsed and emitted code for.
    def ident(self) -> ValueType:
        name = self.match(TokenKind.NAME)
        entry = self.lookup_symbol(name)
        self.emit_ln(f"global.get ${name}")
        return entry.typ

    def toplevel(self):
        """Top-level entry point for the compiler.

        Called after initialization to start the compilation process.
        """
        self.module_prolog()
        self.indent += 2
        self.top_decls()
        self.indent -= 2
        self.module_epilog()

    # <top-level decl> ::= <data decl> <main program>
    # <data decl> ::= 'VAR' ...
    # <main program> ::= 'PROGRAM' <ident> <block> 'END'
    def top_decls(self):
        while self.token.kind != TokenKind.DOT:
            if self.token.kind != TokenKind.NAME:
                self.expected("a top-level declaration")
            match self.token.value:
                case "VAR":
                    self.decl()
                    self.semi()
                case "PROGRAM":
                    self.program()
                case _:
                    self.abort(f"unrecognized keyword '{self.token.value}'")

    def program(self):
        # Consume PROGRAM <name> BEGIN
        self.advance_scanner()
        self.match(TokenKind.NAME)
        self.match_name("BEGIN")
        self.emit_ln("")
        self.emit_ln('(func $main (export "main") (result i64)')
        self.indent += 2
        self.emit_ln("(local $tmp i64)")
        self.block()

        # By convention (our "ABI"), the main function returns the value of the
        # global variable X.
        self.emit_ln("global.get $X")
        self.indent -= 2
        self.emit_ln(")")
        self.match_name("END")

    # <decl> ::= 'VAR' <type> <var-list>
    # <var-list> ::= <var> (, <var> )*
    # <var> ::= <ident> [ = <num> ]
    def decl(self):
        self.match_name("VAR")
        typ = self.type_from_name(self.match(TokenKind.NAME))
        self.alloc_var(self.match(TokenKind.NAME), typ=typ)
        while self.token.kind == TokenKind.COMMA:
            self.advance_scanner()
            self.alloc_var(self.match(TokenKind.NAME), typ=typ)

    # <if> ::= IF <bool-expression> <block> [ ELSE <block>] END
    # <while> ::= WHILE <bool-expression> <block> END
    # <block> ::= <statement> ( ';' <statement> )*
    # <statement> ::= <if> | <while> | <assignment> | null
    def statement(self, breakloop_label: str = "") -> bool:
        """Handles a single statement starting at the current token.

        Returns True if the statement ends the block, False otherwise.
        """
        if self.token.kind != TokenKind.NAME:
            self.expected("a statement")
        match self.token.value:
            case "END" | "ELSE":
                return True
            case "IF":
                self.do_if(breakloop_label)
            case "WHILE":
                self.do_while()
            case "BREAK":
                self.do_break(breakloop_label)
            case _:
                self.assign()
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
    def assign(self):
        name = self.match(TokenKind.NAME)
        entry = self.lookup_symbol(name)
        self.match(TokenKind.EQUAL)
        expr_type = self.bool_expression()
        self.convert_type(expr_type, entry.typ)
        self.emit_ln(f"global.set ${name}")

    def factor(self) -> ValueType:
        expr_type: ValueType
        if self.token.kind == TokenKind.LPAREN:
            self.advance_scanner()
            expr_type = self.bool_expression()
            self.match(TokenKind.RPAREN)
        elif self.token.kind == TokenKind.NAME:
            expr_type = self.ident()
        else:
            num = self.match(TokenKind.NUMBER)
            self.emit_ln(f"i64.const {num}")
            expr_type = ValueType.TypeQuad
        return expr_type

    def neg_factor(self) -> ValueType:
        self.match(TokenKind.SUB)
        if self.token.kind == TokenKind.NUMBER:
            self.emit_ln(f"i64.const -{self.match(TokenKind.NUMBER)}")
        else:
            expr_type = self.factor()
            self.convert_type(expr_type, ValueType.TypeQuad)
            self.emit_ln("i64.const -1")
            self.emit_ln("i64.mul")
        return ValueType.TypeQuad

    def first_factor(self) -> ValueType:
        match self.token.kind:
            case TokenKind.ADD:
                self.advance_scanner()
                return self.factor()
            case TokenKind.SUB:
                return self.neg_factor()
            case _:
                return self.factor()

    def multiply(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.factor()
        return self.type_matched_binop(lhs_type, rhs_type, "mul")

    def divide(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.factor()
        return self.type_matched_binop(lhs_type, rhs_type, "div_s")

    def term1(self, lhs_type: ValueType) -> ValueType:
        # Common code for term and first_term
        while self.token.kind in (TokenKind.MUL, TokenKind.DIV):
            if self.token.kind == TokenKind.MUL:
                lhs_type = self.multiply(lhs_type)
            elif self.token.kind == TokenKind.DIV:
                lhs_type = self.divide(lhs_type)
        return lhs_type

    def term(self) -> ValueType:
        lhs_type = self.factor()
        return self.term1(lhs_type)

    def first_term(self) -> ValueType:
        first_type = self.first_factor()
        return self.term1(first_type)

    def add(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.term()
        return self.type_matched_binop(lhs_type, rhs_type, "add")

    def subtract(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.term()
        return self.type_matched_binop(lhs_type, rhs_type, "sub")

    def expression(self) -> ValueType:
        expr_type = self.first_term()
        while self.token.kind in (TokenKind.ADD, TokenKind.SUB):
            if self.token.kind == TokenKind.ADD:
                expr_type = self.add(expr_type)
            elif self.token.kind == TokenKind.SUB:
                expr_type = self.subtract(expr_type)
        return expr_type

    def equals(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.expression()
        return self.type_matched_binop(lhs_type, rhs_type, "eq")

    def not_equals(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.expression()
        return self.type_matched_binop(lhs_type, rhs_type, "ne")

    def less_than(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.expression()
        return self.type_matched_binop(lhs_type, rhs_type, "lt_s")

    def less_equal(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.expression()
        return self.type_matched_binop(lhs_type, rhs_type, "le_s")

    def greater_than(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.expression()
        return self.type_matched_binop(lhs_type, rhs_type, "gt_s")

    def greater_equal(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.expression()
        return self.type_matched_binop(lhs_type, rhs_type, "ge_s")

    def relation(self) -> ValueType:
        lhs_type = self.expression()
        match self.token.kind:
            case TokenKind.EQUAL:
                return self.equals(lhs_type)
            case TokenKind.NOT_EQUAL:
                return self.not_equals(lhs_type)
            case TokenKind.LESS_THAN:
                return self.less_than(lhs_type)
            case TokenKind.LESS_EQUAL:
                return self.less_equal(lhs_type)
            case TokenKind.GREATER_THAN:
                return self.greater_than(lhs_type)
            case TokenKind.GREATER_EQUAL:
                return self.greater_equal(lhs_type)
            case _:
                return lhs_type

    def not_factor(self) -> ValueType:
        if self.token.kind == TokenKind.NOT:
            self.advance_scanner()
            expr_type = self.relation()
            if expr_type == ValueType.TypeLong:
                self.emit_ln("i32.eqz")
            else:
                self.emit_ln("i64.eqz")
            return expr_type
        else:
            return self.relation()

    def bool_term(self) -> ValueType:
        expr_type = self.not_factor()
        while self.token.kind == TokenKind.AND:
            self.advance_scanner()
            rhs_type = self.not_factor()
            expr_type = self.type_matched_binop(expr_type, rhs_type, "and")
        return expr_type

    def bool_or(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.bool_term()
        return self.type_matched_binop(lhs_type, rhs_type, "or")

    def bool_xor(self, lhs_type: ValueType) -> ValueType:
        self.advance_scanner()
        rhs_type = self.bool_term()
        return self.type_matched_binop(lhs_type, rhs_type, "xor")

    def bool_expression(self) -> ValueType:
        # expr_type starts with the type of the left-most bool-term, and is
        # updated after each operation. The type can only expand from long to
        # quad as needed.
        expr_type = self.bool_term()
        while self.token.kind in (TokenKind.OR, TokenKind.XOR):
            if self.token.kind == TokenKind.OR:
                expr_type = self.bool_or(expr_type)
            elif self.token.kind == TokenKind.XOR:
                expr_type = self.bool_xor(expr_type)
        return expr_type

    def type_matched_binop(
        self, type1: ValueType, type2: ValueType, op: str
    ) -> ValueType | NoReturn:
        match (type1, type2):
            case (ValueType.TypeLong, ValueType.TypeLong):
                self.emit_ln(f"i32.{op}")
                return ValueType.TypeLong
            case (ValueType.TypeQuad, ValueType.TypeQuad):
                self.emit_ln(f"i64.{op}")
                return ValueType.TypeQuad
            case (ValueType.TypeQuad, ValueType.TypeLong):
                self.emit_ln("i64.extend_i32_s")
                self.emit_ln(f"i64.{op}")
                return ValueType.TypeQuad
            case (ValueType.TypeLong, ValueType.TypeQuad):
                # Use local to hold the i64 value while we convert the i32 below
                # it to i64 as well.
                self.emit_ln("local.set $tmp")
                self.emit_ln("i64.extend_i32_s")
                self.emit_ln("local.get $tmp")
                self.emit_ln(f"i64.{op}")
                return ValueType.TypeQuad
            case _:
                self.abort(f"Cannot apply {op} to {type1} and {type2}")

    def do_if(self, breakloop_label: str = ""):
        self.advance_scanner()
        self.bool_expression()
        self.emit_ln("if")
        self.indent += 2
        self.block(breakloop_label)
        self.indent -= 2
        if self.token_is_name("ELSE"):
            self.advance_scanner()
            self.emit_ln("else")
            self.indent += 2
            self.block(breakloop_label)
            self.indent -= 2
        self.match_name("END")
        self.emit_ln("end")

    def do_break(self, breakloop_label: str):
        if breakloop_label == "":
            self.abort("No loop to break from")
        self.match_name("BREAK")
        self.emit_ln(f"br {breakloop_label}")

    def do_while(self):
        self.match_name("WHILE")
        labels = self.generate_loop_labels()
        self.emit_ln(f"loop {labels['loop']}")
        self.indent += 2
        self.emit_ln(f"block {labels['break']}")
        self.indent += 2
        self.bool_expression()
        # For a while loop the break condition is the inverse of the loop
        # condition.
        self.emit_ln("i64.eqz")
        self.emit_ln(f"br_if {labels['break']}")
        self.block(labels["break"])
        self.emit_ln(f"br {labels['loop']}")
        self.match_name("END")
        self.indent -= 2
        self.emit_ln("end")  # end block
        self.indent -= 2
        self.emit_ln("end")  # end loop
