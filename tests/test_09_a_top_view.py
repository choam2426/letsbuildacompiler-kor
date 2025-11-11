import io
import unittest
from part09_a_top_view import Compiler


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

    def test_program(self):
        output = io.StringIO()
        compiler = Compiler("pA.", output=output)
        compiler.prog()

        print(self.split_emission(output))


if __name__ == "__main__":
    unittest.main()
