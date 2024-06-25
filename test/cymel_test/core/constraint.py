# -*- coding: utf-8 -*-
u"""
constraint related tests
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

    def setUp(self):
        cmds.file(f=True, new=True)

        # given
        self.a = cmds.createNode('transform', ss=1)
        self.b = cmds.createNode('transform', ss=1)
        self.c = cmds.createNode('transform', ss=1)

    def test_Constraint_constraint_node_can_initialize_with_Constraint_class(self):
        con = cmds.parentConstraint(self.a, self.b)[0]
        conObj = cm.nt.Constraint(con)
        self.assertIsInstance(
            conObj,
            cm.nt.Constraint
        )

    def test_Constraint_getWeight_returns_empty_list_if_target_doesnot_exists(self):
        con = cmds.createNode('parentConstraint')
        conObj = cm.nt.Constraint(con)
        self.assertEqual(
            conObj.getWeight(),
            []
        )

    def test_Constraint(self):

        # given
        a = self.a
        b = self.b
        c = self.c

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
            ['transform1W0', 'transform2W1']
        )

        # when
        aliases = conObj.getWeightPlugList()

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
