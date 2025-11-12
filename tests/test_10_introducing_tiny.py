import io
import unittest
from tests.wasm_util import run_wasm
from part10_introducing_tiny import Compiler


class TestCompileAndExecute(unittest.TestCase):
    def compile_and_run(self, src: str, show=False) -> int:
        output = io.StringIO()
        compiler = Compiler(src, output=output)
        compiler.prog()
        full_code = output.getvalue()

        if show:
            print("--------- WASM CODE ---------")
            print(full_code)
            print("-----------------------------")
        return run_wasm(full_code)

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
        result = self.compile_and_run("p vx,y=5 b x=y+7 e.")
        self.assertEqual(result, 12)

        result = self.compile_and_run("p vx=6,y=5 b x=y+7+x e.")
        self.assertEqual(result, 18)

    def test_assign_boolean_expr(self):
        result = self.compile_and_run(
            """
        p
            vx=8,y,z
        b
            y = x = 8
            z = x < 5
            y = y & !z
            x = y
        e.
        """
        )
        self.assertEqual(result, 1)

        result = self.compile_and_run("""
        p
            vx=8,y=3,z=2
        b
            x = (y + 5 = 8) & (z < 3)
        e.
        """)
        self.assertEqual(result, 1)

        result = self.compile_and_run(
            """
        p
            vx=8,y=4,z=2
        b
            x = (y + 5 = 8) & (z < 3)
        e.
        """
        )
        self.assertEqual(result, 0)

    def test_if_else(self):
        result = self.compile_and_run(
            r"""
        p
            vx=0,y=10
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

        result = self.compile_and_run(
            r"""
        p
            vx=0,y=10
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
        result = self.compile_and_run(
            r"""
        p
            vx=0,y=5
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
        result = self.compile_and_run(
            r"""
        p     
            vx=0,y=5
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


if __name__ == "__main__":
    unittest.main()
