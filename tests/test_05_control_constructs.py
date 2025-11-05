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
        compiler = Compiler("iorlxe", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            ["<condition>", "if", "O", "R", "else", "X", "end"],
        )

    def test_block_before_after_if(self):
        output = io.StringIO()
        compiler = Compiler("aixced", output=output)
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
                "D",
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
                "loop $loop0",
                "block $breakloop0",
                "<condition>",
                "i32.eqz",
                "br_if $breakloop0",
                "X",
                "Y",
                "Z",
                "br $loop0",
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
                "loop $loop0",
                "block $breakloop0",
                "<condition>",
                "i32.eqz",
                "br_if $breakloop0",
                "X",
                "br $breakloop0",
                "Y",
                "br $loop0",
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
                "loop $loop0",
                "block $breakloop0",
                "<condition>",
                "i32.eqz",
                "br_if $breakloop0",
                "<condition>",
                "if",
                "X",
                "br $breakloop0",
                "Y",
                "end",
                "Z",
                "br $loop0",
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
                "loop $loop0",
                "block $breakloop0",
                "X",
                "br $breakloop0",
                "Y",
                "br $loop0",
                "end",
                "end",
            ],
        )


if __name__ == "__main__":
    unittest.main()
