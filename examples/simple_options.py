from pylibcli import default, command, run
import pylibcli.opttools

pylibcli.opttools.DEBUG = True

@default
def main(*args, aflag=None, bflag=None, cvalue=None):
    """Parse the args.

    :param aflag: Set aflag
    :type aflag: bool or None.
    :param bflag: Set bflag
    :type bflag: bool or None.
    :param int cvalue: Set cvalue
    """
    print("aflag: {}, bflag: {}, cvalue: {}".format(aflag, bflag, cvalue))
    print("Non-option arguments: {}".format(args))

if __name__ == '__main__':
    run()
