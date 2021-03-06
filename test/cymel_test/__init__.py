# -*- coding: utf-8 -*-
u"""
Test of cymel.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from cymel_test import (
    pyutils, utils,
)


def suite():
     return unittest.TestSuite((
        pyutils.suite(),
        utils.suite(),
    ))


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
