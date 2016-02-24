import sys
import os
import functools
import re
import logging
import inspect

from . import getopt

DEBUG = False
logger = logging.getLogger(__name__)

class OptionError(Exception):
    pass


class StructureError(Exception):
    pass


class CommandHandler():
    def __init__(self, func, *, name=None, logger=None, alias=None, ref=None):
        self._func = func
        self._ref = ref
        self.name = func.__name__ if name is None else name
        self.opts = None
        if DEBUG:
            self.build_opts()

    def __call__(self, argv):
        self.build_opts()
        if DEBUG:
            print('"{}" called'.format(self.name))
            print(argv, repr(self.shortopts), self.longopts, sep='\n')
            gi = getopt.iter_getopt_long(argv, self.shortopts, self.longopts)
            for i in gi:
                print(i , gi.opterr, gi.optopt, gi.optind, gi.optarg)
            print(gi.argv[gi.optind:])
        self._func()

    def build_opts(self):
        if self.opts is not None:
            return
        self.opts = {}
        # Build longopts from func signature
        fas = inspect.getfullargspec(self._func)
        if len(fas.args) > 1:
            raise StructureError('Function "{}" has more than one positional '\
                'argument defined. This may result in ambiguous options. Try '\
                'varargs and keyword-only arguments instead.'.\
                    format(self._func.__name__))
        self.longopts = []
        #O, n, r, o = getopt.Option, getopt.no_argument, \
            #getopt.required_argument, getopt.optional_argument
        # keyword only args
        for i in fas.kwonlyargs:
            self.longopts.append(self.parse_opt(i))

        self.shortopts = 'ab'

        if DEBUG:
            from pprint import pprint
            print('parsed opts:')
            pprint(self.opts)
            print('parsed longopts:')
            pprint(self.longopts)
            print('parsed shortopts:')
            pprint(self.shortopts)

    def parse_opt(self, name):
        if name in self.opts:
            return
        self.opts[name] = {}
        if self._func.__doc__ is not None:
            # Try parse function docstring ':param type name: help'
            regex = re.compile(r'^\s*:param\s+(\w+)\s+{}:\s*(.*)\s*$'.format(name), re.M)
            result = regex.findall(self._func.__doc__)
            if len(result) > 1:
                raise StructureError('param "{}" type duplicated defined'.format(name))
            elif len(result) == 1:
                self.opts[name]['type'] = [result[0][0].lower()]
                self.opts[name]['help'] = [result[0][1]]

            # Try parse function docstring ':param name: help'
            regex = re.compile(r'^\s*:param\s+{}:\s*(.*)\s*$'.format(name), re.M)
            result = regex.findall(self._func.__doc__)
            if len(result) > 1 or (len(result) == 1 and 'help' in self.opts[name]):
                raise StructureError('param "{}" help dumplicated defined'.format(name))
            elif len(result) == 1:
                if 'help' in self.opts[name]:
                    raise StructureError('param "{}" help dumplicated defined'.format(name))
                else:
                    self.opts[name]['help'] = result[0]

            # Try parse function docstring ':type name: type0 or type1 or type2.
            regex = re.compile(r'^\s*:type\s+{}:\s*([\s\w]+)\.?\s*$'.format(name), re.M)
            result = regex.findall(self._func.__doc__)
            if len(result) > 1 or (len(result) == 1 and 'type' in self.opts[name]):
                raise StructureError('param "{}" type duplicated defined'.format(name))
            elif len(result) == 1:
                self.opts[name]['type'] = []
                for i in result[0].lower().split():
                    if i != 'or':
                        self.opts[name]['type'].append(i)

        print(inspect.getfullargspec(self._func))
        if 'type' not in self.opts[name]:
            fas = inspect.getfullargspec(self._func)
            # Try guess type by default value
            if name in fas.kwonlydefaults:
                val = fas.kwonlydefaults[name]
                if isinstance(val, int):
                    self.opts[name]['type'] = ['int']
                elif isinstance(val, str):
                    self.opts[name]['type'] = ['str']
                elif isinstance(val, bool):
                    self.opts[name]['type'] = ['bool']
                elif isinstance(val, str):
                    self.opts[name]['type'] = ['str']
                elif isinstance(val, list):
                    self.opts[name]['type'] = ['list']
                elif isinstance(val, dict):
                    raise NotImplementedError('dict currently not supported')

        if 'type' not in self.opts[name]:
            # Use a dafult fallback
            self.opts[name]['type'] = ['int', 'str', 'flag']

        if 'flag' in self.opts[name]['type'] or 'none' in self.opts[name]['type']:
            req = getopt.optional_argument
        else:
            req = getopt.required_argument

        # Option.val should be int or char, but with python, str is also usable.
        return getopt.Option(name, req, None, name)

    def format_value(self, name, value):
        if 'type' not in self.opts[name]:
            return value
        for i in self.opts[name]['type']:
            try:
                if i == 'int':
                    if value.lower().startswith('0x'):
                        return int(value, 16)
                    elif value.lower().startswith('0o'):
                        return int(value, 8)
                    elif value.lower().startswith('0b'):
                        return int(value, 2)
                    elif value.startswith('0'):
                        return int(value, 8)
                    else:
                        return int(value)
                elif i == 'hex':
                    return int(value, 16)
                elif i == 'dec':
                    return int(value, 10)
                elif i == 'oct':
                    return int(value, 8)
                elif i == 'bin':
                    return int(value, 2)
                elif i == 'float':
                    return float(value)
                elif i == 'str':
                    return str(value)
                elif i == 'boot':
                    return value.lower() not in ('0', 'n', 'no', 'f', 'false', \
                        'nil', 'nul', 'null', 'none', '-')
                elif i == 'list':
                    # Currently only list of str
                    return value.split(',')
                elif i == 'dict':
                    raise NotImplementedError('dict currently not supported')
                elif i == 'flag':
                    continue # silently skip
                elif i == 'none':
                    continue # silently skip
                else:
                    logger.warn('Type "{}" is not supported, skipped'.format(i))
                    if DEBUG:
                        break
                    continue
            except TypeError:
                pass
        raise OptionError('Option "{}" got invalid value "{}"'.format(name, value))


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
        self._default(argv)