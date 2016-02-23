import builtins
import unittest
import unittest.mock
import io
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


class TestGetopt(unittest.TestCase):
    def test_getopt_with_matched_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -a -b -c -d".split()
            gi = getopt.iter_getopt(argv, 'abcd')
            for i in [
                ('a', 1, '?', 2, None),
                ('b', 1, '?', 3, None),
                ('c', 1, '?', 4, None),
                ('d', 1, '?', 5, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_with_matched_option_combined(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -ab -cd".split()
            gi = getopt.iter_getopt(argv, 'abcd')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 2, None),
                ('c', 1, '?', 2, None),
                ('d', 1, '?', 3, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_with_invalid_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -a -b -c -d".split()
            gi = getopt.iter_getopt(argv, 'abd')
            for i in [
                ('a', 1, '?', 2, None),
                ('b', 1, '?', 3, None),
                ('?', 1, 'c', 4, None),
                ('d', 1, 'c', 5, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)

    def test_getopt_with_arguments(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -a -b arg0".split()
            gi = getopt.iter_getopt(argv, 'ab')
            for i in [
                ('a', 1, '?', 2, None),
                ('b', 1, '?', 3, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['arg0'])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_with_arguments_mixed(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt arg0 -a arg1 -b arg2".split()
            gi = getopt.iter_getopt(argv, 'ab')
            for i in [
                ('a', 1, '?', 3, None),
                ('b', 1, '?', 5, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['arg0', 'arg1', 'arg2'])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_with_option_missing_required_value(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abc".split()
            gi = getopt.iter_getopt(argv, 'abc:')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                ('?', 1, 'c', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)

    def test_getopt_with_option_missing_optional_value(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abc".split()
            gi = getopt.iter_getopt(argv, 'abc::')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                ('c', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() == 0)




if __name__ == '__main__': # pragma: no cover
    unittest.main()
