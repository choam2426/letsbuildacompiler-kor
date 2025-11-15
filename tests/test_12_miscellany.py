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


if __name__ == "__main__":
    unittest.main()
