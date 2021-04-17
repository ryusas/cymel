# -*- coding: utf-8 -*-
u"""
Test of cymel.utils.namespace
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import unittest

import maya.cmds as cmds

from cymel.utils.namespace import Namespace, RelativeNS


#------------------------------------------------------------------------------
class TestNamespace(unittest.TestCase):
    u"""
    Test of cymel.utils.namespace
    """
    def test_namespace(self):
        cmds.file(f=True, new=True)

        boo = Namespace('boo')
        self.assertEqual(boo, ':boo')
        self.assertFalse(boo.exists())
        self.assertFalse(boo.isCurrent())

        with boo:
            self.assertEqual(boo, ':boo')
            self.assertTrue(boo.exists())
            self.assertTrue(boo.isCurrent())

            aaa = cmds.createNode('transform', n='aaa')
            self.assertEqual(aaa, 'boo:aaa')
            self.assertTrue(cmds.objExists(aaa))

            with RelativeNS():
                bbb = cmds.createNode('transform', n='bbb')
                self.assertEqual(bbb, 'bbb')
                self.assertTrue(cmds.objExists(bbb))

                foo = Namespace('foo')
                self.assertEqual(foo, ':boo:foo')
                self.assertFalse(foo.exists())
                self.assertFalse(foo.isCurrent())

                woo = Namespace('woo')
                self.assertEqual(woo, ':boo:woo')
                self.assertFalse(woo.exists())
                self.assertFalse(woo.isCurrent())

            with foo:
                self.assertTrue(foo.exists())
                self.assertTrue(foo.isCurrent())

                ccc = cmds.createNode('transform', n='ccc')
                self.assertEqual(ccc, 'boo:foo:ccc')
                self.assertTrue(cmds.objExists(ccc))

            with RelativeNS(woo):
                self.assertTrue(woo.exists())
                self.assertTrue(woo.isCurrent())

                ddd = cmds.createNode('transform', n='ddd')
                self.assertEqual(ddd, 'ddd')
                self.assertTrue(cmds.objExists(ddd))

            self.assertEqual(boo.relative(), '')
            self.assertEqual(foo.relative(), 'foo')
            self.assertEqual(woo.relative(), 'woo')

        aaa = ':' + aaa
        self.assertTrue(cmds.objExists(aaa))

        self.assertFalse(cmds.objExists(bbb))
        bbb = boo + ':' + bbb
        self.assertTrue(cmds.objExists(bbb))

        ccc = ':' + ccc
        self.assertTrue(cmds.objExists(ccc))

        self.assertFalse(cmds.objExists(ddd))
        ddd = woo + ':' + ddd
        self.assertTrue(cmds.objExists(ddd))

        self.assertEqual(boo, ':boo')
        self.assertEqual(foo, ':boo:foo')
        self.assertEqual(woo, ':boo:woo')

        self.assertEqual(boo.relative(), 'boo')
        self.assertEqual(foo.relative(), 'boo:foo')
        self.assertEqual(woo.relative(), 'boo:woo')

        self.assertEqual(boo.parent(), ':')
        self.assertEqual(boo.children(), [foo, woo])
        self.assertEqual(foo.parent(), boo)
        self.assertEqual(woo.parent(), boo)

        tmp = Namespace(foo + ':tmp')
        with RelativeNS(tmp):
            self.assertEqual([str(x) for x in boo.ls()], [aaa, bbb])
            self.assertEqual([str(x) for x in foo.ls()], [ccc])
            self.assertEqual([str(x) for x in woo.ls()], [ddd])

        self.assertEqual([str(x) for x in boo.ls()], [aaa[1:], bbb[1:]])
        self.assertEqual([str(x) for x in foo.ls()], [ccc[1:]])
        self.assertEqual([str(x) for x in woo.ls()], [ddd[1:]])

        root = Namespace(':')
        self.assertEqual(list(root.iterBreadthFirst()), [root, boo, foo, woo, tmp])
        self.assertEqual(list(root.iterDepthFirst()), [root, boo, foo, tmp, woo])


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
