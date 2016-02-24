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

    def test_gettext_missing(self):
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
    def test_option_construct(self):
        with self.assertRaises(TypeError):
            getopt.Option()
        with self.assertRaises(getopt.GetoptError):
            getopt.Option(0, getopt.no_argument, None, 't')
        with self.assertRaises(getopt.GetoptError):
            getopt.Option("test", 0, None, 't')
        with self.assertRaises(getopt.GetoptError):
            getopt.Option("test", getopt.no_argument, True, 't')
        with self.assertRaises(getopt.GetoptError):
            getopt.Option("test", getopt.no_argument, None, None)
        repr(getopt.Option("test", getopt.no_argument, None, 't'))


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

    def test_getopt_with_invalid_option_posixly_correct(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
          with unittest.mock.patch('os.environ', {'POSIXLY_CORRECT': ''}):
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

    def test_getopt_with_arguments_mixed_posixly_correct(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
          with unittest.mock.patch('os.environ', {'POSIXLY_CORRECT': ''}):
            argv = "testopt -a arg0 -b arg1".split()
            gi = getopt.iter_getopt(argv, 'ab')
            for i in [
                ('a', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['arg0', '-b', 'arg1'])
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

    def test_getopt_with_option_missing_required_value_quote(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abc".split()
            gi = getopt.iter_getopt(argv, ':abc:')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                (':', 1, 'c', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)

    def test_getopt_with_option_with_required_value(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abcde".split()
            gi = getopt.iter_getopt(argv, 'abc:')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                ('c', 1, '?', 2, 'de')]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_with_option_with_required_value_discrete(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abc -de".split()
            gi = getopt.iter_getopt(argv, 'abc:')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                ('c', 1, '?', 3, '-de')]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() == 0)

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

    def test_getopt_with_option_with_optional_value(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abcde".split()
            gi = getopt.iter_getopt(argv, 'abc::')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                ('c', 1, '?', 2, 'de')]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_with_two_hyphen(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abc -- -- -a -b -c".split()
            gi = getopt.iter_getopt(argv, 'abc::')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                ('c', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['--', '-a', '-b', '-c'])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_with_two_hyphen_alt(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -abc de -- -- -a -b -c".split()
            gi = getopt.iter_getopt(argv, 'abc::')
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 1, None),
                ('c', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['de', '--', '-a', '-b', '-c'])
            self.assertTrue(stderr.tell() == 0)


class TestGetoptLong(unittest.TestCase):
    def setUp(self):
        O = getopt.Option
        no_argument = getopt.no_argument
        required_argument = getopt.required_argument
        optional_argument = getopt.optional_argument

        self.callback = unittest.mock.MagicMock()
        self.callback_alt = unittest.mock.MagicMock()
        self.longopts = [
            O("noarg",        no_argument,       self.callback,     1  ),
            O("required",     required_argument, None,              'c'),
            O("optional",     optional_argument, None,              'd'),
            O("optional-alt", optional_argument, self.callback_alt, 2),]

    def test_getopt_long_with_matched_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -a -b --noarg --required=req --optional".split()
            gi = getopt.iter_getopt_long(argv, 'ab', self.longopts)
            for i in [
                ('a', 1, '?', 2, None),
                ('b', 1, '?', 3, None),
                (0,   1, '?', 4, None),
                ('c', 1, '?', 5, 'req'),
                ('d', 1, '?', 6, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() == 0)
            self.callback.assert_called_once_with(1)

    def test_getopt_long_with_no_short_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt arg0 --noarg --required=req --optional".split()
            gi = getopt.iter_getopt_long(argv, '', self.longopts)
            for i in [
                (0,   1, '?', 3, None),
                ('c', 1, '?', 4, 'req'),
                ('d', 1, '?', 5, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['arg0'])
            self.assertTrue(stderr.tell() == 0)
            self.callback.assert_called_once_with(1)

    def test_getopt_long_with_partial_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -a -b --no --required=req --optional".split()
            gi = getopt.iter_getopt_long(argv, 'ab', self.longopts)
            for i in [
                ('a', 1, '?', 2, None),
                ('b', 1, '?', 3, None),
                (0,   1, '?', 4, None),
                ('c', 1, '?', 5, 'req'),
                ('d', 1, '?', 6, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_long_with_ambiguous_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -a -b --noarg --required=req --opti".split()
            gi = getopt.iter_getopt_long(argv, 'ab', self.longopts)
            for i in [
                ('a', 1, '?', 2, None),
                ('b', 1, '?', 3, None),
                (0,   1, '?', 4, None),
                ('c', 1, '?', 5, 'req'),
                ('?', 1, '?', 6, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)

    def test_getopt_long_with_invalid_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt --help".split()
            gi = getopt.iter_getopt_long(argv, 'ab', self.longopts)
            for i in [
                ('?', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)

    def test_getopt_long_with_arguments_mixed(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt arg0 --req req".split()
            gi = getopt.iter_getopt_long(argv, 'ab', self.longopts)
            for i in [
                ('c', 1, '?', 4, 'req')]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['arg0'])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_long_with_arguments_mixed_require_order(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -ab arg0 --req req".split()
            gi = getopt.iter_getopt_long(argv, '+ab', self.longopts)
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], ['arg0', '--req', 'req'])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_long_with_arguments_mixed_return_order(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -ab arg0 --req req".split()
            gi = getopt.iter_getopt_long(argv, '-ab', self.longopts)
            for i in [
                ('a', 1, '?', 1, None),
                ('b', 1, '?', 2, None),
                (1,   1, '?', 3, 'arg0'),
                ('c', 1, '?', 5, 'req')]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() == 0)

    def test_getopt_long_with_no_argument_provided(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt --noarg=arg".split()
            gi = getopt.iter_getopt_long(argv, 'ab', self.longopts)
            for i in [
                ('?', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)

    def test_getopt_long_with_missing_required_value(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt --required".split()
            gi = getopt.iter_getopt_long(argv, 'ab', self.longopts)
            for i in [
                ('?', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)


class TestGetoptLongOnly(unittest.TestCase):
    def setUp(self):
        O = getopt.Option
        no_argument = getopt.no_argument
        required_argument = getopt.required_argument
        optional_argument = getopt.optional_argument

        self.callback = unittest.mock.MagicMock()
        self.callback_alt = unittest.mock.MagicMock()
        self.longopts = [
            O("noarg",        no_argument,       self.callback,     1  ),
            O("required",     required_argument, None,              'c'),
            O("optional",     optional_argument, None,              'd'),
            O("optional-alt", optional_argument, self.callback_alt, 2),]

    def test_getopt_long_only_with_matched_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -a -b -noarg -required=req -optional".split()
            gi = getopt.iter_getopt_long_only(argv, 'ab', self.longopts)
            for i in [
                ('a', 1, '?', 2, None),
                ('b', 1, '?', 3, None),
                (0,   1, '?', 4, None),
                ('c', 1, '?', 5, 'req'),
                ('d', 1, '?', 6, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() == 0)
            self.callback.assert_called_once_with(1)

    def test_getopt_long_only_with_invalid_option(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -help".split()
            gi = getopt.iter_getopt_long_only(argv, 'ab', self.longopts)
            for i in [
                ('?', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)

    def test_getopt_long_only_with_no_argument_provided(self):
        with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
            argv = "testopt -noarg=arg".split()
            gi = getopt.iter_getopt_long_only(argv, 'ab', self.longopts)
            for i in [
                ('?', 1, '?', 2, None)]:
                self.assertEqual(i , (gi.__next__(), \
                    gi.opterr, gi.optopt, gi.optind, gi.optarg))
            self.assertEqual(list(gi), [])
            self.assertEqual(gi.argv[gi.optind:], [])
            self.assertTrue(stderr.tell() > 0)


if __name__ == '__main__': # pragma: no cover
    unittest.main()
