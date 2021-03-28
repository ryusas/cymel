# -*- coding: utf-8 -*-
u"""
Test of cymel.pyutils.ordereddict
"""
import sys
import unittest
import random

from cymel.pyutils.finalizer import registerFinalizer
from cymel.pyutils.ordereddict import CleanOrderedDict


#------------------------------------------------------------------------------
class TestCleanOrderedDict(unittest.TestCase):
    u"""
    Test of CleanOrderedDict
    """
    def setUp(self):
        random.seed(123)
        self._numbers = list(range(20))
        random.shuffle(self._numbers)

    def test_append(self):
        d = CleanOrderedDict()
        for i in self._numbers:
            d[Key(i)] = i

        self.assertEqual(self._numbers, [x.v for x in d.keys()])
        self.assertEqual(self._numbers, [x for x in d.values()])
        del d
        self.assertEqual(Key.count, 0)

    def test_list(self):
        d = CleanOrderedDict([(Key(i), i) for i in self._numbers])

        self.assertEqual(self._numbers, [x.v for x in d.keys()])
        self.assertEqual(self._numbers, [x for x in d.values()])
        del d
        self.assertEqual(Key.count, 0)


class Key(object):
    count = 0

    def __init__(self, val):
        self.v = val
        self._hash = hash(val)

        Key.count += 1

        def proc():
            Key.count -= 1
        registerFinalizer(self, proc)

    def __hash__(self):
        return self._hash

    def __eq__(self, k):
        return self.v == k.v

    def __repr__(self):
        return 'Key(%r)' % self.v


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
