import io
import unittest
from tests.wasm_util import run_wasm
from part07_lexical_scanning import Compiler


module_template = r"""
(module
  (func (export "main") (result i32)
    (local $X i32)
    (local $Y i32)
    (local $Z i32)
    (local $FOO i32)
    (local $BAR i32)
    (local $loopvar1 i32)
    (local $looplimit1 i32)
{instrs}
    ;; For testing, the function always returns the value of X.
    local.get $X
  )
)
""".lstrip()


class TestCompileAndExecute(unittest.TestCase):
    def compile_and_run(self, src: str, show=False) -> int:
        output = io.StringIO()
        compiler = Compiler(src, output=output)
        compiler.block()
        instrs = output.getvalue()

        full_code = module_template.format(instrs=instrs)
        if show:
            print("--------- WASM CODE ---------")
            print(full_code)
            print("-----------------------------")
        return run_wasm(full_code)

    def test_single_assignment(self):
        result = self.compile_and_run("x=4")
        self.assertEqual(result, 4)

        result = self.compile_and_run("x=5*(3+4)")
        self.assertEqual(result, 35)

    def test_boolean_expression(self):
        result = self.compile_and_run("X = 2 < 3")
        self.assertEqual(result, 1)

        result = self.compile_and_run("X = 5 = 2")
        self.assertEqual(result, 0)

        result = self.compile_and_run("X = 4 > 7")
        self.assertEqual(result, 0)

    def test_multiple_assignments(self):
        result = self.compile_and_run(r"""
            foo = 2
            Z = 3
            X = foo * Z""")
        self.assertEqual(result, 6)

    def test_basic_if(self):
        code = r"""
            bar = 4
            X = 0
            if bar > 3 
                X = 9
            end
            """
        result = self.compile_and_run(code)
        self.assertEqual(result, 9)


if __name__ == "__main__":
    unittest.main()
