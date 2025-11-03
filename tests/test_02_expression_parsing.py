import io
import unittest
from part02_expression_parsing import Compiler


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

    def test_basic_term(self):
        output = io.StringIO()
        compiler = Compiler("3*9", output=output)
        compiler.term()

        self.assertEqual(
            self.split_emission(output), ["i32.const 3", "i32.const 9", "i32.mul"]
        )

    def test_expression(self):
        output = io.StringIO()
        compiler = Compiler("(3+5)*2-8/4", output=output)
        compiler.expression()

        self.assertEqual(
            self.split_emission(output),
            [
                "i32.const 3",
                "i32.const 5",
                "i32.add",
                "i32.const 2",
                "i32.mul",
                "i32.const 8",
                "i32.const 4",
                "i32.div",
                "i32.sub",
            ],
        )


if __name__ == "__main__":
    unittest.main()
