import io
import unittest
from tests.wasm_util import run_wasm
from part13_procedures import Compiler


class TestCompileAndExecute(unittest.TestCase):
    def _compile_to_wasm(self, src: str, show=False) -> str:
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
        full_code = self._compile_to_wasm(src, show=show)
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

        procedure add5
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

        { Also show that procedures can be defined after use }
        program testprog
        begin
            add10()
            add10()
            add10()
        end

        procedure add5
            X = X + 5
        end

        procedure add10
            add5()
            add5()
        end
        .
        """
        )
        self.assertEqual(result, 30)


if __name__ == "__main__":
    unittest.main()
