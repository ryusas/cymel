# -*- coding: utf-8 -*-
u"""
Test of cymel.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# import sys, os
#
# sys.path.insert(0, os.path.join(__path__[0], '..', '..', 'python'))

import unittest
from cymel_test import (
    core, pyutils, utils,
)


def suite():
     return unittest.TestSuite((
        core.suite(),
        pyutils.suite(),
        utils.suite(),
    ))


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
