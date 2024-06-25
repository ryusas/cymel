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

__all__ = ['Constraint']


#------------------------------------------------------------------------------
class Constraint(nodetypes.parentBasicNodeClass('constraint')):
    u"""
    :mayanode:`constraint`
    """
    if _FIX_SLOTS:
        __slots__ = ('_cmd',)

    @classmethod
    def newObject(cls, data):
        obj = super(Constraint, cls).newObject(data)
        obj._cmd = getattr(cmds, obj.type())
        return obj

    def _getTargetList(self):
        """Return the list of target objects.

        :rtype: list[str]
        """
        return self._cmd(self, targetList=True, q=True) or []

    def getTargetList(self):
        """Return the list of target objects.

        :rtype: list[Constraint]
        """
        return list(map(CyObject, self._getTargetList()))

    def getWeightAliasList(self):
        """
        Returns the names of the attributes that control the weight of the target objects.
        Aliases are returned in the same order as the targets are returned by the targetList flag

        :rtype: list[str]
        """
        return self._cmd(self, weightAliasList=True, q=True) or []

    def getWeightPlugList(self):
        """
        Returns the plug that control the weight of the target objects.
        Plugs are returned in the same order as the targets are returned by the targetList flag

        :rtype: list[plug]
        """
        return list(
            map(
                self.plug_,
                self._cmd(self, weightAliasList=True, q=True) or []
            )
        )

    def setWeight(self, weight, *targetObjects):
        """
        Sets the weight value for the specified targetObject(s).
        if targetObjects are not provided, this will set weights for all targets

        :param float weight: weight value to set for given target
        :param targetObjects: target nodes of this constraint
        """
        if targetObjects:
            self._cmd(targetObjects + (self,), e=True, weight=weight)
        else:
            targetObjects = self._getTargetList()
            if targetObjects:
                self._cmd(targetObjects + [self.name_()], e=True, weight=weight)

    def getWeight(self, *targetObjects):
        """
        Returns the weight value for the specified targetObject(s).
        if targetObjects are not provided, this will get weights of all targets

        :param targetObjects: target nodes of this constraint

        :rtype: float or list[float]
        """
        if targetObjects:
            return self._cmd(targetObjects + (self,), q=True, weight=True)
        else:
            targetObjects = self._getTargetList()
            if targetObjects:
                return self._cmd(targetObjects + [self.name_()], q=True, weight=True)
            return targetObjects


nodetypes.registerNodeClass(Constraint, 'constraint')
