import unittest
from part01_introduction import Compiler


class TestCompiler(unittest.TestCase):
    def test_get_name_valid(self):
        compiler = Compiler("A")
        name = compiler.get_name()
        self.assertEqual(name, "A")

    def test_get_name_invalid(self):
        compiler = Compiler("1")
        with self.assertRaises(Exception) as e:
            compiler.get_name()
        self.assertEqual(str(e.exception), "Error: Name expected")

    def test_get_num_valid(self):
        compiler = Compiler("5")
        num = compiler.get_num()
        self.assertEqual(num, "5")

    def test_get_num_invalid(self):
        compiler = Compiler("A")
        with self.assertRaises(Exception) as e:
            compiler.get_num()
        self.assertEqual(str(e.exception), "Error: Integer expected")


if __name__ == "__main__":
    unittest.main()
