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
        compiler = Compiler("iorlbe", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            ["<condition>", "if", "O", "R", "else", "B", "end"],
        )

    def test_block_before_after_if(self):
        output = io.StringIO()
        compiler = Compiler("aibced", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "A",
                "<condition>",
                "if",
                "B",
                "C",
                "end",
                "D",
            ],
        )

    def test_nested_if(self):
        output = io.StringIO()
        compiler = Compiler("iaibece", output=output)
        compiler.block()

        self.assertEqual(
            self.split_emission(output),
            [
                "<condition>",
                "if",
                "A",
                "<condition>",
                "if",
                "B",
                "end",
                "C",
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


if __name__ == "__main__":
    unittest.main()
