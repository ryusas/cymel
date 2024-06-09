# -*- coding: utf-8 -*-
u"""
:mayanode:`constraint`
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ..typeregistry import nodetypes, _FIX_SLOTS
from .cyobject import CyObject
import maya.api.OpenMaya as _api2
import itertools

__all__ = ['Constraint']

_from_iterable = itertools.chain.from_iterable

_MFn_kDagNode = _api2.MFn.kDagNode
_MFn_kTransform = _api2.MFn.kTransform
_MFn_kConstraint = _api2.MFn.kConstraint
_2_MDagPath = _api2.MDagPath
_2_getAllPathsTo = _2_MDagPath.getAllPathsTo
_2_NullObj = _api2.MObject.kNullObj


#------------------------------------------------------------------------------
class Constraint(nodetypes.parentBasicNodeClass('constraint')):
    u"""
    :mayanode:`constraint`
    """
    if _FIX_SLOTS:
        __slots__ = tuple()

    def getTargetList(self):
        """Return the list of target objects.

        :rtype: list
        """
        inFunc = getattr(cmds, self.type())
        return [CyObject(obj) for obj in inFunc(self, targetList=True, q=True)]

    def getWeightAliasList(self):
        """
        Returns the names of the attributes that control the weight of the target objects.
        Aliases are returned in the same order as the targets are returned by the targetList flag

        :rtype: list
        """
        inFunc = getattr(cmds, self.type())
        return [CyObject('{}.{}'.format(self.name(), obj)) for obj in inFunc(self, weightAliasList=True, q=True)]

    def setWeight(self, weight, *targetObjects):
        """
        Sets the weight value for the specified targetObject(s).
        """
        inFunc = getattr(cmds, self.type())
        if not targetObjects:
            targetObjects = self.getTargetList()

        constraintObj = self.constraintParentInverseMatrix.inputs()[0].node()
        args = list(targetObjects) + [constraintObj]
        return inFunc(*args, **{'edit': True, 'weight': weight})

    def getWeight(self, *targetObjects):
        """
        Returns the weight value for the specified targetObject(s).

        :rtype: float
        """
        inFunc = getattr(cmds, self.type())
        if not targetObjects:
            targetObjects = self.getTargetList()

        constraintObj = self.constraintParentInverseMatrix.inputs()[0].node()
        args = list(targetObjects) + [constraintObj]
        return inFunc(*args, **{'query': True, 'weight': True})


nodetypes.registerNodeClass(Constraint, 'constraint')
