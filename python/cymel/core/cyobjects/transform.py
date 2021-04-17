# -*- coding: utf-8 -*-
u"""
:mayanode:`transform` ノードタイプラッパークラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ..typeregistry import nodetypes, _FIX_SLOTS
from .transform_c import TransformMixin
from .cyobject import CyObject, BIT_DAGNODE, BIT_TRANSFORM

__all__ = ['Transform']

_parent = cmds.parent
_ls = cmds.ls


#------------------------------------------------------------------------------
class Transform(TransformMixin, nodetypes.parentBasicNodeClass('transform')):
    u"""
    :mayanode:`transform` ノードタイプラッパークラス。
    """
    if _FIX_SLOTS:
        __slots__ = tuple()

    TYPE_BITS = BIT_DAGNODE | BIT_TRANSFORM  #: クラスでサポートしているノードの特徴を表す。

    def addChild(self, child, r=False, add=False):
        u"""
        子ノードを追加する。複数指定可能。

        :param child:
            子にするノードの `.DagNode` や名前や、それらのリスト。
        :param `bool` r:
            現在のローカル変換を維持するかどうか。
            デフォルトではワールド空間で維持される。
        :param `bool` add:
            移動ではなくパスを追加する（インスタンス）。
        """
        parent = self.name()
        if isinstance(child, Sequence) and not isinstance(child, BASESTR):
            others = [str(x) for x in child]
            shapes = _ls(others, type='shape')
            if shapes:
                shapeSet =set(shapes)
                others = [x for x in x not in shapeSet]
                _parent(shapes, parent, s=True, r=True, add=add)
            if others:
                _parent(others, parent, r=r, add=add)
        else:
            child = CyObject(child)
            if child.isShape():
                _parent(child, parent, s=True, r=True, add=add)
            else:
                _parent(child, parent, r=r, add=add)

nodetypes.registerNodeClass(Transform, 'transform')

