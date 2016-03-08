from libcli import default, command, error, run
import libcli.opttools

#libcli.opttools.DEBUG = True


class node():
    def __init__(self, op, l, r=None):
        self.op = op
        self.l = l
        self.r = r

    def __str__(self):
        if self.op is None:
            return str(self.l)
        else:
            return '({})'.format(''.join([str(self.l), str(self.op), str(self.r)]))

    def eval(self):
        if self.op is None:
            return self.l
        elif self.op == '+':
            return self.l.eval() + self.r.eval()
        elif self.op == '-':
            return self.l.eval() - self.r.eval()
        elif self.op == 'x':
            return self.l.eval() * self.r.eval()
        elif self.op == '/':
            return self.l.eval() / self.r.eval()
        else:
            raise NotImplementedError('Operator {}'.format(self.op))


@default(val='_:int,float')
class Expression():
    def __init__(self, val=None):
        self._root = node(None, val) if val is not None else None

    def __del__(self):
        if self._root is None:
            print('No input.')
        else:
            val = self._root.eval()
            if isinstance(val, float):
                print('{}={:.3}'.format(self, val))
            else:
                print('{}={}'.format(self, val))

    def __str__(self):
        return str(self._root)

    @command(_name='+', val='_:int,float')
    def add(self, val):
        val = node(None, val)
        if self._root is None:
            self._root = val
        else:
            self._root = node('+', self._root, val)
        return self

    @command(_name='-', val='_:int,float')
    def sub(self, val):
        val = node(None, val)
        if self._root is None:
            self._root = val
        else:
            self._root = node('-', self._root, val)
        return self

    @command(_name='*', val='_:int,float')
    @command(_name='x', val='_:int,float')
    def add(self, val):
        val = node(None, val)
        if self._root is None:
            self._root = val
        elif self._root.op is None:
            self._root = node('x', self._root, val)
        else:
            i = self._root
            while i.r.op is not None and i.r.op in ('+', '-'):
                i = i.r
            i.r = node('x', i.r, val)
        return self

    @command(_name='/', val='_:int,float')
    def add(self, val):
        val = node(None, val)
        if self._root is None:
            self._root = val
        elif self._root.op is None:
            self._root = node('/', self._root, val)
        else:
            i = self._root
            while i.r.op is not None and i.r.op in ('+', '-'):
                i = i.r
            i.r = node('/', i.r, val)
        return self




if __name__ == '__main__':
    run()
