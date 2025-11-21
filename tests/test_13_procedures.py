import io
from typing import TextIO
import unittest
from tests.wasm_util import run_wasm
from part13_procedures import Compiler


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
        show=False,
    ) -> int:
        full_code = self._compile_to_wasm(src, show=show)
        return run_wasm(full_code)

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

    def test_semicolons(self):
        result = self.compile_and_run_with_io(
            r"""
        p ;
            v x=0;
            v y=10
        b
            x = x + 5;
            y = y - 2
            x = x + y;
        e.
        """
        )
        self.assertEqual(result, 13)

    def test_if_else(self):
        result = self.compile_and_run_with_io(
            r"""
        p
            v x=0,y=10
        b
            i x < 5
                x = 20 ;
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
                x = 30 ;
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
                x = x + 2 ;
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


if __name__ == "__main__":
    unittest.main()
