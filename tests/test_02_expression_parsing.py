import unittest
from part02_expression_parsing import Compiler


class TestCompiler(unittest.TestCase):
    def test_basic_term(self):
        import io

        output = io.StringIO()
        compiler = Compiler("3*9", output=output)
        compiler.term()
        self.assertEqual(output.getvalue(), "    i32.const 3\n    i32.const 9\n    i32.mul\n")


if __name__ == "__main__":
    unittest.main()
