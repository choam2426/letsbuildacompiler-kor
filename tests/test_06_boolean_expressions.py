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
        result = self.compile_and_run("Y = 2  Z = 3  X = Y * Z")
        self.assertEqual(result, 6)

        result = self.compile_and_run("Y = 1  X = Y+8  X = X*9")
        self.assertEqual(result, 81)

    def test_basic_if(self):
        result = self.compile_and_run("Y = 5  X = 0  i Y > 3  X = 9 e")
        self.assertEqual(result, 9)

        result = self.compile_and_run("Y = 2  X = 0  i Y > 3  X = 9 e")
        self.assertEqual(result, 0)

    def test_if_else(self):
        result = self.compile_and_run("Y = 5  X = 0  i Y < 3  X = 9 l X = 7 e")
        self.assertEqual(result, 7)

        result = self.compile_and_run("Y = 2  X = 0  i Y < 3  X = 9 l X = 7 e")
        self.assertEqual(result, 9)

    def test_nested_if(self):
        code = r"""
            Y = {yval}
            X = 0
            i Y < 3
                X = 9
            l
                i Y = 5
                    X = 8
                l
                    X = 7
                e
            e"""
        result = self.compile_and_run(code.format(yval=2))
        self.assertEqual(result, 9)

        result = self.compile_and_run(code.format(yval=5))
        self.assertEqual(result, 8)

        result = self.compile_and_run(code.format(yval=9))
        self.assertEqual(result, 7)

    def test_while_loop(self):
        result = self.compile_and_run(r"""
            Y = 3
            X = 0
            w Y > 0
                X = X + 2
                Y = Y - 1
            e
        """)
        self.assertEqual(result, 6)

        # Loop not entered
        result = self.compile_and_run(r"""
            Y = 3
            X = 0
            w Y > 3
                X = X + 2
                Y = Y - 1
            e
        """)
        self.assertEqual(result, 0)

        # Loop with break that's triggered
        result = self.compile_and_run(
            r"""
            Y = 3
            X = 0
            w Y > 0
                i Y = 1
                    b
                e
                X = X + 2
                Y = Y - 1
            e
        """
        )
        self.assertEqual(result, 4)

    def test_loop_loop(self):
        result = self.compile_and_run(
            r"""
            Y = 3
            X = 0
            p
                i Y = 0
                    b
                e
                X = X + 2
                Y = Y - 1
            e
        """
        )
        self.assertEqual(result, 6)

    def test_repeat_loop(self):
        result = self.compile_and_run(
            r"""
            Y = 3
            X = 0
            r
                X = X + 2
                Y = Y - 1
                u Y < 1
            e
        """
        )
        self.assertEqual(result, 6)

    def test_do_loop(self):
        result = self.compile_and_run(
            r"""
            Y = 3
            X = 0
            d Y + 1
                X = X + 2
            e
        """
        )
        self.assertEqual(result, 8)

    def test_for_loop(self):
        result = self.compile_and_run(
            r"""
            X = 1
            f I = 0   6
                X = X * 2
            e
        """
        )
        self.assertEqual(result, 64)

        # Test with a computed upper limit
        result = self.compile_and_run(
            r"""
            X = 1
            Y = 1
            Z = 3
            f I = 0   Z+X
                Y = Y * 3
            e
            X = Y
        """
        )
        self.assertEqual(result, 81)

        # Test with a break
        result = self.compile_and_run(
            r"""
            X = 1
            f I = 0   9
                i X = 8
                    b
                e
                X = X * 2
            e
        """
        )
        self.assertEqual(result, 8)


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
