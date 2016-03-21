import enum
import functools
import logging
import os
try:
    from gettext import gettext as _
except ImportError:
    def _(s):
        return s

logger = logging.getLogger(__name__)


class GetoptError(Exception):
    pass


class GetRef():
    def __init__(self, target):
        self.target = target
    def __getattr__(self, name):
        return functools.partial(self.target.__setattr__, name)


class Flags():
    def __init__(self):
        self._ = GetRef(self)


def my_index(_str, _chr):
    assert isinstance(_str, str)
    assert isinstance(_chr, str)
    idx = _str.find(_chr)
    if idx >= 0:
        return _str[idx:]
    else:
        return None


class has_arg_enum(enum.Enum):
    no_argument = 0
    required_argument = 1
    optional_argument = 2

no_argument = has_arg_enum.no_argument
required_argument = has_arg_enum.required_argument
optional_argument = has_arg_enum.optional_argument

class Option():
    def __init__(self, name, has_arg, flag_setter, val):
        if isinstance(name, str):
            self.name = name
        else:
            raise GetoptError('option.name should be string')
        if isinstance(has_arg, has_arg_enum):
            self.has_arg = has_arg
        else:
            raise GetoptError('option.has_arg should be has_arg_enum')
        if flag_setter is None or flag_setter == 0 or callable(flag_setter):
            self.flag_setter = flag_setter
        else:
            raise GetoptError('option.flag_setter should be callable')
        if isinstance(val, (int, str)):
            self.val = val
        else:
            raise GetoptError('option.val should be int or char')
    def __repr__(self):
        return '<Option: {}, {}, {}, {}>'.format(repr(self.name), 
            self.has_arg.name, repr(self.flag_setter), repr(self.val))


class opt_ordering(enum.Enum):
    REQUIRE_ORDER = 0
    PERMUTE = 1
    RETURN_IN_ORDER = 2

REQUIRE_ORDER = opt_ordering.REQUIRE_ORDER
PERMUTE = opt_ordering.PERMUTE
RETURN_IN_ORDER = opt_ordering.RETURN_IN_ORDER

class GetoptIter():
    def __init__(self, argv, optstring, longopts, longind, long_only):
        self.argv = argv
        self.optstring = optstring
        self.longopts = longopts
        self.longind = longind
        self.long_only = long_only
        self.opterr = 1
        self.optopt = '?'
        self.optind = 1
        self.optarg = None
        self.first_nonopt = 1
        self.last_nonopt = 1
        self.nextchar = None
        if 'POSIXLY_CORRECT' in os.environ:
            self.posixly_correct = os.environ['POSIXLY_CORRECT']
        else:
            self.posixly_correct = None

        if len(self.optstring) > 0 and self.optstring[0] == '-':
            self.ordering = RETURN_IN_ORDER
            self.optstring = self.optstring[1:]
        elif len(self.optstring) > 0 and self.optstring[0] == '+':
            self.ordering = REQUIRE_ORDER
            self.optstring = self.optstring[1:]
        elif self.posixly_correct is not None:
            self.ordering = REQUIRE_ORDER
        else:
            self.ordering = PERMUTE

    def __iter__(self):
        return self

    def __next__(self):
        self.optarg = None
        if self.nextchar is None:
            if self.ordering == PERMUTE:
                if self.first_nonopt != self.last_nonopt \
                    and self.last_nonopt != self.optind:
                    self.exchange()
                elif self.last_nonopt != self.optind:
                    self.first_nonopt = self.optind

                while self.optind < len(self.argv) \
                    and (self.argv[self.optind][0] != '-' \
                        or len(self.argv[self.optind]) == 1):
                    self.optind += 1
                self.last_nonopt = self.optind

            if self.optind != len(self.argv) and self.argv[self.optind] == '--':
                self.optind += 1

                if self.first_nonopt != self.last_nonopt \
                    and self.last_nonopt != self.optind:
                    self.exchange()
                elif self.first_nonopt == self.last_nonopt:
                    self.first_nonopt = self.optind
                self.last_nonopt = len(self.argv)

                self.optind = len(self.argv)

            if self.optind == len(self.argv):
                if self.first_nonopt != self.last_nonopt:
                    self.optind = self.first_nonopt
                raise StopIteration

            if self.argv[self.optind][0] != '-' or len(self.argv[self.optind]) == 1 :
                if self.ordering == REQUIRE_ORDER:
                    raise StopIteration
                self.optarg = self.argv[self.optind]
                self.optind += 1
                return 1

            temp = self.argv[self.optind]
            self.nextchar = temp[1+(self.longopts is not None and len(temp) >= 1 \
                and temp[1] == '-'):]

        if self.longopts is not None and (self.argv[self.optind][1] == '-' \
            or (self.long_only and (len(self.argv[self.optind]) >= 3 \
                or not my_index(self.optstring, self.argv[self.optind][1])))):
            nameend = self.nextchar.find('=')
            if nameend < 0:
                nameend = len(self.nextchar)
            exact = False
            ambig = False
            pfound = None
            self.optarg = None
            #indfound = 0
            #option_index = None

            for p in self.longopts:
                #option_index = longopts.index(p)
                if p.name[:nameend] == self.nextchar[:nameend]:
                    if nameend == len(p.name):
                        pfound = p
                        #indfound = option_index
                        exact = True
                        break
                    elif pfound is None:
                        pfound = p
                        #indfound = option_index
                    else:
                        ambig = True

            if ambig and not exact:
                if self.opterr:
                    logger.error(_("{}: option {} is ambiguous").\
                        format(self.argv[0], self.argv[self.optind]))
                self.nextchar = None
                self.optind += 1
                return '?'

            if pfound is not None:
                #option_index = indfound
                self.optind += 1
                if self.nextchar[nameend:]:
                    if pfound.has_arg != no_argument:
                        self.optarg = self.nextchar[nameend+1:]
                    else:
                        if self.opterr:
                            if len(self.argv[self.optind-1]) > 1 and self.argv[self.optind-1][1] == '-':
                                logger.error(_("{}: option `--{}' doesn't allow and argument").format(self.argv[0], pfound.name))
                            else:
                                logger.error(_("{}: option `{}{}' doesn't allow and argument").format(self.argv[0], self.argv[self.optind-1][0], pfound.name))
                        self.nextchar = None
                        return '?'
                elif pfound.has_arg == required_argument:
                    if self.optind < len(self.argv):
                        self.optarg = self.argv[self.optind]
                        self.optind += 1
                    else:
                        if self.opterr:
                            logger.error(_("{}: option `{}' requires an argument").format(self.argv[0], self.argv[self.optind-1]))
                        self.nextchar = None
                        return ':' if len(self.optstring) > 0 and self.optstring[0] == ':' else '?'
                self.nextchar = None
                #if self.longind is not None:
                    #self.longind = option_index
                self.longind = self.longopts.index(pfound)
                if callable(pfound.flag_setter):
                    pfound.flag_setter(pfound.val)
                    return 0
                return pfound.val

            if (not self.long_only) \
                or (len(self.argv[self.optind]) > 1 \
                    and self.argv[self.optind][1] == '-') \
                    or (my_index(self.optstring, self.nextchar) is None):
                if self.opterr:
                    if len(self.argv) > self.optind \
                        and len(self.argv[self.optind]) > 1 \
                            and self.argv[self.optind][1] == '-':
                        logger.error(_("{}: unrecognized option `--{}'").\
                            format(self.argv[0], self.nextchar))
                    elif len(self.argv) > self.optind:
                        logger.error(_("{}: unrecognized option `{}{}'").\
                            format(self.argv[0], self.argv[self.optind][0], \
                                self.nextchar))
                self.nextchar = None
                self.optind += 1
                return '?'

        c = self.nextchar[0]
        self.nextchar = self.nextchar[1:]
        temp = my_index(self.optstring, c)
        if len(self.nextchar) == 0:
            self.optind += 1
            self.nextchar = None

        if temp is None or c == ':':
            if self.opterr:
                if self.posixly_correct is not None:
                    logger.error(_("{}: illegal option -- {}").format(self.argv[0], c))
                else:
                    logger.error(_("{}: invalid option -- {}").format(self.argv[0], c))
            self.optopt = c
            return '?'
        if len(temp) > 1 and temp[1] == ':':
            if len(temp) > 2 and temp[2] == ':':
                # This is an option that accepts an argument optionally.
                if self.nextchar is not None and len(self.nextchar) > 0:
                    self.optarg = self.nextchar
                    self.optind += 1
                else:
                    self.optarg = None
                self.nextchar = None
            else:
                # This is an option that requires an argument
                if self.nextchar is not None and len(self.nextchar) > 0:
                    self.optarg = self.nextchar
                    self.optind += 1
                elif self.optind == len(self.argv):
                    if self.opterr:
                        logger.error(_("{}: option requires an argument -- {}")\
                            .format(self.argv[0], c))
                    self.optopt = c
                    if self.optstring[0] == ':':
                        c = ':'
                    else:
                        c = '?'
                else:
                    self.optarg = self.argv[self.optind]
                    self.optind += 1
                self.nextchar = None
        return c

    def exchange(self):
        bottom = self.first_nonopt
        middle = self.last_nonopt
        top = self.optind

        while top > middle and middle > bottom:
            if top - middle > middle - bottom:
                length = middle - bottom
                for i in range(length):
                    self.argv[bottom + i], self.argv[top - length + i] = \
                        self.argv[top - length + i], self.argv[bottom + i]
                top -= length
            else:
                length = top - middle
                for i in range(length):
                    self.argv[bottom + i], self.argv[middle + i] = \
                        self.argv[middle + i], self.argv[bottom + i]
                bottom += length

        self.first_nonopt += self.optind - self.last_nonopt
        self.last_nonopt = self.optind


def iter_getopt(argv, shortopts):
    return GetoptIter(argv, optstring=shortopts, longopts=None, \
        longind=None, long_only=None)

def iter_getopt_long(argv, shortopts, longopts):
    return GetoptIter(argv, optstring=shortopts, longopts=longopts, \
        longind=None, long_only=None)

def iter_getopt_long_only(argv, shortopts, longopts):
    return GetoptIter(argv, optstring=shortopts, longopts=longopts, \
        longind=None, long_only=True)
