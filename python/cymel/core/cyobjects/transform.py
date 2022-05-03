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

    def addChild(self, child, r=False, add=False, avoidJointShear=False, unmaintainIS=False):
        u"""
        子ノードを追加する。複数指定可能。

        :param child:
            子にするノードの `.DagNode` や名前や、それらのリスト。
        :param `bool` r:
            現在のローカル変換を維持するかどうか。
            デフォルトではワールド空間で維持される。
        :param `bool` add:
            移動ではなくパスを追加する（インスタンス）。
        :param `bool` avoidJointShear:
            追加する子が joint で、ワールド姿勢の維持のために shear
            が必要な場合に、その使用を避けるための transform が
            追加されるようにする。
            これは本来の Maya の挙動だが、このメソッドのデフォルトでは
            joint の shear を使用することで transform を追加しない。
        :param `bool` unmaintainIS:
            このノードが joint の場合に inverseScale 接続・切断の
            保守をしない。
        """
        name = self.name()

        # 子のシーケンスが指定された場合。
        if isinstance(child, Sequence) and not isinstance(child, BASESTR):
            others = [str(x) for x in child]
            shapes = _ls(others, type='shape')
            # シェイプはまとめて処理してしまう。
            if shapes:
                shapeSet =set(shapes)
                others = [x for x in others if x not in shapeSet]
                _parent(shapes, name, s=True, r=True, add=add)
            # その他は順番に処理する。
            if others:
                if add or ((avoidJointShear or not r) and bool(r) is bool(unmaintainIS)) or not _ls(others, type='joint'):
                    _parent(others, name, r=r, add=add)
                else:
                    for child in others:
                        child = CyObject(child)
                        if child.isJoint():
                            child._DagNode__setJointParent(self, not r, not unmaintainIS, avoidJointShear)
                        else:
                            _parent(child.name_(), name, r=r, add=add)

        # 単一の子が指定された場合。
        else:
            child = CyObject(child)
            if child.isShape():
                _parent(child.name_(), name, s=True, r=True, add=add)
            elif add or not child.isJoint() or ((avoidJointShear or not r) and bool(r) is bool(unmaintainIS)):
                _parent(child.name_(), name, r=r, add=add)
            else:
                child._DagNode__setJointParent(self, not r, not unmaintainIS, avoidJointShear)

nodetypes.registerNodeClass(Transform, 'transform')

