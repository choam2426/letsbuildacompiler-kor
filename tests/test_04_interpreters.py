import io
import unittest
from part04_interpreters import Interpreter


class TestInterpreter(unittest.TestCase):
    def test_empty_output(self):
        out = io.StringIO()
        interpreter = Interpreter(".", output=out)
        interpreter.interpret()

        self.assertEqual(out.getvalue().strip(), "")

    def test_simple_assignment(self):
        out = io.StringIO()
        interpreter = Interpreter("A = 5\n!A.", output=out)
        interpreter.interpret()

        self.assertEqual(out.getvalue().strip(), "5")

    def test_assignment_and_expression(self):
        out = io.StringIO()
        interpreter = Interpreter("X = 10 Y = X * 2 + 5 !Y.", output=out)
        interpreter.interpret()

        self.assertEqual(out.getvalue().strip(), "25")

    def test_input_output(self):
        inp = io.StringIO("7\n21\n")
        out = io.StringIO()
        interpreter = Interpreter("?N   ?P  X = (N+1) * P  !X.", input=inp, output=out)
        interpreter.interpret()

        self.assertEqual(out.getvalue().strip(), "168")


if __name__ == "__main__":
    unittest.main()
