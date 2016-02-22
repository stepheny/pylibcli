import enum
import functools


class has_arg_enum(enum.Enum):
    no_argument = 0
    required_argument = 1
    optional_argument = 2

no_argument = has_arg_enum.no_argument
required_argument = has_arg_enum.required_argument
optional_argument = has_arg_enum.optional_argument


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


class option():
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

