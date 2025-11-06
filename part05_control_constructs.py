from typing import TextIO
import sys


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
        # Note: for part 5, we're back to only supporting single-letter names.
        if not self.look.isalpha():
            self.expected("Name")
        name = self.look.upper()
        self.get_char()
        self.skip_white()
        return name

    def get_num(self) -> str:
        # Note: for part 5, we're back to only supporting single-digit numbers.
        if not self.look.isdigit():
            self.expected("Integer")
        num = self.look
        self.get_char()
        self.skip_white()
        return num

    def emit(self, s: str):
        self.output.write("    " + s)

    def emit_ln(self, s: str):
        self.emit(s + "\n")

    def generate_loop_labels(self) -> tuple[str, str]:
        self.loopcount += 1
        return f"$loop{self.loopcount}", f"$breakloop{self.loopcount}"

    def condition(self):
        self.emit_ln("<condition>")

    def expression(self):
        self.emit_ln("<expression>")

    def other(self):
        self.emit_ln(self.get_name())

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
                case "b":
                    self.do_break(breakloop_label)
                case _:
                    self.other()

    def do_if(self, breakloop_label: str = ""):
        self.match("i")
        self.condition()
        self.emit_ln("if")
        self.block(breakloop_label)
        if self.look == "l":
            self.match("l")
            self.emit_ln("else")
            self.block(breakloop_label)
        self.match("e")
        self.emit_ln("end")

    def do_while(self):
        self.match("w")
        loop_label, breakloop_label = self.generate_loop_labels()
        self.emit_ln(f"loop {loop_label}")
        self.emit_ln(f"block {breakloop_label}")
        self.condition()
        # For a while loop the break condition is the inverse of the loop
        # condition.
        self.emit_ln("i32.eqz")
        self.emit_ln(f"br_if {breakloop_label}")
        self.block(breakloop_label)
        self.emit_ln(f"br {loop_label}")
        self.match("e")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def do_loop(self):
        self.match("p")
        loop_label, breakloop_label = self.generate_loop_labels()
        self.emit_ln(f"loop {loop_label}")
        self.emit_ln(f"block {breakloop_label}")
        self.block(breakloop_label)
        self.emit_ln(f"br {loop_label}")
        self.match("e")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def do_repeat(self):
        self.match("r")
        loop_label, breakloop_label = self.generate_loop_labels()
        self.emit_ln(f"loop {loop_label}")
        self.emit_ln(f"block {breakloop_label}")
        self.block(breakloop_label)
        self.match("u")
        self.condition()
        # The 'until' condition dictates when to break, so we just branch back
        # to the loop if the condition is false.
        self.emit_ln("i32.eqz")
        self.emit_ln(f"br_if {loop_label}")
        self.emit_ln("end")  # end block
        self.emit_ln("end")  # end loop

    def do_break(self, breakloop_label: str):
        if breakloop_label == "":
            self.abort("No loop to break from")
        self.match("b")
        self.emit_ln(f"br {breakloop_label}")
