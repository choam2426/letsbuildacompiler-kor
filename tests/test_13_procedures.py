import io
import unittest
from tests.wasm_util import run_wasm
from part13_procedures import Compiler


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

    def test_comments(self):
        result = self.compile_and_run(
            """
        var x=8,y,z { a comment }
        program foo
        begin
            y = x = 8 {another comment}
            z = x {embedded comment} < 5
            y = y & !z
            x = y + { 9 + this is a comment doesn't count } 0
        end.
        """
        )
        self.assertEqual(result, 1)

        result = self.compile_and_run(
            """
        var x=8,y=3,z=2 { nested { comments } are ok }
        program foo
        begin
            x = (y + 5 = 8) & ({ nested { comments } are ok } z < 3)
        end.
        """
        )
        self.assertEqual(result, 1)

    def test_semicolons(self):
        result = self.compile_and_run(
            r"""
        var x=0;
        var y=10

        program foo
        begin
            x = x + 5;
            y = y - 2
            x = x + y;
        end.
        """
        )
        self.assertEqual(result, 13)

    def test_if_else(self):
        result = self.compile_and_run(
            r"""
        var x=0,y=10
        program foo
        begin
            if x < 5
                x = 20 ;
            else
                x = 30
            end
        end.
        """
        )
        self.assertEqual(result, 20)

        result = self.compile_and_run(
            r"""
        var x=0,y=10
        program foo
        begin
            if x > 5
                x = 20
            else
                x = 30 ;
            end
        end.
        """
        )
        self.assertEqual(result, 30)

    def test_while_loop(self):
        result = self.compile_and_run(
            r"""
        var x=0,y=5
        program somename
        begin
            while y > 0
                x = x + 2 ;
                y = y - 1
            end
        end.
        """
        )
        self.assertEqual(result, 10)

        # Same but with an early break
        result = self.compile_and_run(
            r"""
        var x=0,y=5
        program othername
        begin
            while y > 0
                x = x + 2
                if x = 6
                    break
                end
                y = y - 1
            end
        end.
        """
        )
        self.assertEqual(result, 6)

    def test_procedure_basic(self):
        result = self.compile_and_run(
            r"""
        var X=0

        procedure add5()
            X = X + 5
        end

        program testprog
        begin
            add5()
            add5()
            add5()
        end
        .
        """
        )
        self.assertEqual(result, 15)

    def test_procedure_calls_procedure(self):
        result = self.compile_and_run(
            r"""
        var X=0

        procedure add5()
            X = X + 5
        end

        procedure add10()
            add5()
            add5()
        end

        program testprog
        begin
            add10()
            add10()
            add10()
        end
        .
        """
        )
        self.assertEqual(result, 30)

    def test_procedure_params(self):
        result = self.compile_and_run(
            r"""
        var X=0
        var y=0

        procedure addtox(addend)
            X = addend + X
        end

        program testprog
        begin
            addtox(6)
            y = 10
            addtox(y*2)
            addtox(y+30)
        end
        .
        """
        )
        self.assertEqual(result, 66)

    def test_procedure_not_enough_params(self):
        with self.assertRaisesRegex(Exception, "expects 1 parameters, got 0"):
            self.compile_and_run(
                r"""
            var X=0

            procedure addtox(addend)
                X = addend + X
            end

            program testprog
            begin
                addtox()
            end
            .
            """
            )

    def test_procedure_too_many_params(self):
        with self.assertRaisesRegex(Exception, "expects 1 parameters, got 2"):
            self.compile_and_run(
                r"""
            var X=0

            procedure addtox(addend)
                X = addend + X
            end

            program testprog
            begin
                addtox(5, 10)
            end
            .
            """
            )

    def test_procedure_with_local_vars(self):
        result = self.compile_and_run(
            r"""
            var X=0

            procedure aproc()
                var y, z, t;
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

    def test_procedure_local_shadows_global(self):
        result = self.compile_and_run(
            r"""
            var X=0
            var y=9

            procedure aproc()
                var y, z, t;
                y = 2
                z = 13
                t = 17
                X = X + y + z + t
            end

            program testprog
            begin
                aproc()
                x = x * y  { uses global y=9 }
            end
            .
            """
        )
        self.assertEqual(result, 288)

    def test_procedure_with_locals_and_loop(self):
        result = self.compile_and_run(
            r"""
            var X=0

            { sum from 0 to n-1 inclusive, and add to X }
            procedure addseq(n)
                var i, sum  { 0 initialized }
                while i < n
                    sum = sum + i
                    i = i + 1
                end
                X = X + sum
            end

            program testprog
            begin
                addseq(10)
                addseq(5)
            end
            .
            """
        )
        self.assertEqual(result, 45 + 10)

    def test_procedure_with_locals_and_loop_and_ref_result(self):
        result = self.compile_and_run(
            r"""
            var X=0

            { sum from 0 to n-1 inclusive, and add to result }
            procedure addseq(n, ref result)
                var i, sum  { 0 initialized }
                while i < n
                    sum = sum + i
                    i = i + 1
                end
                result = result + sum
            end

            program testprog
            begin
                addseq(11, X)
            end
            .
            """
        )
        self.assertEqual(result, 55)

    def test_procedure_var_duplicates_param(self):
        with self.assertRaisesRegex(Exception, "Duplicate"):
            self.compile_and_run(
                r"""
                var X=0

                procedure aproc(y, z)
                    var y, t;
                    y = 2
                    X = X + y
                end

                program testprog
                begin
                    aproc(5,10)
                end
            .
            """
            )

    def test_procedure_byref(self):
        result = self.compile_and_run(
            r"""
            var X=4
            var Y=9

            procedure addtox(ref addend)
                X = X + addend
            end

            program testprog
            begin
                addtox(Y)
            end
            .
            """
        )
        self.assertEqual(result, 13)

        # one by-value, one by-ref
        result = self.compile_and_run(
            r"""
            var X=4
            var Y=9

            procedure addtox(addend1, ref addend2)
                X = X + addend1 + addend2
            end

            program testprog
            begin
                addtox(4+5, Y)
            end
            .
            """
        )
        self.assertEqual(result, 22)

        # two by-ref
        result = self.compile_and_run(
            r"""
            var X=4
            var Y=9, Z=14;

            procedure addtox(ref addend1, ref addend2)
                X = X + addend1 + addend2
            end

            program testprog
            begin
                addtox(Y, Z)
            end
            .
            """
        )
        self.assertEqual(result, 27)

    def test_procedure_byref_modifies_caller(self):
        result = self.compile_and_run(
            r"""
            var X=4
            var Y=9

            procedure addandmodify(ref addend)
                X = X + addend
                addend = addend + 5
            end

            program testprog
            begin
                addandmodify(Y)
                addandmodify(Y)
            end
            .
            """
        )
        self.assertEqual(result, 4 + 9 + 14)

    def test_procedure_divmod(self):
        result = self.compile_and_run(
            r"""
            var X=0
            var Y=0
            var Q=0
            var R=0

            procedure divmod(dividend, divisor, ref quotient, ref remainder)
                quotient = dividend / divisor
                remainder = dividend - (quotient * divisor)
            end

            program testprog
            begin
                X = 99
                Y = 23
                divmod(X, Y, Q, R)   { quot: 4, rem: 7 }
                X = 100*Q + R
            end
            .
            """
        )
        self.assertEqual(result, 407)

    def test_procedure_calls_procedure_with_ref(self):
        result = self.compile_and_run(
            r"""
            var X=0
            var Y=6

            procedure add(ref value, addend)
                value = value + addend
            end

            procedure multiply(ref value, factor)
                value = value * factor
            end

            procedure process(a, f, ref value)
                add(value, a)
                multiply(value, f)
            end

            program testprog
            begin
                process(4, 2, Y)      { Y = (6 + 4) * 2 = 20 }
                X = Y * Y
            end
            .
            """
        )
        self.assertEqual(result, 400)


if __name__ == "__main__":
    unittest.main()
