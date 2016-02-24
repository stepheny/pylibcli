import sys
import os
import functools
import inspect

from . import getopt

class OptionError(Exception):
    pass


class StructureError(Exception):
    pass


class CommandHandler():
    def __init__(self, func, *, name=None, logger=None, alias=None, ref=None):
        self._func = func
        self._ref = ref
        self.name = func.__name__ if name is None else name

    def __call__(self, argv):
        print('called with {}'.format(' '.join(argv)))


class OptionHandler():
    def __init__(self):
        self._command = []
        self._default = None

    def command(self, func=None, **kwargs):
        cur = inspect.currentframe()
        if func is None:
            return functools.partial(self.command, **kwargs)
        self._command.append(CommandHandler(func))
        name = kwargs['name'] if 'name' in kwargs else func.__name__
        for i in self._command:
            if name == i.name:
                if i._ref:
                    raise StructureError('Command "{}" already defined at [{}]'.format( \
                        name, self._default._ref))
                else:
                    raise StructureError('Command "{}" already defined'.format(name))

    def default(self, func=None, **kwargs):
        cur = inspect.currentframe()
        if func is None:
            return functools.partial(self.default, **kwargs)
        elif self._default is None:
            if cur is None:
                # Python stack frame support not available
                ref = None
            else:
                caller = inspect.getouterframes(cur, 2)[1]
                filename = os.path.relpath(caller.filename)
                ref = '{}:{}'.format(filename, caller.lineno)
                #print('ref:', ref)
            self._default = CommandHandler(func, **kwargs, ref=ref)
            return func
        else:
            if self._default._ref:
                raise StructureError('Default already defined at [{}]'.format( \
                    self._default._ref))
            else:
                raise StructureError('Default already defined')

    def run(self, argv=None):
        if argv is None:
            argv = sys.argv
        print('called with:', argv)
