import unittest
import pylibcli
from pylibcli import getopt

class TestFlags(unittest.TestCase):
    def setUp(self):
        self.flags = getopt.Flags()

    def test_flags(self):
        with self.assertRaises(AttributeError):
            self.flags.SomeString
        self.flags.SomeString = "SomeString"
        self.assertEqual(self.flags.SomeString, "SomeString")
    
    def test_flags_setter(self):
        self.flags._.SomeString("SomeString")
        self.assertEqual(self.flags.SomeString, "SomeString")

