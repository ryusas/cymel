# -*- coding: utf-8 -*-
u"""
Test of cymel.pyutils
"""
import unittest
from cymel_test.pyutils import (
    finalizer, immutables, ordereddict, pyutils,
)


def suite():
     return unittest.TestSuite((
        finalizer.suite(),
        immutables.suite(),
        ordereddict.suite(),
        pyutils.suite(),
    ))


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
