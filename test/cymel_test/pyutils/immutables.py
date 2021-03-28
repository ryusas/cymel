# -*- coding: utf-8 -*-
u"""
Test of cymel.pyutils.immutable
"""
import sys
import unittest

from cymel.pyutils.immutables import (
    CymelImmutableError, immutable, immutableType,
    ImmutableDict,
)


#------------------------------------------------------------------------------
class TestImmutables(unittest.TestCase):
    u"""
    Test of cymel.pyutils.immutable
    """
    def test_immutable(self):
        class MyData(object):
            def __init__(self, v):
                if isinstance(v, MyData):
                    self.v = v.v
                else:
                    self.v = v

        a = MyData(0)
        b = immutable(a)
        ImmutableMyData = immutableType(MyData)
        c = ImmutableMyData(2)

        a.v = 9
        self.assertEqual(b.v, 0)
        self.assertEqual(c.v, 2)
        self.assertRaises(CymelImmutableError, setattr, b, 'v', 9)
        self.assertRaises(CymelImmutableError, setattr, c, 'v', 9)
        self.assertFalse(type(b) is type(a))
        self.assertTrue(type(b) is type(c))

    def test_ImmutableDict(self):
        d = ImmutableDict(a=1, b=2)
        self.assertEqual(d['a'], 1)
        self.assertEqual(d['b'], 2)
        self.assertRaises(CymelImmutableError, d.pop, 'b')


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
