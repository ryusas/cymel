# -*- coding: utf-8 -*-
u"""
:mayanode:`dagNode` ノードタイプラッパークラス。
"""
from ...common import *
from ..typeregistry import nodetypes, _FIX_SLOTS
from .cyobject import BIT_DAGNODE
from .dagnode_c import DagNodeMixin

__all__ = ['DagNode']

_parent = cmds.parent


#------------------------------------------------------------------------------
class DagNode(DagNodeMixin, nodetypes.parentBasicNodeClass('dagNode')):
    u"""
    :mayanode:`dagNode` ノードタイプラッパークラス。
    """
    if _FIX_SLOTS:
        __slots__ = tuple()

    TYPE_BITS = BIT_DAGNODE  #: クラスでサポートしているノードの特徴を表す。

    def setParent(self, parent=None, r=False, add=False):
        u"""
        親ノードを変更する。

        :param parent:
            親の `.Transform` や名前。省略すればペアレント解除。
        :param `bool` r:
            現在のローカル変換を維持するかどうか。
            デフォルトではワールド空間で維持される。
        :param `bool` add:
            移動ではなくパスを追加する（インスタンス）。
        """
        if parent:
            if self.isShape():
                _parent(self.name(), parent, s=True, r=True, add=add)
            else:
                _parent(self.name(), parent, r=r, add=add)
        else:
            if self.isShape():
                raise RuntimeError('A shape cannot be ungrouped.')
            _parent(self.name(), w=True, r=r, add=add)

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

