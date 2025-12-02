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

    def test_procedure_with_local_vars(self):
        result = self.compile_and_run(
            r"""
            var long X=0

            procedure aproc()
                var long y, z, t;
                y = 2
                z = 13
                t = 17
                X = X + y + z + t
            end

            program testprog
            begin
                aproc()
            end
            .
            """
        )
        self.assertEqual(result, 32)


if __name__ == "__main__":
    unittest.main()
