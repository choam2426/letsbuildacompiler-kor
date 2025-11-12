import io
import unittest
from tests.wasm_util import run_wasm
from part10_introducing_tiny import Compiler


class TestCompileAndExecute(unittest.TestCase):
    def compile_and_run(self, src: str, show=False) -> int:
        output = io.StringIO()
        compiler = Compiler(src, output=output)
        compiler.block()
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

    def test_program(self):
        output = io.StringIO()
        compiler = Compiler("pvx,y=5bx=y+5e.", output=output)
        compiler.prog()

        print(output.getvalue())
        # print(self.split_emission(output))
        # self.assertEqual(
        #     self.split_emission(output),
        #     ["; Module X", "(module", ")"],
        # )


if __name__ == "__main__":
    unittest.main()
