import io
import unittest
from tests.wasm_util import run_wasm
from part03_more_expressions import Compiler


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
        compiler = Compiler("axmo = 3", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "(local $AXMO i32)",
                "i32.const 3",
                "local.set $AXMO",
            ],
        )
    
    def test_expression_assignment(self):
        output = io.StringIO()
        compiler = Compiler("  n2 = 60 / (5 + 1)", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "(local $N2 i32)",
                "i32.const 60",
                "i32.const 5",
                "i32.const 1",
                "i32.add",
                "i32.div_s",
                "local.set $N2",
            ],
        )


if __name__ == "__main__":
    unittest.main()
