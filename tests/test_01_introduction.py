import unittest
from part01_introduction import Compiler


class TestCompiler(unittest.TestCase):
    def test_get_name_valid(self):
        compiler = Compiler("A")
        name = compiler.get_name()
        self.assertEqual(name, "A")

    def test_get_name_invalid(self):
        compiler = Compiler("1")
        with self.assertRaisesRegex(Exception, "Name expected"):
            compiler.get_name()

    def test_get_num_valid(self):
        compiler = Compiler("5")
        num = compiler.get_num()
        self.assertEqual(num, "5")

    def test_get_num_invalid(self):
        compiler = Compiler("A")
        with self.assertRaisesRegex(Exception, "Integer"):
            compiler.get_num()

    def test_match(self):
        compiler = Compiler("A")
        compiler.match("A")
        self.assertEqual(compiler.look, "")

        # invalid matches
        compiler = Compiler("B")
        with self.assertRaisesRegex(Exception, "'A' expected"):
            compiler.match("A")

    def test_emit(self):
        import io

        output = io.StringIO()
        compiler = Compiler("", output=output)
        compiler.emit("MOV A, B")
        self.assertEqual(output.getvalue(), "    MOV A, B")

    def test_emit_ln(self):
        import io

        output = io.StringIO()
        compiler = Compiler("", output=output)
        compiler.emit_ln("MOV A, B")
        self.assertEqual(output.getvalue(), "    MOV A, B\n")


if __name__ == "__main__":
    unittest.main()
