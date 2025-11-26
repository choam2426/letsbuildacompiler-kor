from __future__ import annotations
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


# The symbol table maps names to entries in a given scope. We don't support
# lexical scopes yet, so the only available scopes are in procedures and the
# global scope. Symbol tables do have parent links to allow lookups in a parent
# scope and temporary shadowing of variables in procedures.
#
# A name is mapped to an entry, which is of type SymbolTableEntry.
@dataclass
class GlobalVar:
    pass


@dataclass
class LocalVar:
    ref: bool


@dataclass
class Procedure:
    params: list[NamedEntry]


SymbolTableEntry = GlobalVar | LocalVar | Procedure


@dataclass
class NamedEntry:
    name: str
    entry: SymbolTableEntry


@dataclass
class SymbolTable:
    entries: dict[str, SymbolTableEntry]
    parent: SymbolTable | None = None


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

    def lookup_symbol(self, name: str) -> SymbolTableEntry | None:
        """Looks up a name in the symbol table.

        Starts with self.symtable and goes up the parent chain.
        """
        table = self.symtable
        while table is not None:
            if name in table.entries:
                return table.entries[name]
            table = table.parent
        return None

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
        """Matches the current token as a NAME with the given value.

        Advances to the next token if matched; otherwise, aborts.
        """
        if self.token.kind == TokenKind.NAME and self.token.value == name:
            self.advance_scanner()
        else:
            self.expected(f"'{name}'")

    def token_is_name(self, name: str) -> bool:
        return self.token.kind == TokenKind.NAME and self.token.value == name

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
        self.emit_ln("  (memory 8)")
        self.emit_ln("  ;; Linear stack pointer. Used to pass parameters by ref.")
        self.emit_ln("  ;; Grows downwards (towards lower addresses).")
        self.emit_ln("  (global $__sp (mut i32) (i32.const 65536))")
        self.emit_ln("")

    def module_epilog(self):
        self.emit_ln(")")

    def add_symbol(self, name: str, entry: SymbolTableEntry):
        if name in self.symtable.entries:
            self.abort(f"Duplicate symbol {name}")
        self.symtable.entries[name] = entry

    def alloc_var(self, name: str, is_global: bool):
        if is_global:
            value = "0"
            if self.token.kind == TokenKind.EQUAL:
                self.advance_scanner()
                if self.token.kind == TokenKind.SUB:
                    self.advance_scanner()
                    value = "-" + self.match(TokenKind.NUMBER)
                else:
                    value = self.match(TokenKind.NUMBER)
            self.add_symbol(name, GlobalVar())
            self.emit_ln(f"(global ${name} (mut i32) (i32.const {value}))")
        else:
            self.add_symbol(name, LocalVar(ref=False))
            self.emit_ln(f"(local ${name} i32)")

    def undefined(self, name: str):
        self.abort(f"Undefined identifier {name}")

    def ident(self):
        name = self.match(TokenKind.NAME)
        entry = self.lookup_symbol(name)
        match entry:
            case None:
                self.undefined(name)
            case LocalVar(ref=True):
                self.emit_ln(f"local.get ${name}")
                self.emit_ln("i32.load")
            case LocalVar(ref=False):
                self.emit_ln(f"local.get ${name}")
            case GlobalVar():
                self.emit_ln(f"global.get ${name}")
            case _:
                self.abort(f"Cannot refer to {name}")

    def toplevel(self):
        """Top-level entry point for the compiler.

        Called after initialization to start the compilation process.
        """
        self.module_prolog()
        self.indent += 2
        self.top_decls()
        self.indent -= 2
        self.module_epilog()

    # <top-level decl> ::= <data decl> | <procedure> | <main program>
    # <data decl> ::= 'VAR' <var-list>
    # <procedure> ::= 'PROCEDURE' <ident> <block> 'END'
    # <main program> ::= 'PROGRAM' <ident> <block> 'END'
    def top_decls(self):
        while self.token.kind != TokenKind.DOT:
            if self.token.kind != TokenKind.NAME:
                self.expected("a top-level declaration")
            match self.token.value:
                case "VAR":
                    self.decl(is_global=True)
                    self.semi()
                case "PROCEDURE":
                    self.procedure()
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
        self.emit_ln('(func $main (export "main") (result i32)')
        self.indent += 2
        self.block()

        # By convention our "ABI", the main function returns the value of the
        # global variable X.
        self.emit_ln("global.get $X")
        self.indent -= 2
        self.emit_ln(")")
        self.match_name("END")

    def procedure(self):
        self.advance_scanner()
        name = self.match(TokenKind.NAME)

        # Collect parameters
        self.match(TokenKind.LPAREN)
        params = []
        if self.token.kind != TokenKind.RPAREN:
            param = self.procedure_param()
            params.append(param)
            while self.token.kind == TokenKind.COMMA:
                self.advance_scanner()
                param = self.procedure_param()
                params.append(param)
        self.match(TokenKind.RPAREN)

        # Add procedure to symbol table
        self.add_symbol(name, Procedure(params=params))

        # Push frame onto symtable with parameters
        new_entries = {p.name: p.entry for p in params}
        self.symtable = SymbolTable(entries=new_entries, parent=self.symtable)

        params_str = " ".join(f"(param ${p.name} i32)" for p in params)
        self.emit_ln("")
        self.emit_ln(f"(func ${name} {params_str}")
        self.indent += 2

        # Process local declarations
        while self.token_is_name("VAR"):
            self.decl(is_global=False)
            self.semi()

        self.block()

        self.indent -= 2
        self.emit_ln(")")
        self.match_name("END")

        # Pop frame from symtable
        assert self.symtable.parent is not None
        self.symtable = self.symtable.parent

    # <procedure-param> ::= [ 'ref' ] <ident>
    def procedure_param(self) -> NamedEntry:
        ref_or_name = self.match(TokenKind.NAME)
        if ref_or_name == "REF":
            name = self.match(TokenKind.NAME)
            return NamedEntry(name, LocalVar(ref=True))
        else:
            return NamedEntry(ref_or_name, LocalVar(ref=False))

    # <var-list> ::= <var> (, <var> )*
    # <var> ::= <ident> [ = <num> ]
    def decl(self, is_global: bool):
        self.match_name("VAR")
        self.alloc_var(self.match(TokenKind.NAME), is_global=is_global)
        while self.token.kind == TokenKind.COMMA:
            self.advance_scanner()
            self.alloc_var(self.match(TokenKind.NAME), is_global=is_global)

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
                self.assign_or_proc()
        return False

    def block(self, breakloop_label: str = ""):
        # breakloop_label is used for emitting break statements inside loops.
        while self.token.kind != TokenKind.EOF:
            if self.statement(breakloop_label):
                break
            self.semi()

    # <proc> ::= <ident> ( )
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
    def assign_or_proc(self):
        name = self.match(TokenKind.NAME)
        if self.token.kind == TokenKind.LPAREN:
            self.procedure_call(name)
        else:
            # Assignment
            entry = self.lookup_symbol(name)
            self.match(TokenKind.EQUAL)

            # For by-ref local variables, place the address on TOS before
            # the value, so we can store into it.
            match entry:
                case LocalVar(ref=True):
                    self.emit_ln(f"local.get ${name}")

            self.bool_expression()

            match entry:
                case None:
                    self.undefined(name)
                case LocalVar(ref=True):
                    # The stack now has [ ... addr value ], so just store.
                    self.emit_ln("i32.store")
                case LocalVar(ref=False):
                    self.emit_ln(f"local.set ${name}")
                case GlobalVar():
                    self.emit_ln(f"global.set ${name}")
                case _:
                    self.abort(f"Cannot assign to {name}")

    # <proc call> ::= <ident> ( [ <call-param> ( , <call-param> )* ] )
    def procedure_call(self, name: str):
        self.match(TokenKind.LPAREN)
        entry = self.lookup_symbol(name)
        ref_entries = []
        match entry:
            case Procedure(params=params):
                if self.token.kind == TokenKind.RPAREN:
                    if len(params) != 0:
                        self.abort(
                            f"Procedure {name} expects {len(params)} parameters, got 0"
                        )
                else:
                    ref_entries.extend(self.call_argument(name, params))
                self.match(TokenKind.RPAREN)
            case _:
                self.abort(f"Undefined procedure {name}")
        self.emit_ln(f"call ${name}")
        if len(ref_entries) > 0:
            for i, entry in enumerate(reversed(ref_entries)):
                # Store the reference parameters back into their
                # variables.
                self.emit_ln(f";; restore parameter {entry.name} by ref")
                self.emit_ln("global.get $__sp")
                self.emit_ln(f"i32.load offset={i * 4}")
                if isinstance(entry.entry, LocalVar):
                    self.emit_ln(f"local.set ${entry.name}")
                elif isinstance(entry.entry, GlobalVar):
                    self.emit_ln(f"global.set ${entry.name}")
                else:
                    self.abort("Invalid reference parameter")
            self.emit_ln(";; clean up stack for ref parameters")
            self.emit_ln("global.get $__sp")
            self.emit_ln(f"i32.const {len(ref_entries) * 4}")
            self.emit_ln("i32.add")
            self.emit_ln("global.set $__sp")

    # Process a single argument to a call. Note that there is syntax table
    # dependent parsing here: for ref parameters we expect a variable name,
    # and for other parameters we accept arbitrary expressions.
    #
    # Returns a list of NamedEntry for parameters passed by reference that
    # need to be restored from the stack after the call.
    def call_argument(
        self, procname: str, proc_params: list[NamedEntry]
    ) -> list[NamedEntry]:
        ref_entries = []
        nparam = 0
        while True:
            if nparam < len(proc_params) and proc_params[nparam].entry.ref:
                param_name = self.match(TokenKind.NAME)
                entry = self.lookup_symbol(param_name)

                match entry:
                    case None:
                        self.undefined(param_name)
                    case LocalVar(ref=True):
                        # If the parameter is a by-ref local variable, we don't
                        # need to do anything special: just pass it as usual,
                        # as it's already an address.
                        self.emit_ln(f"local.get ${param_name}")
                    case LocalVar(ref=False):
                        self.alloc_stack_space(4)
                        self.emit_ln("global.get $__sp")
                        self.emit_ln(f"local.get ${param_name}")
                        self.emit_ln("i32.store")
                        self.emit_ln("global.get $__sp    ;; push address as parameter")
                        ref_entries.append(NamedEntry(param_name, entry))
                    case GlobalVar():
                        self.alloc_stack_space(4)
                        self.emit_ln("global.get $__sp")
                        self.emit_ln(f"global.get ${param_name}")
                        self.emit_ln("i32.store")
                        self.emit_ln("global.get $__sp    ;; push address as parameter")
                        ref_entries.append(NamedEntry(param_name, entry))
                    case _:
                        self.abort(f"Cannot refer to {param_name}")
            else:
                self.expression()
            nparam += 1
            if self.token.kind == TokenKind.COMMA:
                self.advance_scanner()
            else:
                break
        if nparam != len(proc_params):
            self.abort(
                f"Procedure {procname} expects {len(proc_params)} parameters, got {nparam}"
            )
        return ref_entries

    def alloc_stack_space(self, nbytes: int):
        self.emit_ln("global.get $__sp      ;; make space on stack")
        self.emit_ln(f"i32.const {nbytes}")
        self.emit_ln("i32.sub")
        self.emit_ln("global.set $__sp")

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
        self.emit_ln("i32.eqz")
        self.emit_ln(f"br_if {labels['break']}")
        self.block(labels["break"])
        self.emit_ln(f"br {labels['loop']}")
        self.match_name("END")
        self.indent -= 2
        self.emit_ln("end")  # end block
        self.indent -= 2
        self.emit_ln("end")  # end loop
