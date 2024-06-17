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

    def __init__(self, *args, **kwargs):
        super(Constraint, self).__init__()
        self._cmd = getattr(cmds, self.type())

    def _getTargetList(self):
        """Return the list of target objects.

        :rtype: list[str]
        """
        return self._cmd(self, targetList=True, q=True)

    def getTargetList(self):
        """Return the list of target objects.

        :rtype: list[Constraint]
        """
        return list(map(CyObject, self._getTargetList()))

    def getWeightAliasList(self):
        """
        Returns the names of the attributes that control the weight of the target objects.
        Aliases are returned in the same order as the targets are returned by the targetList flag

        :rtype: list
        """
        return list(
            map(
                self.plug_,
                self._cmd(self, weightAliasList=True, q=True)
            )
        )

    def setWeight(self, weight, *targetObjects):
        """
        Sets the weight value for the specified targetObject(s).
        """
        if targetObjects:
            self._cmd(targetObjects + (self,), e=True, weight=weight)
        else:
            name = self.name()
            self._cmd(self._getTargetList() + [name], e=True, weight=weight)

    def getWeight(self, *targetObjects):
        """
        Returns the weight value for the specified targetObject(s).

        :rtype: float
        """
        if targetObjects:
            return self._cmd(targetObjects + (self,), q=True, weight=True)
        else:
            name = self.name()
            return self._cmd(self._getTargetList() + [name], q=True, weight=True)


nodetypes.registerNodeClass(Constraint, 'constraint')
