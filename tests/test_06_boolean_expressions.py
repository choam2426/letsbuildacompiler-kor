import io
import unittest
from part06_boolean_expressions import Compiler


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

    def test_basic_assignment(self):
        output = io.StringIO()
        compiler = Compiler("x = 3", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "(local $X i32)",
                "i32.const 3",
                "local.set $X",
            ],
        )
    
    def test_boolean_expression_assignment(self):
        output = io.StringIO()
        compiler = Compiler("X = Y < 3", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "(local $X i32)",
                "local.get $Y",
                "i32.const 3",
                "i32.lt_s",
                "local.set $X",
            ],
        )


if __name__ == "__main__":
    unittest.main()
