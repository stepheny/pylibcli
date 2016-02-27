__version__ = "0.2.dev17"

from .opttools import OptionHandler

default_handler = OptionHandler()
command = default_handler.command
default = default_handler.default
error = default_handler.error
run = default_handler.run
