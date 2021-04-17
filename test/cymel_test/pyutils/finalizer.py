# -*- coding: utf-8 -*-
u"""
Test of cymel.pyutils.finalizer
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import unittest
from functools import partial

from cymel.pyutils import finalizer


#------------------------------------------------------------------------------
class TestFinalizer(unittest.TestCase):
    u"""
    Test of cymel.pyutils.finalizer
    """
    def _finalizer(self, data):
        self._received = data

    def setUp(self):
        self._data = 123.456789
        self._object = SimpleClass()
        self._id = finalizer.registerFinalizer(self._object, partial(self._finalizer, self._data))
        self._received = None

    def tearDown(self):
        if self._id:
            finalizer.deregisterFinalizer(self._id)
        del self._id
        del self._object

    def test_registerFinalizer(self):
        self.assertEqual(self._received, None)
        self._object = None
        self.assertEqual(self._received, self._data)

        self.assertRaises(KeyError, finalizer.deregisterFinalizer, self._id)
        self._id = None

    def test_deregisterFinalizer(self):
        finalizer.deregisterFinalizer(self._id)
        self.assertRaises(KeyError, finalizer.deregisterFinalizer, self._id)
        self._id = None

        self._object = None
        self.assertEqual(self._received, None)


class SimpleClass(object):
    pass


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
