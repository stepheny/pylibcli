pylibcli
========
A few libraries intend to help writing cli program more convenient.




Submodules
----------

opttools
~~~~~~~~
Specify Command with decorators.
Automatically generate option list from decorator hinting, docstring and optiong default value.
Parse a list of argumens and call corresponding method in a chainable style.



getopt
~~~~~~
Yet another implementation to work close to GNU getopt.
Unlike standard library, pylibcli.getopt employs an iterator interface.
Optional argument supported.
opttools use getopt internally.
