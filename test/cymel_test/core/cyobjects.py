# -*- coding: utf-8 -*-
u"""
カスタムクラス関連のテスト。
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys
import unittest
import cymel.main as cm
import maya.cmds as cmds


#------------------------------------------------------------------------------
class MyTransform(cm.nt.Transform):
    @staticmethod
    def _verifyNode(mfn, name):
        return mfn.hasAttribute('myNodeTag')

    @classmethod
    def createNode(cls, **kwargs):
        nodename = super(MyTransform, cls).createNode(**kwargs)
        cmds.addAttr(nodename, ln='myNodeTag', at='message', h=True)
        return nodename


#------------------------------------------------------------------------------
class TestCyObjects(unittest.TestCase):
    u"""
    Test of CyObject.
    """
    def test_CustomClass(self):
        cmds.file(f=True, new=True)

        # Use without registration.
        obj = MyTransform(n='hoge')
        self.assertTrue(type(obj) is MyTransform)
        self.assertTrue(type(cm.sel) is cm.nt.Transform)

        # register.
        cm.nt.registerNodeClass(MyTransform, 'transform')

        # MyTransform
        obj = MyTransform(n='foo')
        self.assertTrue(type(obj) is MyTransform)
        self.assertTrue(type(cm.sel) is MyTransform)

        # transform
        obj = cm.nt.Transform(n='bar')
        self.assertTrue(type(obj) is cm.nt.Transform)
        self.assertTrue(type(cm.sel) is cm.nt.Transform)

        # Joint -> MyTransform
        obj = cm.nt.Joint(n='baz')
        obj.addAttr('myNodeTag', 'message', h=True)
        self.assertTrue(type(obj) is cm.nt.Joint)
        self.assertTrue(type(cm.sel) is MyTransform)

        # check type determination.
        self.assertTrue(type(cm.O('foo')) is MyTransform)
        self.assertTrue(type(cm.O('bar')) is cm.nt.Transform)
        self.assertTrue(type(cm.O('baz')) is MyTransform)

        # deregister.
        cm.nt.deregisterNodeClass(MyTransform)

        # checking type determination.
        self.assertTrue(type(cm.O('foo')) is cm.nt.Transform)
        self.assertTrue(type(cm.O('bar')) is cm.nt.Transform)
        self.assertTrue(type(cm.O('baz')) is cm.nt.Joint)

        # Use without registration.
        self.assertTrue(type(cm.sel) is MyTransform)

    def test_DagNode_findTopNodes(self):
        cmds.file(f=True, new=True)

        cmds.createNode('transform', n='rootA')
        cmds.createNode('transform', n='childA', p='rootA')
        cmds.createNode('transform', n='grandchildA', p='childA')
        cmds.createNode('transform', n='siblingA', p='rootA')
        cmds.createNode('transform', n='rootB')
        cmds.createNode('transform', n='childB', p='rootB')

        rootA = cm.O('|rootA')
        childA = cm.O('|rootA|childA')
        grandchildA = cm.O('|rootA|childA|grandchildA')
        siblingA = cm.O('|rootA|siblingA')
        rootB = cm.O('|rootB')
        childB = cm.O('|rootB|childB')

        findTopNodes = cm.nt.DagNode.findTopNodes
        self.assertEqual(findTopNodes([]), [])
        self.assertEqual(findTopNodes((childA,)), [childA])
        self.assertEqual(
            findTopNodes(x for x in (childB, siblingA)),
            [childB, siblingA])
        self.assertEqual(
            findTopNodes((childB, grandchildA, siblingA)),
            [childB, grandchildA, siblingA])
        self.assertEqual(
            findTopNodes((grandchildA, childA, rootA, rootB)),
            [rootA, rootB])
        self.assertEqual(
            findTopNodes((rootB, grandchildA, rootA)),
            [rootB, rootA])
        self.assertEqual(
            findTopNodes((grandchildA, childA, childA, grandchildA)),
            [childA])
        self.assertEqual(findTopNodes((rootA,), getParent=True), [])
        self.assertEqual(
            findTopNodes((x for x in (childA, siblingA)), getParent=True),
            [rootA])
        self.assertEqual(
            findTopNodes(
                (grandchildA, siblingA, childB), getParent=True),
            [rootA, rootB])
        self.assertEqual(
            findTopNodes(
                (childB, grandchildA, siblingA), getParent=True),
            [rootB, rootA])
        self.assertEqual(
            findTopNodes([], getParent=True, includeNone=True), [])
        self.assertEqual(
            findTopNodes((rootA,), getParent=True, includeNone=True),
            [None])
        self.assertEqual(
            findTopNodes(
                (rootA, rootB), getParent=True, includeNone=True),
            [None])
        self.assertEqual(
            findTopNodes(
                (x for x in (rootA, childB)),
                getParent=True, includeNone=True),
            [None, rootB])
        self.assertEqual(
            findTopNodes(
                (childB, rootA), getParent=True, includeNone=True),
            [rootB, None])
        self.assertEqual(
            findTopNodes((rootA, childB), includeNone=True),
            [rootA, childB])

        cmds.createNode('transform', n='instanceParentA')
        cmds.createNode('transform', n='instanceParentB')
        cmds.createNode('transform', n='instanceChild', p='instanceParentA')
        cmds.parent('|instanceParentA|instanceChild', 'instanceParentB', add=True)
        instanceParentA = cm.O('|instanceParentA')
        instanceChildA = cm.O('|instanceParentA|instanceChild')
        instanceChildB = cm.O('|instanceParentB|instanceChild')

        self.assertEqual(
            findTopNodes((instanceParentA, instanceChildA)),
            [instanceParentA])
        self.assertEqual(
            findTopNodes((instanceParentA, instanceChildB)),
            [instanceParentA, instanceChildB])
        self.assertEqual(
            findTopNodes(
                (instanceChildA, instanceChildB), getParent=True),
            [instanceParentA, cm.O('|instanceParentB')])
        self.assertEqual(
            findTopNodes(
                (instanceParentA, instanceChildB), getParent=True),
            [cm.O('|instanceParentB')])


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
