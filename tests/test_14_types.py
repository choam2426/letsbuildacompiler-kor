import io
import unittest
from tests.wasm_util import run_wasm
from part14_types import Compiler


class TestCompileAndExecute(unittest.TestCase):
    def compile_to_wasm(self, src: str, show=False) -> str:
        output = io.StringIO()
        compiler = Compiler(src, output=output)
        compiler.toplevel()
        if show:
            print("--------- WASM CODE ---------")
            print(output.getvalue())
            print("-----------------------------")
        return output.getvalue()

    def compile_and_run(
        self,
        src: str,
        show=False,
    ) -> int:
        full_code = self.compile_to_wasm(src, show=show)
        return run_wasm(full_code)

    def test_global_with_type(self):
        result = self.compile_and_run(
            r"""
            var quad X=0
            var long Q=99

            program testprog
            begin
                X = X + 32
            end
            .
            """
        )
        self.assertEqual(result, 32)

        result = self.compile_and_run(
            r"""
            var quad X=9, Y=10;
            var quad Z=5;

            program testprog
            begin
                X = X + Y * Z
            end
            .
            """,
        )
        self.assertEqual(result, 59)

    def test_basic_long_conversion(self):
        result = self.compile_and_run(
            r"""
            var quad X=0;
            var long A=10;

            program testprog
            begin
                X = A
            end
            .
            """,
        )
        self.assertEqual(result, 10)

    def test_long_arithmetic(self):
        result = self.compile_and_run(
            r"""
            var long A=20, B=5, C=0;
            var quad X;

            program testprog
            begin
                C = A + B
                X = C
            end
            .
            """
        )
        self.assertEqual(result, 25)


if __name__ == "__main__":
    unittest.main()
