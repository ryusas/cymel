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


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
