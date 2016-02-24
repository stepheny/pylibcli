__version__ = "0.2.dev2"

from .opttools import OptionHandler

default_handler = OptionHandler()
command = default_handler.command
default = default_handler.default
run = default_handler.run
