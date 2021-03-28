# -*- coding: utf-8 -*-
u"""
Test of cymel.utils.melgvar
"""
import sys
import unittest

import maya.mel as mel

from cymel.utils.melgvar import melvar


#------------------------------------------------------------------------------
class TestMelgvar(unittest.TestCase):
    u"""
    Test of cymel.utils.melgvar
    """
    def test_melvar(self):
        name = 'gTestCymel'
        v0 = 123
        v1 = 456
        num = len(melvar)
        if name not in melvar:
            num += 1
            mel.eval('int $%s = %d;' % (name, v0))
            self.assertEqual(num, len(melvar))
        else:
            mel.eval('int $%s = %d;' % (name, v0))
        self.assertEqual(melvar[name], v0)
        mel.eval('int $%s = %d;' % (name, v1))
        self.assertEqual(melvar[name], v1)


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
