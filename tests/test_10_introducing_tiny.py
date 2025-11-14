import io
from typing import TextIO
import unittest
from tests.wasm_util import run_wasm_with_io
from part10_introducing_tiny import Compiler


class TestCompileAndExecute(unittest.TestCase):
    def _compile_to_wasm(self, src: str, show=False) -> str:
        output = io.StringIO()
        compiler = Compiler(src, output=output)
        compiler.prog()
        if show:
            print("--------- WASM CODE ---------")
            print(output.getvalue())
            print("-----------------------------")
        return output.getvalue()

    def compile_and_run_with_io(
        self, src: str, output: TextIO | None = None, show=False
    ) -> int:
        full_code = self._compile_to_wasm(src, show=show)
        return run_wasm_with_io(full_code, output)

    def split_emission(self, output):
        """Return compiler emission as a list of non-empty lines.

        Accepts either a string or a StringIO-like object with getvalue().
        """
        if hasattr(output, "getvalue"):
            text = output.getvalue()
        else:
            text = str(output)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def test_basic_assign(self):
        result = self.compile_and_run_with_io("p v x,y=5 b x=y+7 e.")
        self.assertEqual(result, 12)

        result = self.compile_and_run_with_io("p v x=6,y=5 b x=y+7+x e.")
        self.assertEqual(result, 18)

    def test_longer_var_names(self):
        result = self.compile_and_run_with_io(
            "p v firstVar=10,secondVar=20, x b x=firstVar+secondVar e."
        )
        self.assertEqual(result, 30)

    def test_assign_boolean_expr(self):
        result = self.compile_and_run_with_io(
            """
        p
            v x=8,y,z
        b
            y = x = 8
            z = x < 5
            y = y & !z
            x = y
        e.
        """
        )
        self.assertEqual(result, 1)

        result = self.compile_and_run_with_io(
            """
        p
            v x=8,y=3,z=2
        b
            x = (y + 5 = 8) & (z < 3)
        e.
        """
        )
        self.assertEqual(result, 1)

        result = self.compile_and_run_with_io(
            """
        p
            v x=8,y=4,z=2
        b
            x = (y + 5 = 8) & (z < 3)
        e.
        """
        )
        self.assertEqual(result, 0)

    def test_multichar_operators(self):
        code = r"""
        p
            v x=0,y={yval}
        b
            x = y >= 5
            x = x + (y <= 10)
            x = x + (y <> 3)
        e.
        """
        result = self.compile_and_run_with_io(code.format(yval=5))
        self.assertEqual(result, 3)

        result = self.compile_and_run_with_io(code.format(yval=20))
        self.assertEqual(result, 2)

        result = self.compile_and_run_with_io(code.format(yval=3))
        self.assertEqual(result, 1)

    def test_if_else(self):
        result = self.compile_and_run_with_io(
            r"""
        p
            v x=0,y=10
        b
            i x < 5
                x = 20
            l
                x = 30
            e
        e.
        """
        )
        self.assertEqual(result, 20)

        result = self.compile_and_run_with_io(
            r"""
        p
            v x=0,y=10
        b
            i x > 5
                x = 20
            l
                x = 30
            e
        e.
        """
        )
        self.assertEqual(result, 30)

    def test_while_loop(self):
        result = self.compile_and_run_with_io(
            r"""
        p
            v x=0,y=5
        b
            w y > 0
                x = x + 2
                y = y - 1
            e
        e.
        """
        )
        self.assertEqual(result, 10)

        # Same but with an early break
        result = self.compile_and_run_with_io(
            r"""
        p     
            v x=0,y=5
        b
            w y > 0
                x = x + 2
                i x = 6
                    b
                e
                y = y - 1
            e
        e.
        """
        )
        self.assertEqual(result, 6)

    def test_write_statement(self):
        out = io.StringIO()
        result = self.compile_and_run_with_io(
            r"""
        p
            v x=5,y=11
        b
            write(x)
            write(y + 3, x * 2)
        e.
        """,
            output=out,
        )
        self.assertEqual(result, 5)
        emitted_lines = self.split_emission(out)
        self.assertEqual(emitted_lines, ["5", "14", "10"])


if __name__ == "__main__":
    unittest.main()
