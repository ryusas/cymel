# -*- coding: utf-8 -*-
u"""
:mayanode:`dagNode` ノードタイプラッパークラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ..typeregistry import nodetypes, _FIX_SLOTS
from .cyobject import CyObject, BIT_DAGNODE
from .dagnode_c import DagNodeMixin

__all__ = ['DagNode']

_setAttr = cmds.setAttr
_parent = cmds.parent


#------------------------------------------------------------------------------
class DagNode(DagNodeMixin, nodetypes.parentBasicNodeClass('dagNode')):
    u"""
    :mayanode:`dagNode` ノードタイプラッパークラス。
    """
    if _FIX_SLOTS:
        __slots__ = tuple()

    TYPE_BITS = BIT_DAGNODE  #: クラスでサポートしているノードの特徴を表す。

    def show(self):
        u"""
        visibility アトリビュートを True にする。
        """
        _setAttr(self.name() + '.v', True)

    def hide(self):
        u"""
        visibility アトリビュートを False にする。
        """
        _setAttr(self.name() + '.v', False)

    def setParent(self, parent=None, r=False, add=False, avoidJointShear=False, unmaintainIS=False):
        u"""
        親ノードを変更する。

        :param parent:
            親の `.Transform` や名前。省略すればペアレント解除。
        :param `bool` r:
            現在のローカル変換を維持するかどうか。
            デフォルトではワールド空間で維持される。
        :param `bool` add:
            移動ではなくパスを追加する（インスタンス）。
        :param `bool` avoidJointShear:
            このノードが joint で、ワールド姿勢の維持のために shear
            が必要な場合に、その使用を避けるための transform が
            追加されるようにする。
            これは本来の Maya の挙動だが、このメソッドのデフォルトでは
            joint の shear を使用することで transform を追加しない。
        :param `bool` unmaintainIS:
            このノードが joint の場合に inverseScale 接続・切断の
            保守をしない。

        .. warning::
            2019 全てと 2020.0 では、joint の shear は機能しないため、
            avoidJointShear=True を指定しないと姿勢を維持できない場合がある。
            この問題は 2020.1 以降はバグとして修正されている。
        """
        # shape なら普通にやるだけだが、parent 無しにはできない。
        if self.isShape():
            if parent:
                _parent(self.name(), parent, s=True, r=True, add=add)
            else:
                raise RuntimeError('A shape cannot be ungrouped.')

        # joint でないか r=True が不要なら、普通にやるだけ。
        elif add or not self.isJoint() or ((avoidJointShear or not r) and bool(r) is bool(unmaintainIS)):
            # r=True,  unmaintainIS=True,  avoidJointShear=False : 普通に r=True でやる (pose も is も維持されない)
            # r=True,  unmaintainIS=True,  avoidJointShear=True  : 普通に r=True でやる (pose も is も維持されない)
            # r=False, unmaintainIS=False, avoidJointShear=True  : 普通に r=False でやる (transform追加で is も維持)
            if parent:
                _parent(self.name(), parent, r=r, add=add)
            else:
                _parent(self.name(), w=True, r=r, add=add)

        # joint で r=True が必要な場合は厄介（avoidJointShear=False の場合も r=True 扱い）。
        else:
            # r=False, unmaintainIS=True,  avoidJointShear=True  : transform追加で is 維持は無し -> 非サポート
            # r=False, unmaintainIS=False, avoidJointShear=False : maintainM=1, maintainIS=1
            # r=False, unmaintainIS=True,  avoidJointShear=False : maintainM=1, maintainIS=0
            # r=True,  unmaintainIS=False, avoidJointShear=False : maintainM=0, maintainIS=1
            # r=True,  unmaintainIS=False, avoidJointShear=True  : maintainM=0, maintainIS=1
            self.__setJointParent(parent and CyObject(parent), not r, not unmaintainIS, avoidJointShear)

    def __setJointParent(self, parent, maintainM, maintainIS, avoidSh):
        # 元の姿勢を取得。
        if maintainM:
            if avoidSh:
                raise ValueError(
                    'Unsupported option value combinations: r=%r, unmaintainIS=%r, avoidJointShear=%r' %
                    (not maintainM, not maintainIS, avoidSh))
            m = self.getM(ws=True)

        # 元の is の入力と標準的なものかどうかを判定。
        if maintainIS:
            srcIS = self.plug_('is').inputs()
            if srcIS:
                srcIS = srcIS[0]
                if srcIS.shortName() == 's':
                    curParent = self.parent()
                    maintainIS = srcIS.node() == curParent and curParent.isJoint()
                else:
                    maintainIS = False
            else:
                curParent = self.parent()
                maintainIS = not curParent or not curParent.isJoint()

        # parent 処理。r=True を指定すると is の切断や接続の処理がされない。
        if parent:
            _parent(self.name(), parent, r=True)
        else:
            _parent(self.name_(), w=True, r=True)

        # 元の is が標準的なものだった場合、新しい親に対処する。
        if maintainIS:
            if parent and parent.isJoint():
                self.plug_('is').connect(parent.s, force=True)
            elif srcIS:
                self.plug_('is').disconnect(srcIS, force=True)

        # 姿勢を維持。
        if maintainM:
            self.setM(m, ws=True)

    def iterBreadthFirst(self, shapes=False, intermediates=False, underWorld=False):
        u"""
        DAGノードツリーを幅優先反復する。

        :param `bool` shapes: シェイプも含めるかどうか。
        :param `bool` intermediates:
            インターミディエイトオブジェクトも含めるかどうか。
        :param `bool` underWorld:
            アンダーワールドノード（カーブオンサーフェース等）も含めるかどうか。
        :rtype: yeild `DagNode`
        """
        isShape = self.isShape()
        if shapes or not isShape:
            nodes = [self]
        elif underWorld and isShape:
            nodes = self.underWorldNodes()
            if not intermediates:
                nodes = [x for x in nodes if not x.isIntermediateObject()]
        else:
            return

        while nodes:
            queue = nodes
            nodes = []
            for node in queue:
                yield node
                if underWorld and (not shapes or node.isShape()):
                    if intermediates:
                        nodes.extend(node.underWorldNodes())
                    else:
                        nodes.extend([x for x in node.underWorldNodes() if not x.isIntermediateObject()])
                nodes.extend(node.children(shapes, intermediates))

    def iterDepthFirst(self, shapes=False, intermediates=False, underWorld=False):
        u"""
        DAGノードツリーを深さ優先反復する。

        :param `bool` shapes: シェイプも含めるかどうか。
        :param `bool` intermediates:
            インターミディエイトオブジェクトも含めるかどうか。
        :param `bool` underWorld:
            アンダーワールドノード（カーブオンサーフェース等）も含めるかどうか。
        :rtype: yeild `DagNode`
        """
        isShape = self.isShape()
        if shapes or not isShape:
            yield self

        if underWorld and (not shapes or isShape):
            queue = self.underWorldNodes()
            if not intermediates:
                queue = [x for x in queue if not x.isIntermediateObject()]
            queue.extend(self.children(shapes, intermediates))
        else:
            queue = self.children(shapes, intermediates)

        for node in queue:
            for node in node.iterDepthFirst(shapes, intermediates, underWorld):
                yield node

    # TODO: findCommonAncestor
    # TODO: iterPath

nodetypes.registerNodeClass(DagNode, 'dagNode')

