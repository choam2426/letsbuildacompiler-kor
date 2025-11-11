import io
import unittest
from part10_introducing_tiny import Compiler


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
        compiler = Compiler("pvxvyvzbe.", output=output)
        compiler.prog()

        print(self.split_emission(output))
        # self.assertEqual(
        #     self.split_emission(output),
        #     ["; Module X", "(module", ")"],
        # )


if __name__ == "__main__":
    unittest.main()
