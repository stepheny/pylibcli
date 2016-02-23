import builtins
import unittest
import unittest.mock
import pylibcli
import sys
from pylibcli import getopt

class TestMissingGettext(unittest.TestCase):
    def setUp(self):
        self.mock = unittest.mock.Mock()
        if 'gettext' in sys.modules:
            del sys.modules['gettext']
        if 'pylibcli' in sys.modules:
            del sys.modules['pylibcli']
        if 'pylibcli.getopt' in sys.modules:
            del sys.modules['pylibcli.getopt']
        global __real_import__
        __real_import__ = builtins.__import__
        def trap_gettext(name, *args, **kwargs):
            if name == 'gettext':
                raise ImportError
            return __real_import__(name, *args, **kwargs)
        builtins.__import__ = trap_gettext

    def test_missing(self):
        from pylibcli import getopt
        self.assertTrue('gettext' not in sys.modules)
        self.assertEqual("SomeString", getopt._("SomeString"))

    def tearDown(self):
        builtins.__import__ = __real_import__


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


class TestOption(unittest.TestCase):
    def test_construct(self):
        with self.assertRaises(TypeError):
            getopt.Option()
        getopt.Option("test", getopt.no_argument, None, 't')


if __name__ == '__main__':
    unittest.main()
