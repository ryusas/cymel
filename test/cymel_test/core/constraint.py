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


class TestConstraints(unittest.TestCase):
    u"""
    Test of Constraint.
    """
    def test_Constraint(self):
        cmds.file(f=True, new=True)

        # given
        a = cmds.createNode('transform', ss=1)
        b = cmds.createNode('transform', ss=1)
        c = cmds.createNode('transform', ss=1)

        for conType in [
            'parentConstraint',
            'pointConstraint',
            'orientConstraint',
            'scaleConstraint',
            'aimConstraint',
        ]:
            conCmd = getattr(cmds, conType)
            conName = conCmd(a, b, c)
            conObj = cm.O(conName[0])
            self._runAssertionsFor(conType, conObj)
            cmds.delete(conObj)

    def _runAssertionsFor(self, conType, conObj):
        # then
        self.assertIsInstance(
            conObj,
            cm.nt.Constraint
        )

        # when
        targets = conObj.getTargetList()

        # then
        self.assertListEqual(
            targets,
            [cm.nt.Transform('transform1'), cm.nt.Transform('transform2')]
        )

        # when
        aliases = conObj.getWeightAliasList()

        # then
        self.assertListEqual(
            aliases,
            [cm.Plug('transform3_{}1.w0'.format(conType)), cm.Plug('transform3_{}1.w1'.format(conType))]
        )

        # when
        conObj.setWeight(0.5)

        # then
        self.assertEqual(
            cmds.getAttr('transform3_{}1.w0'.format(conType)),
            0.5
        )
        self.assertEqual(
            cmds.getAttr('transform3_{}1.w1'.format(conType)),
            0.5
        )

        # when
        conObj.setWeight(0.75, 'transform1')

        # then
        self.assertEqual(
            cmds.getAttr('transform3_{}1.w0'.format(conType)),
            0.75
        )
        self.assertEqual(
            cmds.getAttr('transform3_{}1.w1'.format(conType)),
            0.5
        )

        self.assertEqual(
            conObj.getWeight(),
            [0.75, 0.5]
        )

        self.assertEqual(
            conObj.getWeight('transform1'),
            0.75
        )

        self.assertEqual(
            conObj.getWeight('transform2'),
            0.5
        )


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
