#! /usr/bin/env python3

import sys
import os
from pylibcli.getopt import iter_getopt_long, Flags, Option, \
    no_argument, required_argument, optional_argument

if __name__ == '__main__':
    flags = Flags()
    flags.verbose = 0

    long_options = [
        Option("verbose", no_argument,       flags._.verbose, 1),
        Option("brief",   no_argument,       flags._.verbose, 0),
        Option("add",     no_argument,       None, 'a'),
        Option("append",  no_argument,       None, 'b'),
        Option("delete",  required_argument, None, 'd'),
        Option("create",  required_argument, None, 'c'),
        Option("file",    required_argument, None, 'f'),]

    gi = iter_getopt_long(sys.argv, "abc:d:f:", long_options)
    gi.longind = 0

    for c in gi:
        if c == 0:
            if long_options[gi.longind].flag_setter:
                break
            print("option {}".format(long_options[gi.longind].name), end='')
            if gi.optarg:
                print(" with arg {}", gi.optarg)
            else:
                print()
        elif c == 'a':
            print("option -a")
        elif c == 'b':
            print("option -b")
        elif c == 'c':
            print("option -c with value `{}'".format(gi.optarg))
        elif c == 'd':
            print("option -d with value `{}'".format(gi.optarg))
        elif c == 'f':
            print("option -f with value `{}'".format(gi.optarg))
        elif c == '?':
            ...
        else:
            os.abort()

    if flags.verbose:
        print("verbose flag is set")

    if gi.optind < len(gi.argv):
        print("non-option ARGV-elements: ", end='')
        while gi.optind < len(gi.argv):
            print("{} ".format(gi.argv[gi.optind]), end='')
            gi.optind += 1
        print()

    sys.exit(0)
