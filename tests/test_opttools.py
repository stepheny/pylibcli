import io
import os
import sys
import math
import unittest
import unittest.mock
from libcli import default, command, error, run
import libcli.opttools as opttools

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

    # DEPRECATED since 0.3
    #def test_commandhandler_construct_many_positional_args(self):
        #with self.assertRaises(opttools.StructureError):
            #def func(a, b):
                #pass # pragma no cover
            #opttools.CommandHandler(func)(['test', 'a', 'b'])

    def test_commandhandler_construct_mix_positional_and_variable_args(self):
        with self.assertRaises(opttools.StructureError):
            def func(a, *b):
                pass # pragma no cover
            opttools.CommandHandler(func)(['test'])

    def test_commandhandler_construct_required_option(self):
        def func(a, *, b):
            self.mock(a, b)
        opttools.CommandHandler(func, a='_a:', b='_b:str')\
            (['test', '-a', 'vala', '-bvalb'])

    def test_commandhandler_construct_required_option_with_default(self):
        with self.assertRaises(opttools.StructureError):
            def func(a, *, b):
                pass # pragma no cover
            opttools.CommandHandler(func, a='_a:=a', b='_b:str')\
                (['test', '-a', 'vala', '-bvalb'])

    def test_commandhandler_construct_hint_duplicate(self):
        with self.assertRaises(opttools.StructureError):
            def func(*, a, b):
                pass # pragma no cover
            opttools.CommandHandler(func, a='d', b='d')(['test', 'a', 'b'])

    def test_commandhandler_construct_hint_optional_without_default(self):
        with self.assertRaises(opttools.StructureError):
            def func(*, a, b):
                pass # pragma no cover
            opttools.CommandHandler(func, a='::', b='::=')(['test', 'a', 'b'])

    def test_commandhandler_parse_integers(self):
        def func(*, h, d, o, b):
            self.mock(h=h, d=d, o=o, b=b)
        opttools.CommandHandler(func, h='h:hex', d='d:dec', o='o:oct', b='b:bin')\
            (['test', '-h', '10', '-d', '10', '-o', '10', '-b', '10'])
        self.mock.assert_called_once_with(h=16, d=10, o=8, b=2)

    def test_commandhandler_parse_integers_smart(self):
        def func(*, h, d, o, b):
            self.mock(h=h, d=d, o=o, b=b)
        opttools.CommandHandler(func, h='h:int', d='d:int', o='o:int', b='b:int')\
            (['test', '-h', '0X10', '-d', '012', '-o', '0O10', '-b', '0B10'])
        self.mock.assert_called_once_with(h=16, d=10, o=8, b=2)

    def test_commandhandler_parse_invalid_option(self):
        with self.assertRaises(opttools.OptionError):
            def func(*, s):
                pass # pragma no cover
            opttools.CommandHandler(func, s=':str')(['test', '-t'])

    def test_commandhandler_parse_missing_option(self):
        with self.assertRaises(opttools.OptionError):
            def func(*, s):
                pass # pragma no cover
            opttools.CommandHandler(func, s=':str')(['test'])

    # DEPRECATED since 0.3
    #def test_commandhandler_parse_duplicated_option(self):
        #with self.assertRaises(opttools.OptionError):
            #def func(s, *args):
                #pass # pragma no cover
            #opttools.CommandHandler(func, s='s:str')\
                #(['test', '-s', 'once', 'twice'])


class TestCommandHandlerDebug(TestCommandHandler):
    def setUp(self):
        super().setUp()
        opttools.DEBUG = True
        self.stderr = io.StringIO()
        self._stderr = sys.stderr
        sys.stderr = self.stderr

    def tearDown(self):
        super().tearDown()
        opttools.DEBUG = False
        sys.stderr = self._stderr


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
                pass # pragma no cover

    def test_optionhandler_command_duplicated(self):
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.command
            @self.opthdr.command
            def func(*args):
                pass # pragma no cover

    def test_optionhandler_default_duplicated_withoud_stack_frame(self):
      with unittest.mock.patch('inspect.currentframe', lambda: None):
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.default
            @self.opthdr.default
            def func(*args):
                pass # pragma no cover

    def test_optionhandler_command_duplicated_withoud_stack_frame(self):
      with unittest.mock.patch('inspect.currentframe', lambda: None):
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.command
            @self.opthdr.command
            def func(*args):
                pass # pragma no cover

    def test_optionhandler_with_invalid_defaut(self):
        with self.assertRaises(opttools.StructureError):
            self.opthdr.default(object())

    def test_optionhandler_with_invalid_command(self):
        with self.assertRaises(opttools.StructureError):
            self.opthdr.command(object())

    def test_optionhandler_except_default(self):
        with self.assertRaises(SystemExit) as cm:
            @self.opthdr.default
            def func(*args):
                raise TestException
            self.opthdr.run(['test'])
        self.assertEqual(cm.exception.code, 127) # opttools default

    def test_optionhandler_except_custom(self):
        with self.assertRaises(SystemExit) as cm:
            @self.opthdr.default
            def func(*args):
                raise TestException32
            self.opthdr.run(['test'])
        self.assertEqual(cm.exception.code, 32)

    def test_optionhandler_except_unexpected(self):
        with self.assertRaises(TestExceptionUnexpected):
            @self.opthdr.default
            def func(*args):
                raise TestExceptionUnexpected
            self.opthdr.run(['test'])

    def test_optionhandler_unexpected_option(self):
      with unittest.mock.patch('sys.stderr', new=io.StringIO()) as stderr:
        with self.assertRaises(SystemExit) as cm:
            @self.opthdr.default
            def func():
                pass
            self.opthdr.run(['test', 'unexpected'])
        self.assertEqual(cm.exception.code, 127) # opttools default
        self.assertTrue(stderr.tell() > 0)

    def test_optionhandler_class_chain(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        @self.opthdr.default(n='_n:int')
        class Counter():
            def __init__(self, *, n=0):
                self._value = 0
            @self.opthdr.command(n='_n:int')
            def add(self, *, n=1):
                self._value += n
                return self
            @self.opthdr.command
            def value(self):
                print(self._value)
                return self
        self.opthdr.run(['test', 'add', '-n20', 'add', 'value'])
        self.assertEqual(stdout.getvalue(), '21\n')

    def test_optionhandler_without_default(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        @self.opthdr.command
        def func():
            print('Hello world!')
        self.opthdr.run(['test', 'func'])
        self.assertEqual(stdout.getvalue(), 'Hello world!\n')

    def test_optionhandler_with_invalid_exception(self):
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.error()
            class NotAnException(BaseException):
                pass

    def test_optionhandler_docstring(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        @self.opthdr.command
        def sin(deg=0):
            """
            :param float deg: Print sine of deg degrees.
            """
            print('{:0.3f}'.format(math.sin(math.radians(deg))))
        self.opthdr.run(['test', 'sin', '90'])
        self.assertEqual(stdout.getvalue(), '1.000\n')

    def test_optionhandler_docstring_alt(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        @self.opthdr.command
        def sin(deg=0):
            """
            :param deg: Print sine of deg degrees.
            :type deg: int or float.
            """
            print('{:0.3f}'.format(math.sin(math.radians(deg))))
        self.opthdr.run(['test', 'sin', '90'])
        self.assertEqual(stdout.getvalue(), '1.000\n')

    def test_optionhandler_docstring_with_hint(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        @self.opthdr.command(deg='_:int,float')
        def sin(deg=0):
            """
            :param float deg: Print sine of deg degrees.
            """
            print('{:0.3f}'.format(math.sin(math.radians(deg))))
        self.opthdr.run(['test', 'sin', '90'])
        self.assertEqual(stdout.getvalue(), '1.000\n')

    def test_optionhandler_docstring_duplicated(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.command
            def sin(deg=0):
                """
                :param float deg: Print sine of deg degrees.
                :param float deg: Print sine of deg degrees.
                """
                pass # pragma no cover
            self.opthdr.run(['test', 'sin', '90'])

    def test_optionhandler_docstring_alt_duplicated(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.command
            def sin(deg=0):
                """
                :param float deg: Print sine of deg degrees.
                :param deg: Print sine of deg degrees.
                """
                pass # pragma no cover
            self.opthdr.run(['test', 'sin', '90'])

    def test_optionhandler_docstring_alt_type_duplicated(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.command
            def sin(deg=0):
                """
                :param float deg: Print sine of deg degrees.
                :type deg: int or float.
                """
                pass # pragma no cover
            self.opthdr.run(['test', 'sin', '90'])

    def test_optionhandler_docstring_with_hint_duplicated(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        with self.assertRaises(opttools.StructureError):
            @self.opthdr.command(deg='_:int,float')
            def sin(deg=0):
                """
                :param float deg: Print sine of deg degrees.
                :param deg: Print sine of deg degrees.
                """
                pass # pragma no cover
            self.opthdr.run(['test', 'sin', '90'])

    def test_optionhandler_docstring_with_unknown_type(self):
      with unittest.mock.patch('sys.stdout', new=io.StringIO()) as stdout:
        with self.assertRaises(opttools.OptionError):
            @self.opthdr.default
            def func(*,a=None, b=None, c=None):
                """
                :type a: flag.
                :type b: none.
                :type c: flag or none or foobar.
                """
                pass # pragma no cover
            self.opthdr.run(['test', '--a', '--b', '--c=foobar'], debug=True)


class TestOptionHandlerDebug(TestOptionHandler):
    def setUp(self):
        super().setUp()
        opttools.DEBUG = True
        self.stderr = io.StringIO()
        self._stderr = sys.stderr
        sys.stderr = self.stderr

    def tearDown(self):
        super().tearDown()
        opttools.DEBUG = False
        sys.stderr = self._stderr


if __name__ == '__main__': # pragma: no cover
    unittest.main()





















