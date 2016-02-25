import io
import os
import sys
import unittest
import unittest.mock
from pylibcli import default, command, error, run
import pylibcli.opttools as opttools

@error
class TestException(Exception):
    pass

@error(errno=32)
class TestException32(Exception):
    pass

class TestExceptionUnexpected(Exception):
    pass

class TestCommandHandler(unittest.TestCase):
    def setUp(self):
        self.mock = unittest.mock.MagicMock()
        def test_func(*args, aflag=None, bflag=None, cflag=None):
            self.mock(*args, aflag=aflag, bflag=bflag, cflag=cflag)
        self.func = test_func
        def test_func_p(*, i=0, s='', b=False, l=[]):
            self.mock(i=i, s=s, b=b, l=l)
        self.func_p = test_func_p
        def test_func_d(*, di={}):
            self.mock(di)
        self.func_d = test_func_d

    def test_commandhandler_construct(self):
        ch = opttools.CommandHandler(self.func)
        ch(['test', '--aflag', '--bflag', '--cflag'])
        self.mock.assert_called_once_with(aflag='None', bflag='None', cflag='None')

    def test_commandhandler_construct_hint(self):
        ch = opttools.CommandHandler(self.func, aflag='_a', bflag='_b', cflag='_c')
        ch(['test', '-a', '-b', '-c'])
        self.mock.assert_called_once_with(aflag='', bflag='', cflag='')

    def test_commandhandler_construct_guess(self):
        ch = opttools.CommandHandler(self.func_p)
        ch(['test'])
        self.mock.assert_called_once_with(i=0, s='', b=False, l=[])

    def test_commandhandler_construct_guess_parse(self):
        ch = opttools.CommandHandler(self.func_p)
        ch(['test', '--i', '16', '--s', 's', '--b', 'N', '--l', 'x,y,z'])
        self.mock.assert_called_once_with(i=16, s='s', b=False, l=['x', 'y', 'z'])

    def test_commandhandler_construct_guess_parse_dict(self):
        ch = opttools.CommandHandler(self.func_d)
        ch(['test', '--d', 'a=1,b=2,c'])
        self.mock.assert_called_once_with([('a', '1'), ('b', '2'), ('c', None)])

if __name__ == '__main__': # pragma: no cover
    unittest.main()
