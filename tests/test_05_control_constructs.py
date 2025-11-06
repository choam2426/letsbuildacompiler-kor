import io
import unittest
from part05_control_constructs import Compiler


class TestCompilerEmittedSource(unittest.TestCase):
    def split_emission(self, output):
        """Return compiler emission as a list of non-empty lines.

        Accepts either a string or a StringIO-like object with getvalue().
        """
        if hasattr(output, "getvalue"):
            text = output.getvalue()
        else:
            text = str(output)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def test_ifelse(self):
        output = io.StringIO()
        compiler = Compiler("ioylxe", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            ["<condition>", "if", "O", "Y", "else", "X", "end"],
        )

    def test_block_before_after_if(self):
        output = io.StringIO()
        compiler = Compiler("aixcey", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "A",
                "<condition>",
                "if",
                "X",
                "C",
                "end",
                "Y",
            ],
        )

    def test_nested_if(self):
        output = io.StringIO()
        compiler = Compiler("iaixeye", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "<condition>",
                "if",
                "A",
                "<condition>",
                "if",
                "X",
                "end",
                "Y",
                "end",
            ],
        )

    def test_basic_while(self):
        output = io.StringIO()
        compiler = Compiler("wxyze", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "loop $loop1",
                "block $breakloop1",
                "<condition>",
                "i32.eqz",
                "br_if $breakloop1",
                "X",
                "Y",
                "Z",
                "br $loop1",
                "end",
                "end",
            ],
        )

    def test_while_with_break(self):
        output = io.StringIO()
        compiler = Compiler("wxbye", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "loop $loop1",
                "block $breakloop1",
                "<condition>",
                "i32.eqz",
                "br_if $breakloop1",
                "X",
                "br $breakloop1",
                "Y",
                "br $loop1",
                "end",
                "end",
            ],
        )

    def test_while_break_in_if(self):
        output = io.StringIO()
        compiler = Compiler("wixbyeze", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "loop $loop1",
                "block $breakloop1",
                "<condition>",
                "i32.eqz",
                "br_if $breakloop1",
                "<condition>",
                "if",
                "X",
                "br $breakloop1",
                "Y",
                "end",
                "Z",
                "br $loop1",
                "end",
                "end",
            ],
        )

    def test_loop_with_break(self):
        output = io.StringIO()
        compiler = Compiler("pxbye", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "loop $loop1",
                "block $breakloop1",
                "X",
                "br $breakloop1",
                "Y",
                "br $loop1",
                "end",
                "end",
            ],
        )

    def test_repeat_loop(self):
        output = io.StringIO()
        compiler = Compiler("rxyu", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "loop $loop1",
                "block $breakloop1",
                "X",
                "Y",
                "<condition>",
                "i32.eqz",
                "br_if $loop1",
                "end",
                "end",
            ],
        )

    def test_do_loop(self):
        output = io.StringIO()
        compiler = Compiler("dxye", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "<expression>",
                "loop $loop1",
                "block $breakloop1",
                "i32.const 1",
                "i32.sub",
                "X",
                "Y",
                "local.tee $tmp0",
                "local.get $tmp0",
                "i32.const 0",
                "i32.gt_u",
                "br_if $loop1",
                "end",
                "end",
                "drop",
            ],
        )

    def test_for_loop(self):
        output = io.StringIO()
        compiler = Compiler("ft=xyze", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "<expression>",
                "i32.const 1",
                "i32.sub",
                "local.set $for0",
                "<expression>",
                "loop $loop1",
                "block $breakloop1",
                "local.tee $tmp0",
                "local.get $tmp0",
                "local.get $for0",
                "i32.const 1",
                "i32.add",
                "local.tee $for0",
                "i32.ge_u",
                "br_if $breakloop1",
                "X",
                "Y",
                "Z",
                "br $loop1",
                "end",
                "end",
                "drop",
            ],
        )

    def test_nested_loops(self):
        output = io.StringIO()
        compiler = Compiler("pmwxeze", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "loop $loop1",
                "block $breakloop1",
                "M",
                "loop $loop2",
                "block $breakloop2",
                "<condition>",
                "i32.eqz",
                "br_if $breakloop2",
                "X",
                "br $loop2",
                "end",
                "end",
                "Z",
                "br $loop1",
                "end",
                "end",
            ],
        )


if __name__ == "__main__":
    unittest.main()
