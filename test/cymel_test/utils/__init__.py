# -*- coding: utf-8 -*-
u"""
Test of cymel.utils
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from cymel_test.utils import (
    files, melgvar, namespace, operation, optionvar,
)


def suite():
     return unittest.TestSuite((
        files.suite(),
        melgvar.suite(),
        namespace.suite(),
        operation.suite(),
        optionvar.suite(),
    ))


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
