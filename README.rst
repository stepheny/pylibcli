pylibcli
========
A few libraries intend to help writing cli program more convenient.


Usage
-----

Basic
~~~~~
Hello world: examples/hello_world.py::

    from libcli import default, run

    @default
    def main():
        print("Hello world!")

    if __name__ == '__main__':
        run()

Define option type
~~~~~~~~~~~~~~~~~~
by docstring: examples/simple_options.py::

    @default
    def main(*args, aflag=None, bflag=None, cvalue=None):
        """Parse the args.

        :param aflag: Set aflag
        :type aflag: flag.
        :param bflag: Set bflag
        :type bflag: flag.
        :param int cvalue: Set cvalue
        """

by decorator hint: examples/simple_options_hinted.py::

    @default(aflag='_a', bflag='_b', cvalue='c:int,float')
    def main(*args, aflag=None, bflag=None, cvalue):

otherwise guess from option default value.


Hint string: [_]shortopt[:[[[type1],type2],type3...] | ::[[[type1],type2],type3...]=default]
- startswith a '_' the option would be used as short option only,
otherwise the option name would be used as a long option;
- shortopt should be a list of characters to be used as short option
- without colons means this option requires no argument,
if set function would be called with this option set a value not None.
- a single colon means this option requires an argument.
- double colon measn the argument is optional, a default value is required
- type list has priority

Possible types (not case sensitive):
- str  a command argument could always be parsed as a string
- int, hex, dec, oct, bin  parse argument as an integer,
int accepts 0x, 0o, 0b, 0(c-style octal literal), default decimal
- float  parse as a floating point number
- flag, none  accept no argument, if set value will be not None, currently ''
following types may vary in future:
- bool  '0', 'n', 'no', 'f', 'false', 'nil', 'nul', 'null', 'none', '-' is False,
otherwise True
- list  a comma separated list, currently all values are supposed to be string
- dict  a comma separated key=value pair list, key and value are supposed to be string


Submodules
----------

opttools
~~~~~~~~
Specify command with decorators.
Automatically generate option list from decorator hinting, docstring and option default value.
Parse a list of argumens and call corresponding method in a chainable style.



getopt
~~~~~~
Yet another implementation to work close to GNU getopt.
Unlike standard library, pylibcli.getopt employs an iterator interface.
Optional argument supported.
opttools use getopt internally.
