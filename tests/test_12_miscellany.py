import io
from typing import TextIO
import unittest
from tests.wasm_util import run_wasm_with_io
from part12_miscellany import Compiler


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
        self,
        src: str,
        instream: TextIO | None = None,
        outstream: TextIO | None = None,
        show=False,
    ) -> int:
        full_code = self._compile_to_wasm(src, show=show)
        return run_wasm_with_io(full_code, instream=instream, outstream=outstream)

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

    def test_comments(self):
        result = self.compile_and_run_with_io(
            """
        p
            v x=8,y,z { a comment }
        b
            y = x = 8 {another comment}
            z = x {embedded comment} < 5
            y = y & !z
            x = y + { 9 + this is a comment doesn't count } 0
        e.
        """
        )
        self.assertEqual(result, 1)

        result = self.compile_and_run_with_io(
            """
        p
            v x=8,y=3,z=2 { nested { comments } are ok }
        b
            x = (y + 5 = 8) & ({ nested { comments } are ok } z < 3)
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
            instream=None,
            outstream=out,
        )
        self.assertEqual(result, 5)
        emitted_lines = self.split_emission(out)
        self.assertEqual(emitted_lines, ["5", "14", "10"])

    def test_read_statement(self):
        inp = io.StringIO("7\n15\n")
        result = self.compile_and_run_with_io(
            r"""
        p
            v x,y,z
        b
            read(z)
            read(y)
            x = z + y
        e.
        """,
            instream=inp,
        )
        self.assertEqual(result, 22)

        inp = io.StringIO("3\n4\n5\n")
        result = self.compile_and_run_with_io(
            r"""
        p
            v x,y,z
        b
            read(x, y, z)
            x = y * z * x
        e.
        """,
            instream=inp,
        )
        self.assertEqual(result, 60)

    def test_read_and_write(self):
        inp = io.StringIO("8\n12\n")
        out = io.StringIO()
        result = self.compile_and_run_with_io(
            r"""
        p
            v x,y,z
        b
            read(x, y)
            z = x + y
            write(z, x * 2, y * 3)
        e.
        """,
            instream=inp,
            outstream=out,
        )
        self.assertEqual(result, 8)
        emitted_lines = self.split_emission(out)
        self.assertEqual(emitted_lines, ["20", "16", "36"])


if __name__ == "__main__":
    unittest.main()
