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
            bar = 40
            X = 0
            if bar > 3 
                X = 99
            end
            """
        result = self.compile_and_run(code)
        self.assertEqual(result, 99)

    def test_nested_if(self):
        code = r"""
            foo = {fooval}
            X = 0
            if foo < 3
                X = 9
            else
                if foo = 5
                    X = 8
                else
                    X = 7
                end
            end"""
        result = self.compile_and_run(code.format(fooval=2))
        self.assertEqual(result, 9)

        result = self.compile_and_run(code.format(fooval=5))
        self.assertEqual(result, 8)

        result = self.compile_and_run(code.format(fooval=9))
        self.assertEqual(result, 7)

    def test_repeat_loop(self):
        result = self.compile_and_run(
            r"""
            Y = 3
            X = 0
            repeat
                X = X + 2
                Y = Y - 1
                until Y < 1
            end
        """
        )
        self.assertEqual(result, 6)

    def test_repeat_with_break(self):
        result = self.compile_and_run(
            r"""
            Y = 10
            X = 0
            repeat
                X = X + 3
                if X > 9
                    break
                end
                Y = Y - 1
                until Y < 1
            end
        """
        )
        self.assertEqual(result, 12)


if __name__ == "__main__":
    unittest.main()
