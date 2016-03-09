import sys
import os
import functools
import re
import collections
import logging
import inspect

from . import getopt

DEBUG = False
_logger = logging.getLogger(__name__)

class OptionError(Exception):
    pass


class StructureError(Exception):
    pass


class CommandHandler():
    def __init__(self, func, *, _=None, _name=None, _ref=None, **kwargs):
        self._func = func
        self._ref = _ref
        self._ = _
        self.name = func.__name__ if _name is None else _name
        self.hint = kwargs
        self.opts = None
        self.alias = None
        if DEBUG:
            self.build_opts()

    def __call__(self, argv, *, last=None):
        self.build_opts()
        kwargs = {}
        gi = getopt.iter_getopt_long(argv, self.shortopts, self.longopts)
        for i in gi:
            if i in self.opts:
                kwargs[i] = self.format_value(i, gi.optarg)
            elif i in self.alias:
                i = self.alias[i]
                kwargs[i] = self.format_value(i, gi.optarg)
            else:
                raise OptionError('Invalid option: "{}" with value: "{}"'.\
                    format(gi.optopt, gi.optarg))
        args = gi.argv[gi.optind:]

        fas = inspect.getfullargspec(self._func)
        for i in fas.kwonlyargs:
            if i not in kwargs and (fas.kwonlydefaults is None \
                or fas.kwonlydefaults is not None and i not in fas.kwonlydefaults):
                raise OptionError('Option "{}" should be provide with "{}"'.\
                    format(i, " or ".join(self.opts[i]['alias'])))

        if self._func.__class__ is type: # Constructor
            if fas.args and fas.args[0] == 'self':
                del fas.args[0]

        if last is not None:
            args.insert(0, last)

        reqnarg = (0 if fas.args is None else len(fas.args)) \
            - (0 if fas.defaults is None else len(fas.defaults))
        for i in range(reqnarg):
            if fas.args[i] in kwargs:
                reqnarg -= 1
        if reqnarg > len(args):
            raise OptionError('Not enough positional argument')
        elif fas.varargs is not None:
            reqnarg = len(args)
        else:
            reqnarg = sum([x not in kwargs for x in fas.args])
        for i in range(last is not None, reqnarg): # Skip first if chained
            #if i < len(fas.args) and fas.args[i] in kwargs: # Should not happen
                #raise OptionError('Option "{}" got both keyword and '\
                    #'positional value'.format(fas.args[i]))
            if i < len(args) and i < len(fas.args) and  fas.args[i] in self.opts:
                args[i] = self.format_value(fas.args[i], args[i])

        return self._func(*args[:reqnarg], **kwargs), args[reqnarg:]

    def build_opts(self):
        if self.opts is not None:
            return
        self.opts = {}
        self.alias = {}
        # Build longopts from func signature
        fas = inspect.getfullargspec(self._func)
        # DEPRECATED since 0.3
        #if len(fas.args) > 2 or len(fas.args) == 2 and fas.args[0] != 'self':
            #raise StructureError('Function "{}" has more than one positional '\
                #'argument defined. This may result in ambiguous options. Try '\
                #'varargs and keyword-only arguments instead.'.\
                    #format(self._func.__name__))
        if fas.varargs is not None and \
            (len(fas.args) > 1 or len(fas.args) == 1 and fas.args[0] != 'self'):
            raise StructureError('Function "{}" is using positional argument '\
                'and variable arguments at the same time. This may result in '\
                'ambiguous options. Try varargs and keyword-only arguments instead.'.\
                    format(self._func.__name__))
        self.longopts = []
        self.shortopts = '' if self._ is None else self._
        # positional args
        #if len(fas.args) == 1:
            #self.longopts.extend(self.parse_opt(fas.args[0]))
        for i in fas.args:
            if i != 'self':
                self.longopts.extend(self.parse_opt(i))
        # keyword only args
        for i in fas.kwonlyargs:
            if not i.startswith('_'):
                self.longopts.extend(self.parse_opt(i))

        if DEBUG:
            print('  short option string: "{}"'.format(self.shortopts), file=sys.stderr)
            print('  long options:', file=sys.stderr)
            print('    "{}"'.format('", "'.join([x.name for x in self.longopts])), \
                file=sys.stderr) 

    def parse_opt(self, name):
        #if name in self.opts: # Should not happen
            #return
        self.opts[name] = {'alias': []}
        if name in self.hint:
            hint = self.hint[name]
            if hint.startswith('_'):
                shortonly = True
                hint = hint[1:]
            else:
                shortonly = False
            i = hint.find(':')
            if i < 0:
                shortopts = hint
                hint = ''
            else:
                shortopts = hint[:i]
                hint = hint[i:]
            for i in shortopts:
                if i in self.alias:
                    raise StructureError('Shortopt "{}" duplicated defined'.\
                        format(i))
                else:
                    self.alias[i] = name
                    self.opts[name]['alias'].append('-'+i)
            if hint.startswith('::'):
                req = getopt.optional_argument
                for i in shortopts:
                    self.shortopts += i + '::'
                htype = hint[2:].split('=')
                if len(htype) != 2:
                    raise StructureError('Option "{}" optional value requires '\
                        'a default value'.format(name))
                if htype[0]:
                    self.opts[name]['type'] = htype[0].split(',')
                else:
                    self.opts[name]['type'] = ['int', 'float', 'str']
                self.opts[name]['default'] = htype[1]
            elif hint.startswith(':'):
                req = getopt.required_argument
                for i in shortopts:
                    self.shortopts += i + ':'
                htype = hint[1:].split('=')
                if len(htype) != 1:
                    raise StructureError('Option "{}" required value should '\
                        'not define a default value'.format(name))
                if htype[0]:
                    self.opts[name]['type'] = htype[0].split(',')
                else:
                    self.opts[name]['type'] = ['int', 'float', 'str']
            else:
                req = getopt.no_argument
                for i in shortopts:
                    self.shortopts += i
                self.opts[name]['type'] = ['flag']

            if shortonly:
                ret = []
            else:
                self.opts[name]['alias'].append('--'+name)
                ret = [getopt.Option(name, req, None, name)]
            if self._func.__doc__ is not None:
                # Try parse function docstring ':param [type] name: help'
                regex = re.compile(r'^\s*:param[\w\s]+{}:\s*(.*)\s*$'.format(name), re.M)
                result = regex.findall(self._func.__doc__)
                if len(result) > 1:
                    raise StructureError('param "{}" type duplicated defined'.format(name))
                elif len(result) == 1:
                    self.opts[name]['help'] = result[0]
            else:
                self.opts[name]['help'] = None

            if DEBUG:
                NRO = (' no', '', ' optional')
                print('  Option "{}" requires{} argument'.format(name,  \
                    NRO[req.value]), file=sys.stderr)
                print('    available as "{}"'.format('", "'.join( \
                    self.opts[name]['alias'])), file=sys.stderr)
                if req != getopt.no_argument:
                    print('    argument type prefered "{}"'.format('", "'.join( \
                        self.opts[name]['type'])), file=sys.stderr)
                if 'help' in self.opts[name] and self.opts[name]['help'] is not None:
                    print('    with docstring: "{}"'.format( \
                        self.opts[name]['help']), file=sys.stderr)
                else:
                    print('    docstring not available', file=sys.stderr)
            return ret

        elif self._func.__doc__ is not None:
            # Try parse function docstring ':param type name: help'
            regex = re.compile(r'^\s*:param\s+(\w+)\s+{}:\s*(.*)\s*$'.format(name), re.M)
            result = regex.findall(self._func.__doc__)
            if len(result) > 1:
                raise StructureError('param "{}" type duplicated defined'.format(name))
            elif len(result) == 1:
                self.opts[name]['type'] = [result[0][0].lower()]
                self.opts[name]['help'] = result[0][1]

            # Try parse function docstring ':param name: help'
            regex = re.compile(r'^\s*:param\s+{}:\s*(.*)\s*$'.format(name), re.M)
            result = regex.findall(self._func.__doc__)
            if len(result) > 1 or (len(result) == 1 and 'help' in self.opts[name]):
                raise StructureError('param "{}" help dumplicated defined'.format(name))
            elif len(result) == 1:
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

        if 'type' not in self.opts[name]:
            fas = inspect.getfullargspec(self._func)
            # Try guess type by default value
            if fas.kwonlydefaults is not None and name in fas.kwonlydefaults:
                val = fas.kwonlydefaults[name]
                if isinstance(val, bool): # issubclass(bool, int)
                    self.opts[name]['type'] = ['bool']
                elif isinstance(val, int):
                    self.opts[name]['type'] = ['int']
                elif isinstance(val, str):
                    self.opts[name]['type'] = ['str']
                elif isinstance(val, list):
                    self.opts[name]['type'] = ['list']
                elif isinstance(val, dict):
                    self.opts[name]['type'] = ['dict']

        if 'type' not in self.opts[name]:
            # Use a dafult fallback
            self.opts[name]['type'] = ['int', 'float', 'str', 'flag']

        if self.opts[name]['type'] in (['flag'], ['none']):
            req = getopt.no_argument
        elif 'flag' in self.opts[name]['type'] or 'none' in self.opts[name]['type']:
            req = getopt.optional_argument
        else:
            req = getopt.required_argument

        self.opts[name]['alias'].append('--'+name)

        if DEBUG:
            NRO = (' no', '', ' optional')
            print('  Option "{}" requires{} argument'.format(name,  \
                NRO[req.value]), file=sys.stderr)
            print('    available as "{}"'.format('", "'.join( \
                self.opts[name]['alias'])), file=sys.stderr)
            if req != getopt.no_argument:
                print('    argument type prefered "{}"'.format('", "'.join( \
                    self.opts[name]['type'])), file=sys.stderr)
            if 'help' in self.opts[name] and self.opts[name]['help'] is not None:
                print('    with docstring: "{}"'.format( \
                    self.opts[name]['help']), file=sys.stderr)
            else:
                print('    docstring not available', file=sys.stderr)
        # Option.val should be int or char, but with python, str is also usable.
        return [getopt.Option(name, req, None, name)]

    def format_value(self, name, value):
        #if 'type' not in self.opts[name]: # Should not happen
            #return value
        if value is None and 'default' in self.opts[name]:
            value = self.opts[name]['default']
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
                elif i == 'bool':
                    return value.lower() not in ('0', 'n', 'no', 'f', 'false', \
                        'nil', 'nul', 'null', 'none', '-')
                elif i == 'list':
                    # Currently only list of str
                    return value.split(',')
                elif i == 'dict':
                    ret = []
                    for i in value.split(','):
                        kv = i.split('=', 1)
                        ret.append(tuple(kv) if len(kv) == 2 else (kv[0], None))
                    return ret
                elif i == 'flag':
                    if value is None:
                        return ''
                    else:
                        continue
                elif i == 'none':
                    if value is None:
                        return ''
                    else:
                        continue
                else:
                    _logger.warn('Type "{}" is not supported, skipped'.format(i))
                    if DEBUG:
                        break
                    continue
            except (TypeError, ValueError, AttributeError):
                pass
        raise OptionError('Option "{}" should be "{}" but got invalid value "{}"'.\
            format(name, '" or "'.join(self.opts[name]['type']), value))


class OptionHandler():
    def __init__(self):
        self._command = collections.OrderedDict()
        self._default = None
        self._error = collections.OrderedDict()

    def command(self, func=None, _='+', **kwargs):
        cur = inspect.currentframe()
        if func is None:
            return functools.partial(self.command, **kwargs)
        if not callable(func):
            raise StructureError('Command "{}" not callable'.format(repr(func)))
        name = kwargs['_name'] if '_name' in kwargs else func.__name__
        if name in self._command:
            if self._command[name]._ref:
                raise StructureError('Command "{}" already defined at [{}]'.format( \
                    name, self._command[name]._ref))
            else:
                raise StructureError('Command "{}" already defined'.format(name))
        else:
            if cur is None:
                # Python stack frame support not available
                ref = None
            else:
                caller = inspect.getouterframes(cur, 2)[1]
                filename = os.path.relpath(caller.filename)
                ref = '{}:{}'.format(filename, caller.lineno)
            kwargs['_'] = _
            if DEBUG:
                if ref:
                    print('\nCommand "{}" at [{}]:'.format(name, ref), file=sys.stderr)
                else:
                    print('\nCommand "{}":'.format(name), file=sys.stderr)
            self._command[name] = CommandHandler(func, **kwargs, _ref=ref)
        return func

    def default(self, func=None, _='+', **kwargs):
        cur = inspect.currentframe()
        if func is None:
            return functools.partial(self.default, **kwargs)
        elif not callable(func):
            raise StructureError('Command "{}" not callable'.format(repr(func)))
        elif self._default is None:
            if cur is None:
                # Python stack frame support not available
                ref = None
            else:
                caller = inspect.getouterframes(cur, 2)[1]
                filename = os.path.relpath(caller.filename)
                ref = '{}:{}'.format(filename, caller.lineno)
            kwargs['_'] = _
            if DEBUG:
                if ref:
                    print('\nDefault command at [{}]:'.format(ref), file=sys.stderr)
                else:
                    print('\nDefault command:', file=sys.stderr)
            self._default = CommandHandler(func, **kwargs, _ref=ref)
        else:
            if self._default._ref:
                raise StructureError('Default already defined at [{}]'.format( \
                    self._default._ref))
            else:
                raise StructureError('Default already defined')
        return func

    def error(self, ext=None, **kwargs):
        cur = inspect.currentframe()
        if ext is None:
            return functools.partial(self.error, **kwargs)
        elif not issubclass(ext, Exception):
            raise StructureError('Error "{}" should be subclass of "Exception"'.\
                format(ext.__name__))
        else:
            self._error[ext] = kwargs
        return ext

    def run(self, argv=None, *, last=None, logger=None, debug=False):
        if argv is None:
            argv = sys.argv
        if logger is None:
            logger = _logger
        try:
            if callable(self._default):
                last, argv = self._default(argv, last=last)
            else:
                argv = argv[1:]
            while argv:
                if argv[0] in self._command:
                    last, argv = self._command[argv[0]](argv, last=last)
                else:
                    raise OptionError('Unknow command "{}"'.format(argv[0]))
        except tuple(self._error) as exc:
            errno = 127
            for i in self._error:
                if isinstance(exc, i):
                    if 'errno' in self._error[i]:
                        errno = self._error[i]['errno']
                    break
            logger.error(repr(exc))
            sys.exit(errno)
        except () if debug else OptionError as ex:
            logger.error(ex)
            sys.exit(127)
