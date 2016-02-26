import io
import os
import sys
import unittest
import unittest.mock
from pylibcli import default, command, error, run
import pylibcli.opttools as opttools

class TestException(Exception):
    pass

class TestException32(Exception):
    pass

class TestExceptionUnexpected(Exception):
    pass

class TestCommandHandler(unittest.TestCase):
    def setUp(self):
        self.mock = unittest.mock.MagicMock()

    def test_commandhandler_construct(self):
        def func(*args, aflag=None, bflag=None, cflag=None):
            self.mock(*args, aflag=aflag, bflag=bflag, cflag=cflag)
        opttools.CommandHandler(func)(['test', '--aflag', '--bflag', '--cflag'])
        self.mock.assert_called_once_with(aflag='None', bflag='None', cflag='None')

    def test_commandhandler_construct_hint(self):
        def func(*args, aflag=None, bflag=None, cflag=None):
            self.mock(*args, aflag=aflag, bflag=bflag, cflag=cflag)
        opttools.CommandHandler(func, aflag='_a', bflag='_b', cflag='_c::=-')\
            (['test', '-a', '-b', '-c'])
        self.mock.assert_called_once_with(aflag='', bflag='', cflag='-')

    def test_commandhandler_construct_guess(self):
        def func(*, i=0, s='', b=False, l=[]):
            self.mock(i=i, s=s, b=b, l=l)
        opttools.CommandHandler(func)(['test'])
        self.mock.assert_called_once_with(i=0, s='', b=False, l=[])

    def test_commandhandler_construct_guess_parse(self):
        def func(*, i=0, s='', b=False, l=[]):
            self.mock(i=i, s=s, b=b, l=l)
        opttools.CommandHandler(func)\
            (['test', '--i', '16', '--s', 's', '--b', 'N', '--l', 'x,y,z'])
        self.mock.assert_called_once_with(i=16, s='s', b=False, l=['x', 'y', 'z'])

    def test_commandhandler_construct_guess_parse_dict(self):
        def func(*, di={}):
            self.mock(di)
        opttools.CommandHandler(func)(['test', '--d', 'a=1,b=2,c'])
        self.mock.assert_called_once_with([('a', '1'), ('b', '2'), ('c', None)])

    def test_commandhandler_construct_mono_positional_args(self):
        def func(input):
            self.mock(input)
        ch = opttools.CommandHandler(func, input='i::str=-')
        ch(['test', '--input=foobar'])
        self.mock.assert_called_once_with('foobar')
        with self.assertRaises(opttools.OptionError):
            ch(['test'])

    def test_commandhandler_construct_many_positional_args(self):
        with self.assertRaises(opttools.StructureError):
            def func(a, b):
                self.mock(a, b)
            opttools.CommandHandler(func)(['test', 'a', 'b'])

    def test_commandhandler_construct_required_option(self):
        def func(a, *, b):
            self.mock(a, b)
        opttools.CommandHandler(func, a='_a:', b='_b:str')\
            (['test', '-a', 'vala', '-bvalb'])

    def test_commandhandler_construct_hint_duplicate(self):
        with self.assertRaises(opttools.StructureError):
            def func(*, a, b):
                self.mock(a, b)
            opttools.CommandHandler(func, a='d', b='d')(['test', 'a', 'b'])

    def test_commandhandler_construct_hint_optional_without_default(self):
        with self.assertRaises(opttools.StructureError):
            def func(*, a, b):
                self.mock(a, b)
            opttools.CommandHandler(func, a='::', b='::=')(['test', 'a', 'b'])


class TestOptionHandler(unittest.TestCase):
    def setUp(self):
        self.opthdr = opttools.OptionHandler()
        self.opthdr.error(TestException)
        self.opthdr.error(TestException32, errno=32)
        self.mock = unittest.mock.MagicMock()

    def test_optionhandler_run(self):
        @self.opthdr.command
        @self.opthdr.default
        def func(*args):
            self.mock(*args)
        self.opthdr.run(['test', 'arg0', 'arg1', 'arg2'])
        self.mock.assert_called_once_with('arg0', 'arg1', 'arg2')

    def test_optionhandler_run_sys_argv(self):
        @self.opthdr.command
        @self.opthdr.default
        def func(*args):
            self.mock(*args)
        with unittest.mock.patch('sys.argv', ['test', 'arg0', 'arg1', 'arg2']):
            self.opthdr.run()
            self.mock.assert_called_once_with('arg0', 'arg1', 'arg2')

    def test_optionhandler_run_withoud_stack_frame(self):
        with unittest.mock.patch('inspect.currentframe', lambda: None):
            @self.opthdr.command
            @self.opthdr.default
            def func(*args):
                self.mock(*args)
            self.opthdr.run(['test', 'arg0', 'arg1', 'arg2'])
            self.mock.assert_called_once_with('arg0', 'arg1', 'arg2')

    def test_optionhandler_default_duplicated(self):
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.default
            @self.opthdr.default
            def func(*args):
                self.mock(*args)

    def test_optionhandler_command_duplicated(self):
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.command
            @self.opthdr.command
            def func(*args):
                self.mock(*args)

if __name__ == '__main__': # pragma: no cover
    unittest.main()





















