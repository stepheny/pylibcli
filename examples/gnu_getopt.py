#! /usr/bin/env python3
"""
Equivalent to
http://www.gnu.org/software/libc/manual/html_node/Example-of-Getopt.html
"""

import sys
import os
from pylibcli.getopt import iter_getopt

if __name__ == '__main__':
    aflag = 0
    bflag = 0
    cvalue = None

    gi = iter_getopt(sys.argv, "abc:")
    for c in gi:
        if c == 'a':
            aflag = 1
        elif c == 'b':
            bflag = 1
        elif c == 'c':
            cvalue = gi.optarg
        elif c == '?':
            if gi.optopt == 'c':
                print("Option -{} requires an argument.".format(gi.optopt), file=sys.stderr)
            else:
                print("Unknown option `{}'".format(repr(gi.optopt)), file=sys.stderr)
            sys.exit(1)
        else:
            os.abort()

    print("aflag = {}, bflag = {}, cvalue = {}".format(aflag, bflag, cvalue))

    for i in sys.argv[gi.optind:]:
        print("Non-option argument {}".format(i))
    sys.exit(0)
