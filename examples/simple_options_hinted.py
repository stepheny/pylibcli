from pylibcli import default, command, run
import pylibcli.opttools

#pylibcli.opttools.DEBUG = True

@default(aflag='_a', bflag='_b', cvalue='c:int,float')
def main(*args, aflag=None, bflag=None, cvalue):
    """Parse the args.

    :param aflag: Set aflag
    :type aflag: flag.
    :param bflag: Set bflag
    :type bflag: flag.
    :param int cvalue: Set cvalue
    """

    aflag = 'not set' if aflag is None else 'set'
    bflag = 'not set' if bflag is None else 'set'
    print("aflag: {aflag}, bflag: {bflag}, cvalue: {cvalue}".format(**locals()))
    print("Non-option arguments: \"{}\"".format("\", \"".join(args)))

if __name__ == '__main__':
    run()
