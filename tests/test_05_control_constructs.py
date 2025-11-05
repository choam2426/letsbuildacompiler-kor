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

    def test_block(self):
        output = io.StringIO()
        compiler = Compiler("iorbe", output=output)
        compiler.block()

        print(self.split_emission(output))
        # self.assertEqual(
        #     self.split_emission(output),
        #     [
        #         "(local $AXMO i32)",
        #         "i32.const 3",
        #         "local.set $AXMO",
        #     ],
        # )

if __name__ == "__main__":
    unittest.main()
