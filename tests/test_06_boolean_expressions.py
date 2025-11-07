import io
import unittest
from tests.wasm_util import run_wasm
from part06_boolean_expressions import Compiler


module_template = r"""
(module
  (func (export "main") (result i32)
    (local $X i32)
    (local $Y i32)
    (local $Z i32)
{instrs}
    ;; For testing, the function always returns the value of X.
    local.get $X
  )
)
""".lstrip()


class TestCompileAndExecute(unittest.TestCase):
    def compile_and_run(self, src: str) -> int:
        output = io.StringIO()
        compiler = Compiler(src, output=output)
        compiler.block()
        instrs = output.getvalue()

        full_code = module_template.format(instrs=instrs)
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
        result = self.compile_and_run("Y = 2  Z = 3  X = Y * Z")
        self.assertEqual(result, 6)

        result = self.compile_and_run("Y = 1  X = Y+8  X = X*9")
        self.assertEqual(result, 81)


class TestCompilerEmittedSource(unittest.TestCase):
    def split_emission(self, output):
        """Return compiler emission as a list of non-empty lines.

        Accepts either a string or a StringIO-like object with getvalue().
        """
        if hasattr(output, "getvalue"):
            text = output.getvalue()
        else:
            text = str(output)
        return [line.strip() for line in text.splitlines() if line.strip()]

    def test_basic_assignment(self):
        output = io.StringIO()
        compiler = Compiler("x = 3", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "i32.const 3",
                "local.set $X",
            ],
        )

    def test_boolean_expression_assignment(self):
        output = io.StringIO()
        compiler = Compiler("X = Y < 3", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "local.get $Y",
                "i32.const 3",
                "i32.lt_s",
                "local.set $X",
            ],
        )

    def test_longer_boolean_expression(self):
        output = io.StringIO()
        compiler = Compiler("X = (Y + 5 = 9) & (Z < 3)", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "local.get $Y",
                "i32.const 5",
                "i32.add",
                "i32.const 9",
                "i32.eq",
                "local.get $Z",
                "i32.const 3",
                "i32.lt_s",
                "i32.and",
                "local.set $X",
            ],
        )

    def test_unary_minus_plus(self):
        # In this part we've changed how unary signs are handled; test
        # these here.
        output = io.StringIO()
        compiler = Compiler("X = -Y", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "local.get $Y",
                "i32.const -1",
                "i32.mul",
                "local.set $X",
            ],
        )

        output = io.StringIO()
        compiler = Compiler("X = -2 - +Y", output=output)
        compiler.assignment()

        self.assertEqual(
            self.split_emission(output),
            [
                "i32.const -2",
                "local.get $Y",
                "i32.sub",
                "local.set $X",
            ],
        )


if __name__ == "__main__":
    unittest.main()
