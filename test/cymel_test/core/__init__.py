u"""
Test of cymel.core
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from cymel_test.core import (
    cyobjects,
    constraint,
)


def suite():
     return unittest.TestSuite((
        cyobjects.suite(),
        constraint.suite(),
    ))


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
