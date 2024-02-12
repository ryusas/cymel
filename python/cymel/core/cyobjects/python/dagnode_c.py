# -*- coding: utf-8 -*-
u"""
`.DagNode` クラスでサポートする機能の中核。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from .cyobject import _newNodeObjByMPath
from .objectref import _getObjectRef
from ._api2mplug import mplug_get_nums, mplug_get_xformmatrix
from ..datatypes.boundingbox import _newBB
from ..datatypes.matrix import _newM, ImmutableMatrix
from ..datatypes.quaternion import _newQ
from ..datatypes.vector import _newV
from ..datatypes.transformation import _newX
from ..datatypes import E
import maya.api.OpenMaya as _api2

__all__ = []

_REVERSE_RO = E.REVERSE_ORDER

_MFn = _api2.MFn
_2_MDagPath = _api2.MDagPath
_2_MFnDagNode = _api2.MFnDagNode
_MX = _api2.MTransformationMatrix
_MM = _api2.MMatrix
_MQ = _api2.MQuaternion
_ME = _api2.MEulerRotation
_MP = _api2.MPoint
_MV = _api2.MVector
if MAYA_VERSION >= (2016, 5):
    _2_MItDag = _api2.MItDag

_MFn_kTransform = _MFn.kTransform
_MFn_kShape = _MFn.kShape
_MFn_kJoint = _MFn.kJoint
_2_getAllPathsTo = _2_MDagPath.getAllPathsTo
_2_getAPathTo = _2_MDagPath.getAPathTo
_MSpace_kTransform = _api2.MSpace.kTransform


#------------------------------------------------------------------------------
class DagNodeMixin(object):
    u"""
    `.DagNode` クラスでサポートする機能の中核。
    """
    __slots__ = tuple()

    def isIntermediateObject(self):
        u"""
        インターミディエイトオブジェクトかどうか。

        :rtype: `bool`
        """
        return self.mfn().isIntermediateObject

    def objectColor(self):
        u"""
        設定されているオブジェクトカラーを得る。

        :rtype: `int`
        """
        return self.mfn().objectColor

    def useObjectColor(self):
        u"""
        オブジェクトカラーが使用される設定になっているかどうか。

        :rtype: `bool`
        """
        return self.mfn().useObjectColor

    def isVisible(self):
        u"""
        可視性を得る。

        :rtype: `bool`
        """
        return self._mpath().isVisible()

    def isTemplated(self):
        u"""
        テンプレート化されているかどうか。

        :rtype: `bool`
        """
        return self._mpath().isTemplated()

    def partialPath(self):
        u"""
        パーシャルパス名を得る。

        `~.CyObject.name` と同じ。

        :rtype: `str`
        """
        return self._mpath().partialPathName()

    def fullPath(self):
        u"""
        フルパス名を得る。

        :rtype: `str`
        """
        return self._mpath().fullPathName()

    def isRoot(self):
        u"""
        ルートノードかどうか。

        :rtype: `bool`
        """
        return self._mpath().length() == 1

    def root(self):
        u"""
        DAGパスに沿ったルートノードを得る。

        自身がルートノードなら同じ参照が返される。

        API の :mayaapi2:`MDagPath` の dagRoot() とは異なり、
        見えない『ワールド』ノードではなく、
        シーン上のルートノードが得られる。

        :rtype: `.Transform` or None
        """
        orig = self._mpath()
        d = orig.length() - 1
        return _newNodeObjByMPath(_2_MDagPath(orig).pop(d)) if d else self

    def allRoots(self):
        u"""
        このノードインスタンスを階層下に持つ全ルートノードのリストを得る。

        自身がルートノードなら同じ参照が返される。

        :rtype: `list`
        """
        orig = self._mpath()
        if orig.length() == 1:
            # ルートノードは他にインスタンスが在ることは有り得ないようだ。
            return [self]

        # NOTE: inUnderWorld だと (MDagPath|MFnDagNode).isInstanced は正常動作するが MFnDagNode.instanceCount は常に 1 となる。
        if orig.isInstanced():  # indirect も含んだ判定。
            mpaths = []
            for x in _2_getAllPathsTo(orig.node()):
                # NOTE: getAllPathsTo で得たものをそのまま使うとクラッシュすることがあるので複製。
                x = _2_MDagPath(x).pop(x.length() - 1)
                if x not in mpaths:
                    mpaths.append(x)
            return [_newNodeObjByMPath(x) for x in mpaths]
        else:
            return [_newNodeObjByMPath(_2_MDagPath(orig).pop(orig.length() - 1))]

    def leaves(self):
        u"""
        階層下のリーフノードのリストを得る。

        アンダーワールドノード（カーブオンサーフェース等）に
        下ることはされない。

        :rtype: `list`
        """
        leaves = []
        orig = self._mpath()
        mpaths = [orig]
        while mpaths:
            queue = mpaths
            mpaths = []
            for mpath in queue:
                num = mpath.childCount()
                if num:
                    mpaths.extend([_2_MDagPath(mpath).push(mpath.child(i)) for i in range(num)])
                else:
                    leaves.append(mpath)

        if len(leaves) == 1 and leaves[0] is orig:
            return [self]
        return [_newNodeObjByMPath(x) for x in leaves]

    def siblings(self):
        u"""
        自分以外の兄弟ノードのリストを返す。

        :rtype: `list`
        """
        parent = self.mpath().pop()
        num = parent.childCount()
        if num > 1:
            get = parent.child
            mobjs = [get(i) for i in range(num)]
            mnode = self.mnode_()
            return [_newNodeObjByMPath(_2_MDagPath(parent).push(x)) for x in mobjs if x != mnode]
        return []

    def siblingIndex(self):
        u"""
        兄弟におけるインデックスを得る。

        :rtype: `int`
        """
        parent = self.mpath().pop()
        num = parent.childCount()
        if num > 1:
            return _indexOfArr(self.mnode_(), parent.child, num)
        return 0

    def siblingIndices(self):
        u"""
        DAGパス中の全ノードの兄弟インデックスリストを得る。

        :rtype: `list`

        .. note::
            ノードリストをソートするキー関数として利用すると、
            DAG階層の深さ優先ソートとなる。

            幅優先なら `lengthAndSiblingIndices` を
            兄弟順保証しない幅優先なら `pathLength` を使うと良い。
        """
        result = []
        mpath = self._mpath()
        pathLen = mpath.length()

        if self.mfn_().inUnderWorld:
            while pathLen:
                parent = _2_MDagPath(mpath).pop()
                num = parent.childCount()
                if num > 1:
                    result.append(_indexOfArr(mpath.node(), parent.child, num))
                else:
                    result.append(0)

                if _2_MFnDagNode(parent).inModel:
                    mpath = parent
                    pathLen -= 1
                else:
                    # 着目している親が『ワールド』ノードの場合、次はそれをスキップ。
                    mpath = parent.pop()
                    pathLen -= 2
        else:
            while pathLen:
                parent = _2_MDagPath(mpath).pop()
                num = parent.childCount()
                if num > 1:
                    result.append(_indexOfArr(mpath.node(), parent.child, num))
                else:
                    result.append(0)
                mpath = parent
                pathLen -= 1

        result.reverse()
        return result

    def lengthAndSiblingIndices(self):
        u"""
        DAGパスを構成するノード数と、兄弟インデックスリストのペアを得る。

        :rtype: (int, `list`)

        .. note::
            ノードリストをソートするキー関数として利用すると、
            DAG階層の幅優先ソートとなる。

            兄弟順保証が不要なら `pathLength` を、
            深さ優先なら `siblingIndices` を利用する良い。
        """
        k = self.siblingIndices()
        return len(k), k

    def pathLength(self):
        u"""
        DAGフルパスの長さを得る。

        カーブオンサーフェースと親シェイプとの間に存在する
        シーン上では見えない『ワールド』ノードはカウントされないため、
        API の :mayaapi2:`MDagPath` の length() とは異なる。

        :rtype: `int`

        .. note::
            ノードリストをソートするキー関数として利用すると、
            DAG階層の兄弟順保証無しの幅優先ソートとなる。

            兄弟順保証するなら `lengthAndSiblingIndices` を
            深さ優先なら `siblingIndices` を利用すると良い。
        """
        orig = self._mpath()
        num = orig.length()
        if num >= 3 and self.mfn_().inUnderWorld:
            #return num - 1
            # 二重以上の UnderWorld が無いなら num - 1 で良いのだが、念のため not inModel の数だけ削減する。
            if num < 5:
                return num - 1
            mpath = _2_MDagPath(orig).pop()
            mfn = _2_MFnDagNode(mpath)
            while mfn.inUnderWorld:
                if not mfn.inModel:
                    num -= 1
                mpath.pop()
                mfn = _2_MFnDagNode(mpath)
        return num

    def numParents(self, indirect=False):
        u"""
        このノードインスタンスを子に持つ親ノードの数を得る。

        :param `bool` indirect:
            インスタンスポイント以外も含まれる親のパス全てを得る。
        :rtype: `int`
        """
        return self.numInstances() if indirect else self.mfn().parentCount()

    def parents(self, indirect=False):
        u"""
        このノードインスタンスを子に持つ親ノードのリストを得る。

        :param `bool` indirect:
            インスタンスポイント以外も含まれる親のパス全てを得る。
        :rtype: `list`
        """
        # ルートノードなら親は無し。
        orig = self._mpath()
        if orig.length() < 2:
            return []

        # このパス上の親を取得。
        mfn = self.mfn_()
        if self.isShape():
            parent = self._transform()
        else:
            mpath = _2_MDagPath(orig).pop()
            if mfn.inUnderWorld:
                if not _2_MFnDagNode(mpath).inModel:
                    mpath.pop()
            parent = _newNodeObjByMPath(mpath)

        # インスタンスポイント以外の全パスを得るなら、このノードの全パスの親を得る。
        if indirect:
            # インスタンスが1つなら親も1つ。
            if not orig.isInstanced():  # indirectも含んだ判定。
                return [parent]
            idx = orig.instanceNumber()
            return [
                parent if i == idx else _newNodeObjByMPath(_getParentPath(x))
                for i, x in enumerate(_2_getAllPathsTo(self.mnode_()))
            ]

        # インスタンスポイントにおける親ノードを得るなら mfn から得る。
        else:
            # インスタンス数が複数でもインスタンスポイントでなければ、親は1つとなる。
            num = mfn.parentCount()
            if num == 1:
                return [parent]

            # 親が複数の場合、このパス上でない親は getAPathTo に任せる。
            mobjs = [mfn.parent(i) for i in range(num)]
            mnode = parent.mnode_()
            return [
                parent if x == mnode else _newNodeObjByMPath(_2_getAPathTo(x))
                for x in mobjs]

    def parent(self, step=1):
        u"""
        DAGパスに沿った親ノードを得る。

        アンダーワールドノード（カーブオンサーフェース等）から
        親シェイプを得ることもできる。

        :param `int` step:
            遡るノード数。
            API の :mayaapi2:`MDagPath` の pop とは異なり、
            カーブオンサーフェースと親シェイプとの間に存在する
            シーン上では見えない『ワールド』ノードはカウントしない。
        :rtype: `.DagNode` or None
        """
        if step > 0:
            self.checkValid()
            if step == 1 and self.isShape():
                # shape の親を得るなら _transform メソッドを呼ぶ。
                return self._transform()
            orig = self._mpath_()
            if self.mfn_().inUnderWorld:
                if step < orig.length() - 1:
                    mpath = _2_MDagPath(orig).pop()
                    mfn = _2_MFnDagNode(mpath)
                    while mfn.inUnderWorld:
                        if mfn.inModel:
                            if step == 1:
                                break
                            step -= 1
                        mpath.pop()
                        mfn = _2_MFnDagNode(mpath)
                    step -= 1
                    if step:
                        mpath.pop(step)
                    return _newNodeObjByMPath(mpath)
            else:
                if step < orig.length():
                    return _newNodeObjByMPath(_2_MDagPath(orig).pop(step))

    def numChildren(self, shapes=False, intermediates=False):
        u"""
        DAGパス上の子ノードの数を得る。

        :param `bool` shapes:
            シェイプも含めるかどうか。
        :param `bool` intermediates:
            shapes=True のとき、さらに
            インターミディエイトオブジェクトも含めるかどうか。
        :rtype: `int`
        """
        if self.isTransform():
            if shapes and intermediates:
                return self._mpath().childCount()
            num = 0
            orig = self._mpath()
            get = orig.child
            for i in range(orig.childCount()):
                mobj = get(i)
                if (
                    (shapes or not mobj.hasFn(_MFn_kShape)) and
                    (intermediates or not _2_MFnDagNode(mobj).isIntermediateObject)
                ):
                    num += 1
            return num
        return 0

    def children(self, shapes=False, intermediates=False):
        u"""
        DAGパス上の子ノードのリストを得る。

        シェイプからアンダーワールドノード（カーブオンサーフェース等）を
        得ることはできないため、その場合は `underWorldNodes` を利用すること。

        :param `bool` shapes:
            シェイプも含めるかどうか。
        :param `bool` intermediates:
            shapes=True のとき、さらに
            インターミディエイトオブジェクトも含めるかどうか。
        :rtype: `list`
        """
        if not self.isTransform():
            return []

        if shapes:
            return self.__getShapes(intermediates, True)

        orig = self._mpath()
        get = orig.child
        return [
            _newNodeObjByMPath(_2_MDagPath(orig).push(o))
            for o in [get(i) for i in range(orig.childCount())]
            if not o.hasFn(_MFn_kShape) and
            (intermediates or not _2_MFnDagNode(o).isIntermediateObject)
        ]

    def child(self, idx, shapes=False, intermediates=False):
        u"""
        インデックス指定で子ノードを1つ得る。

        シェイプからアンダーワールドノード（カーブオンサーフェース等）を
        得ることはできないため、その場合は `underWorldNodes` を利用すること。

        :param `int` idx:
            インデックス。
            shapes や intermediates オプションによって、
            同じインデックスでも得られるものが変わることがある。
            無効なインデックスを指定するとエラーではなく None となる。
        :param `bool` shapes:
            シェイプも含めるかどうか。
        :param `bool` intermediates:
            shapes=True のとき、さらに
            インターミディエイトオブジェクトも含めるかどうか。
        :rtype: `.DagNode` or None
        """
        if not self.isTransform():
            return

        orig = self._mpath()
        get = orig.child

        # シェイプを含める場合はキャッシュと同期する。
        if shapes:
            # インターミディエイトを含める場合は、直接インデックス指定で得て、
            # それがシェイプの場合にシェイプとの同期を処理する。
            if intermediates:
                # まず、直接得て、シェイプでなければそれを返す。
                try:
                    mobj = get(idx)
                except:
                    return
                if not mobj.hasFn(_MFn_kShape):
                    return _newNodeObjByMPath(_2_MDagPath(orig).push(mobj))

                # シェイプだった場合は、キャッシュ用のシェイプインデックスを調べて同期する。
                k0 = 0  # not intermediate
                k1 = 0  # all
                for i in range(orig.childCount()):
                    mobj = get(i)
                    if mobj.hasFn(_MFn_kShape):
                        if i == idx:
                            return self._Node_c__getShapeWithCache(k0, k1, mobj)
                        if not _2_MFnDagNode(mobj).isIntermediateObject:
                            k0 += 1
                        k1 += 1

            # インターミディエイトを含めない場合は、どのみち直接インデックス指定では得られないので、
            # 子をトラバースして、インデックスを調べつつ、それがシェイプなら同期する。
            else:
                k0 = 0  # not intermediate
                k1 = 0  # all
                for i in range(orig.childCount()):
                    mobj = get(i)
                    if _2_MFnDagNode(mobj).isIntermediateObject:
                        if mobj.hasFn(_MFn_kShape):
                            k1 += 1
                    else:
                        if not idx:
                            if mobj.hasFn(_MFn_kShape):
                                return self._Node_c__getShapeWithCache(k0, k1, mobj)
                            else:
                                return _newNodeObjByMPath(_2_MDagPath(orig).push(mobj))
                        if mobj.hasFn(_MFn_kShape):
                            k0 += 1
                            k1 += 1
                        idx -= 1

        # シェイプを含めないなら、キャッシュとの同期を考える必要はない。
        else:
            for i in range(orig.childCount()):
                mobj = get(i)
                if (
                    (shapes or not mobj.hasFn(_MFn_kShape)) and
                    (intermediates or not _2_MFnDagNode(mobj).isIntermediateObject)
                ):
                    if not idx:
                        return _newNodeObjByMPath(_2_MDagPath(orig).push(mobj))
                    idx -= 1

    def isParentOf(self, node, exact=False, underWorld=True):
        u"""
        指定ノードの親かどうか検査する。

        直接の親に限らない上位ノードかどうかチェックする場合は
        `isAncestorOf` が利用できる。

        :type node: `.DagNode`
        :param node: チェックするノード。
        :param exact:
            インスタンス関係は考慮せず、DAGパスに沿った判定のみとするかどうか。
        :param `bool` underWorld:
            アンダーワールド（カーブオンサーフェース）の親シェイプも判定する。
        :rtype: `bool`
        """
        if exact:
            mpath = node.mpath().pop()
            if underWorld and not _2_MFnDagNode(mpath).inModel:
                mpath.pop()
            return mpath == self._mpath()

        else:
            mnode = self.mnode()
            node_fn = node.mfn()
            for i in range(node_fn.parentCount()):
                if node_fn.parent(i) == mnode:
                    return True
            if underWorld and node_fn.inUnderWorld:
                mpath = node.mpath_().pop()
                return not _2_MFnDagNode(mpath).inModel and mpath.pop().node() == mnode
            return False

    def isAncestorOf(self, node, exact=False, underWorld=True):
        u"""
        指定ノードの上位ノードかどうか検査する。

        直接の親かどうかをチェックする場合は
        `isParentOf` が利用できる。

        :type node: `.DagNode`
        :param node: チェックするノード。
        :param exact:
            インスタンス関係は考慮せず、DAGパスに沿った判定のみとするかどうか。
        :param `bool` underWorld:
            アンダーワールド（カーブオンサーフェース）の親シェイプも判定する。
        :rtype: `bool`
        """
        if exact:
            if underWorld or (self.mfn().inUnderWorld == node.mfn().inUnderWorld):
                self_mpath = self._mpath_()
                node_mpath = node._mpath_()
                n = node_mpath.length() - self_mpath.length()
                return n > 0 and self_mpath == _2_MDagPath(node_mpath).pop(n)
            return False

        else:
            self_fn = self.mfn()
            if self_fn.isParentOf(node.mnode()):
                return True
            if underWorld and not self_fn.inUnderWorld:
                node_fn = node.mfn_()
                if node_fn.inUnderWorld:
                    mnode = _2_getAPathTo(node_fn.dagRoot()).pop().node()
                    return self.mnode_() == mnode or self_fn.isParentOf(mnode)
            return False

    def inUnderWorld(self):
        u"""
        アンダーワールド（カーブオンサーフェース等）かどうか。

        :rtype: `bool`
        """
        return self.mfn().inUnderWorld

    def parentWorld(self):
        u"""
        アンダーワールド（カーブオンサーフェース等）における親空間シェイプを返す。

        本メソッドによって、カーブオンサーフェースから
        親のサーフェースシェイプを得ることができる。

        :rtype: `.Shape` or None
        """
        mfn = self.mfn()
        if mfn.inUnderWorld:
            mpath = self.mpath_().pop()
            root = mfn.dagRoot()  # シーン上には見えない『ワールド』ノード。
            while root != mpath.node():
                mpath.pop()
            return _newNodeObjByMPath(mpath.pop())

    if MAYA_VERSION >= (2016, 5):
        def hasUnderWorldNodes(self):
            u"""
            シェイプ下にアンダーワールドノード（カーブオンサーフェース等）を持つかどうか。

            :rtype: `bool`
            """
            shape = self.shape()
            if shape:
                it = _2_MItDag()
                it.reset(shape._mpath())
                it.traverseUnderWorld = True
                next(it)
                return not it.isDone() and not _2_MFnDagNode(it.getPath()).inModel
            return False

        def underWorldNodes(self):
            u"""
            シェイプ下のアンダーワールドノード（カーブオンサーフェース等）のリストを得る。

            :rtype: `list`
            """
            shape = self.shape()
            if shape:
                it = _2_MItDag()
                it.reset(shape._mpath())
                it.traverseUnderWorld = True
                next(it)
                if not it.isDone():
                    mpath = it.getPath()
                    if not _2_MFnDagNode(mpath).inModel:
                        get = mpath.child
                        return [_newNodeObjByMPath(_2_MDagPath(mpath).push(get(i))) for i in range(mpath.childCount())]
            return []

    def numShapes(self, intermediates=False):
        u"""
        :mayanode:`transform` の持つ :mayanode:`shape` ノード数を得る。

        :param `bool` intermediates:
            インターミディエイトオブジェクトも含めるかどうか。
        :rtype: `int`
        """
        if self.isTransform():
            if intermediates:
                num = 0
                orig = self._mpath()
                get = orig.child
                for i in range(orig.childCount()):
                    if get(i).hasFn(_MFn_kShape):
                        num += 1
                return num
            else:
                return self._mpath().numberOfShapesDirectlyBelow()
        return 0

    def shape(self, idx=0, intermediates=False):
        u"""
        :mayanode:`shape` ノードを得る。

        自身がシェイプの場合は自身が、
        :mayanode:`transform` の場合はそのシェイプが得られる。

        :param `int` idx:
            得たいシェイプのインデックス。
            自身がシェイプの場合は無視される。

            intermediates オプションによって、
            同じインデックスでも得られるものが変わることがある。
            無効なインデックスを指定するとエラーではなく None となる。

            Python的な負のインデックスも指定可能。
        :param `bool` intermediates:
            インターミディエイトオブジェクトも含めるかどうか。
        :rtype: `.Shape` or None
        """
        if self.isShape():
            return self
        elif self.isTransform():
            self.checkValid()
            return self._shape(idx, intermediates)

    def shapes(self, intermediates=False):
        u"""
        :mayanode:`transform` の持つ :mayanode:`shape` ノードのリストを得る。

        :param `bool` intermediates:
            インターミディエイトオブジェクトも含めるかどうか。
        :rtype: `list`
        """
        return self.__getShapes(intermediates) if self.isTransform() else []

    def __getShapes(self, intermediates=False, others=False):
        u"""
        子ノード群を得つつシェイプをキャッシュするための共通ルーチン。

        :param `bool` intermediates:
            インターミディエイトオブジェクトも含めるかどうか。
        :param `bool` others:
            シェイプ以外の子も含めるかどうか。
            ただし、キャッシュされるのはシェイプのみ。
        :rtype: `list`
        """
        # 子の MObject を収集。
        orig = self._mpath()
        get = orig.child
        allMObjs = [get(i) for i in range(orig.childCount())]
        if others:
            if intermediates:
                flagMObjs = [(o.hasFn(_MFn_kShape), o) for o in allMObjs]
                mfns = [_2_MFnDagNode(o) for f, o in flagMObjs if f]
            else:
                flagMFns = [(o.hasFn(_MFn_kShape), _2_MFnDagNode(o)) for o in allMObjs]
                mfns = [x for f, x in flagMFns if f]
        else:
            mfns = [_2_MFnDagNode(o) for o in allMObjs if o.hasFn(_MFn_kShape)]
        allIdxDict = dict([(x.name(), i) for i, x in enumerate(mfns)])

        # 既存のキャッシュを取得。
        oldCache0, oldCache1 = self._CyObject__data['shape']

        # 現在のシェイプ構成に合わせて、既存のキャッシュから可能な限り引き継ぐ。
        cache1 = {}
        for shape in oldCache0.values():
            if shape.isValid():
                i = allIdxDict.pop(shape.nodeName_(), None)
                if i is not None:
                    cache1[i] = shape
        for shape in oldCache1.values():
            if shape.isValid():
                i = allIdxDict.pop(shape.nodeName_(), None)
                if i is not None:
                    cache1[i] = shape

        # キャッシュから引き継げなかったシェイプで、戻り値に必要なものだけを生成する。
        if allIdxDict:
            wref = _getObjectRef(self).weakref()
            if intermediates:
                # all
                for i in allIdxDict.values():
                    shape = _newNodeObjByMPath(_2_MDagPath(orig).push(mfns[i].object()))
                    shape._CyObject__data['transform'] = wref
                    cache1[i] = shape
            else:
                # not intermediate
                for i in allIdxDict.values():
                    if not mfns[i].isIntermediateObject:
                        shape = _newNodeObjByMPath(_2_MDagPath(orig).push(mfns[i].object()))
                        shape._CyObject__data['transform'] = wref
                        cache1[i] = shape

        # all を参照しながら not intermediate キャッシュを生成。
        cache0 = {}
        k0 = 0
        for i in range(len(mfns)):
            shape = cache1.get(i)
            if shape and not shape.mfn_().isIntermediateObject:
                cache0[k0] = shape
                k0 += 1

        # 新しいキャッシュをセット。
        self._CyObject__data['shape'] = [cache0, cache1]

        # オプションに応じた list を返す。
        if others:
            def count():
                cnt[0] += 1
                return cnt[0]
            cnt = [-1]
            if intermediates:
                return [
                    (cache1[count()] if f else _newNodeObjByMPath(_2_MDagPath(orig).push(o)))
                    for f, o in flagMObjs]
            else:
                return [
                    (cache0[count()] if f else _newNodeObjByMPath(_2_MDagPath(orig).push(x.object())))
                    for f, x in flagMFns if not x.isIntermediateObject]
        else:
            if intermediates:
                return [cache1[i] for i in sorted(cache1)]
            else:
                return [cache0[i] for i in sorted(cache0)]

    def transform(self):
        u"""
        :mayanode:`transform` ノードを得る。

        自身が :mayanode:`transform` の場合は自身が、
         :mayanode:`shape` の場合はその親が得られる。

        :rtype: `.Transform` or None
        """
        if self.isTransform():
            return self
        elif self.isShape():
            self.checkValid()
            return self._transform()

    # _shape を少し隠しているように、これも少し隠すものとする。
    def _transform(self):
        u"""
        `~.CyObject.checkValid` を省略して、シェイプから :mayanode:`transform` ノードを得る。

        :rtype: `.Transform` or None
        """
        # キャッシュが古い可能性があるので、MDagPath は毎回取得し直す。
        mpath = _2_MDagPath(self._CyObject__data['mpath'])
        try:
            mpath.pop()
        except RuntimeError:
            return

        # キャッシュが在ればそれを再利用、無ければ新規生成する。
        obj = self._CyObject__data['transform']
        if obj:
            obj = obj()
            if obj and obj.isValid() and obj._CyObject__data['mpath'] == mpath:
                return obj
        obj = _newNodeObjByMPath(mpath)

        # transform の子ノードを調べ、キャッシュキーを決定する。
        k0 = 0  # not intermediate
        k1 = 0  # all
        get = mpath.child
        shape_mnode = self._CyObject__data['mnode']
        for i in range(mpath.childCount()):
            mnode = get(i)
            if mnode == shape_mnode:
                break
            if mnode.hasFn(_MFn_kShape):
                k1 += 1
                if not _2_MFnDagNode(mnode).isIntermediateObject:
                    k0 += 1

        # 相互キャッシュを生成。
        obj._CyObject__data['shape'][0][k0] = self
        obj._CyObject__data['shape'][1][k1] = self
        self._CyObject__data['tranform'] = _getObjectRef(obj).weakref()
        return obj

    def isInstanceable(self):
        u"""
        インスタンス可能かどうか。

        :rtype: `bool`
        """
        return self.mfn().isInstanceable

    def isInstanced(self, indirect=True):
        u"""
        インスタンスされているかどうか。

        :param `bool` indirect:
            直接インスタンス化されたポイント以外も含めるかどうか。
        :rtype: `bool`
        """
        # NOTE: inUnderWorld だと (MDagPath|MFnDagNode).isInstanced は正常動作するが MFnDagNode.instanceCount は常に 1 となる。
        if indirect:
            return self._mpath().isInstanced()  # indirect も含んだ判定で mfn より少し速い。
        else:
            return self.mfn().isInstanced(False)

    def instanceIndex(self):
        u"""
        インスタンス番号を得る。

        :rtype: `int`

        .. note::
            この番号は並び順の変更やインスタンス数の増減によって動的に変わる。
            また、使用されているワールドスペースプラグのインデックスも
            それに合わせて変わる。
        """
        return self._mpath().instanceNumber()

    def numInstances(self, indirect=True):
        u"""
        インスタンス数を得る。

        :param `bool` indirect:
            直接インスタンス化されたポイント以外も含めるかどうか。
        :rtype: `int`
        """
        # NOTE: inUnderWorld だと (MDagPath|MFnDagNode).isInstanced は正常動作するが MFnDagNode.instanceCount は常に 1 となる。
        mfn = self.mfn()
        if indirect and mfn.inUnderWorld:
            orig = self._mpath_()
            if orig.isInstanced():  # indirect も含んだ判定。
                # inUnderWorld を抜けるまで上昇してから instanceCount を得る。
                mpath = _2_MDagPath(orig).pop()
                mfn = _2_MFnDagNode(mpath)
                while mfn.inUnderWorld:
                    mpath.pop()
                    mfn = _2_MFnDagNode(mpath)
                return mfn.instanceCount(indirect)
            return 1
        else:
            # inUnderWorld だとインスタンスコピーはできないのでこれで良い。
            return mfn.instanceCount(indirect)

    def instance(self, idx):
        u"""
        インスタンス番号からインスタンスを得る。

        :param `int` idx: インスタンス番号。
        :rtype: `.DagNode` or None
        """
        if self._mpath().instanceNumber() == idx:
            return self

        # 0 番の場合 getAPathTo で得られるようだ。
        if not idx:
            mnode = self.mnode_()
            mpath = _2_getAPathTo(mnode)
            if not mpath.instanceNumber():  # 念のためチェック。
                mpath = _2_MDagPath(_2_getAllPathsTo(mnode)[idx])
            return type(self)(mpath)

        # NOTE: getAllPathsTo で得たものをそのまま使うとクラッシュすることがあるので複製。
        arr = _2_getAllPathsTo(self.mnode_())
        if 0 <= idx < len(arr):
            return type(self)(_2_MDagPath(arr[idx]))

    def instances(self, noSelf=False):
        u"""
        インスタンスのリストを返す。

        :param `bool` noSelf: 自身を含めないようにする。
        :rtype: `list`
        """
        orig = self._mpath()
        if orig.isInstanced():  # indirect も含んだ判定。
            cls = type(self)
            idx = orig.instanceNumber()
            # NOTE: getAllPathsTo で得たものをそのまま使うとクラッシュすることがあるので複製。
            if noSelf:
                return [
                    cls(_2_MDagPath(x))
                    for i, x in enumerate(_2_getAllPathsTo(self.mnode_()))
                    if i != idx]
            else:
                return [
                    self if i == idx else cls(_2_MDagPath(x))
                    for i, x in enumerate(_2_getAllPathsTo(self.mnode_()))]
        return [] if noSelf else [self]

    def boundingBox(self, ws=False):
        u"""
        バウンディングボックスを得る。

        :param `bool` ws: ワールド空間で得るかどうか。
        :rtype: `.BoundingBox`
        """
        if ws:
            bb = self.mfn().boundingBox.transformUsing(self._mpath_().exclusiveMatrix())
            return _newBB(bb)
        return _newBB(self.mfn().boundingBox)

    def getMatrix(self, ws=False, p=False, inv=False):
        u"""
        ノードのトランスフォーメーションのマトリックスを得る。

        :param `bool` ws: ワールド空間で得るかどうか。
        :param `bool` p: 親のマトリックスを得るかどうか。
        :param `bool` inv: 逆行列を得るかどうか。
        :rtype: `.Matrix`
        """
        # それぞれプラグから得る方法もあるが、MDagPath から得た方が速い。
        if ws:
            if p:
                if inv:
                    return _newM(self._mpath().exclusiveMatrixInverse())
                else:
                    return _newM(self._mpath().exclusiveMatrix())
            else:
                if inv:
                    return _newM(self._mpath().inclusiveMatrixInverse())
                else:
                    return _newM(self._mpath().inclusiveMatrix())
        else:
            if p:
                # 親のファンクションセットを得るより MDagPath のまま計算した方が速い。
                mpath = _2_MDagPath(self._mpath()).pop()
                if inv:
                    return _newM(mpath.exclusiveMatrix() * mpath.inclusiveMatrixInverse())
                else:
                    return _newM(mpath.inclusiveMatrix() * mpath.exclusiveMatrixInverse())
            elif self.isTransform():
                if inv:
                    return _newM(self.mfn().transformationMatrix().inverse())
                else:
                    return _newM(self.mfn().transformationMatrix())
            else:
                return _newM(_MM())

    getM = getMatrix  #: `getMatrix` の別名。

    def getTransformation(self, ws=False):
        u"""
        ノードのトランスフォーメーション情報を得る。

        :mayanode:`transform` 派生ノードの
        アトリビュート ``xm`` の値を得ることと同じだが、
        オプションでワールドスペースの値を得ることもできる。

        :param `bool` ws: ワールド空間で得るかどうか。
        :rtype: `.Transformation`
        """
        if self.isTransform():
            x = mplug_get_xformmatrix(self.mfn().findPlug('xm', True))
            if ws:
                # Transformation に Matrix を乗じることで、
                # ピボットなどの各基準位置もワールド空間で一致させる。
                mpath = self._mpath_()
                if mpath.length() > 1:
                    x *= _newM(self._mpath_().exclusiveMatrix())
                    x.clear('is')
            return x
        else:
            if ws:
                return _newX(dict(m=_newM(self._mpath().exclusiveMatrix(), ImmutableMatrix)))
            else:
                return _newX({})

    getX = getTransformation  #: `getTransformation` の別名。

    def getScaling(self, ws=False):
        u"""
        ノードのスケーリングの値を得る。

        ws=False の場合は、
        単に scale アトリビュートから得られ、
        :mayanode:`joint` ノードのローカルマトリックスには含まれる
        inverseScale の影響は無視される。

        :param `bool` ws: ワールド空間で得るかどうか。
        :rtype: `.Vector`
        """
        if ws:
            return _newV(_MP(_MX(self._mpath().inclusiveMatrix()).scale(_MSpace_kTransform)))
        if self.isTransform():
            return _newV(_MP(mplug_get_nums(self.mfn().findPlug('s', True))))
        return _newV(_MP(1., 1., 1.))

    getS = getScaling  #: `getScaling` の別名。

    def getShearing(self, ws=False):
        u"""
        ノードのシアーの値を得る。

        ws=False の場合は、
        単に shear アトリビュートから得られ、
        :mayanode:`joint` ノードのローカルマトリックスには含まれる
        inverseScale の影響は無視される。

        :param `bool` ws: ワールド空間で得るかどうか。
        :rtype: `.Vector`
        """
        if ws:
            return _newV(_MP(_MX(self._mpath().inclusiveMatrix()).shear(_MSpace_kTransform)))
        if self.isTransform():
            return _newV(_MP(mplug_get_nums(self.mfn().findPlug('sh', True))))
        return _newV(_MP())

    getSh = getShearing  #: `getShearing` の別名。

    def getQuaternion(self, ws=False, ra=False, r=True, jo=True):
        u"""
        ノードの回転のクォータニオンを得る。

        デフォルトでは rotateAxis を含んでいない回転となり、
        マトリックスからの分解結果とは一致しないが、
        Maya の機能（Local Axis 表示やコンストレイン）が
        ノードの回転方向とする基準と一致する。

        ws=False の場合は、
        3種の回転アトリビュートのみから合成された結果が得られ、
        :mayanode:`joint` ノードのローカルマトリックスには含まれる
        inverseScale の影響は無視される。

        :param `bool` ws: ワールド空間で得るかどうか。
        :param `bool` ra: rotateAxis を含めるかどうか。
        :param `bool` r: rotate を含めるかどうか。
        :param `bool` jo: jointOrient を含めるかどうか。
        :rtype: `.Quaternion`

        .. note::
            ws=True の場合の親までの非一様 scale や shear による影響や
            ws=False の場合の jointOrient は、 
            :mayacmd:`xform` コマンドや :mayaapi2:`MTransformationMatrix`
            では考慮されないが、本メソッドでは考慮されている。

            ws=True の結果は Legacy Viewport での Local Axis 表示と常に一致するが、
            上位階層に 非一様 scale や shear が含まれる場合、
            orientConstraint や parentConstraint の結果とは一致しない場合がある。
            これは、コンストレイン側で考慮が足りていないからである。
            ただし、segmentScaleCompensate で常に非一様 scale が打ち消されていれば一致する。

            ws=False の結果は、上位階層に非一様 scale や shear が無いか、
            segmentScaleCompensate で常に非一様 scale が打ち消されていれば、
            親の getQ(ws=True, ra=True) を乗じた結果は getQ(ws=True) と一致する。

        .. warning::
            以下のオプションの組み合わせはエラーになる。

            - ws=False, ra=True, r=False, jo=True
            - ws=True, ra=True, r=False
            - ws=True, ra=True, jo=False
            - ws=True, r=True, jo=False
        """
        if ws:
            if (not(r and jo)) if ra else (r and not jo):
                raise ValueError('getQuaternion: unsupported option combination.')

            if self.isTransform():
                # Legacy Viewport の Local Axis と同じになる。
                # nw ではこのノードのscaleとshearを取り除いているがそれだと Local Axis には一致しない。
                # いずれにせよ、非一様scaleが残っている場合のコンストレインの結果とは一致しない。
                mfn = self.mfn()
                if ra or r or (jo and mfn.object().hasFn(_MFn_kJoint)):
                    q = _MQ().setValue(self._mpath().inclusiveMatrix().homogenize())
                    if not ra:
                        findPlug = mfn.findPlug
                        v = mplug_get_nums(findPlug('ra', True))
                        q = _ME(-v[0], -v[1], -v[2], ZYX).asQuaternion() * q
                        if not r:
                            v = mplug_get_nums(findPlug('r', True))
                            q = _ME(-v[0], -v[1], -v[2], _REVERSE_RO[findPlug('ro', True).asShort()]).asQuaternion() * q
                else:
                    q = _MQ().setValue(self._mpath().exclusiveMatrix().homogenize())
            else:
                # transform でなければ、ローカルオプションによる差はない。
                q = _MQ().setValue(self._mpath().inclusiveMatrix().homogenize())

        else:
            if ra and not r and jo:
                raise ValueError('getQuaternion: unsupported option combination.')

            if self.isTransform():
                # ssc=on であれば
                # (this.getQ() * parent.getQ(ws=True, ra=True)) が
                # this.getQ(ws=True) と同じになるようにしている。
                mfn = self.mfn()
                if ra:
                    findPlug = mfn.findPlug
                    q = _ME(mplug_get_nums(findPlug('ra', True))).asQuaternion()
                    if r:
                        q *= _ME(mplug_get_nums(findPlug('r', True)), findPlug('ro', True).asShort()).asQuaternion()
                        if jo and mfn.object().hasFn(_MFn_kJoint):
                            q *= _ME(mplug_get_nums(findPlug('jo', True))).asQuaternion()
                elif r:
                    findPlug = mfn.findPlug
                    q = _ME(mplug_get_nums(findPlug('r', True)), findPlug('ro', True).asShort()).asQuaternion()
                    if jo and mfn.object().hasFn(_MFn_kJoint):
                        q *= _ME(mplug_get_nums(findPlug('jo', True))).asQuaternion()
                elif jo and mfn.object().hasFn(_MFn_kJoint):
                    q = _ME(mplug_get_nums(mfn.findPlug('jo', True))).asQuaternion()
                else:
                    return _newQ(_MQ())
            else:
                # transform でなければ、ローカルオプションによる差はない。
                return _newQ(_MQ())

        if q[3] < 0.:
            q.negateIt()
        return _newQ(q)

    getQ = getQuaternion  #: `getQuaternion` の別名。

    def getJOQ(self, ws=False):
        u"""
        ノードの jointOrient までのクォータニオンを得る。

        `getQuaternion` の r=False 指定と同じ。

        :param `bool` ws: ワールド空間で得るかどうか。
        :rtype: `.Quaternion`
        """
        return self.getQ(ws=ws, r=False)

    def getTranslation(self, ws=False, at=2):
        u"""
        ノードの位置を得る。

        デフォルトでは回転ピボットの位置となり、
        マトリックスからの分解結果とは一致しないが、
        Maya の機能（Local Axis 表示位置やコンストレイン）が
        ノードの位置とする基準と一致する。

        :param `bool` ws: ワールド空間で得るかどうか。
        :param `int` at:
            どのアトリビュートに相当する位置を得るか。

            - 0 だとローカル原点（親の matrix 位置）。
            - 1 だと translate の位置。
            - 2 だと rotatePivot の位置。
            - 3 だと scalePivot の位置。
            - 4 以上だと matrix の位置。

        :rtype: `.Vector`
        """
        # -sp s sh sp spt -rp ra r jo rp rpt -is t
        if not self.isTransform():
            at = 4

        if at >= 3:
            if ws:
                m = self._mpath().inclusiveMatrix()
            else:
                m = self.mfn().transformationMatrix()
            if at >= 4:
                return _newV(_MP(m[12], m[13], m[14]))
            p = _MP(mplug_get_nums(self.mfn_().findPlug('sp', True)))
            p *= m
            return _newV(p)

        if at < 1:
            if ws:
                m = self._mpath().exclusiveMatrix()
                return _newV(_MP(m[12], m[13], m[14]))
            else:
                return _newV(_MP())

        mfn = self.mfn()
        findPlug = mfn.findPlug
        p = _MP(mplug_get_nums(findPlug('t', True)))

        if at >= 2:
            v = _MV(mplug_get_nums(findPlug('rp', True)))
            v += _MV(mplug_get_nums(findPlug('rpt', True)))
            if mfn.object().hasFn(_MFn_kJoint) and findPlug('ssc', True).asBool():
                s = mplug_get_nums(findPlug('is', True))
                v *= _MM([
                    1. / s[0], 0., 0., 0.,
                    0., 1. / s[1], 0., 0.,
                    0., 0., 1. / s[2], 0.,
                    0., 0., 0., 1.,
                ])
            p += v

        if ws:
            m = self._mpath_().exclusiveMatrix()
            p *= m
        return _newV(p)

    getT = getTranslation  #: `getTranslation` の別名。


#------------------------------------------------------------------------------
def _indexOfArr(obj, get, num):
    for i in range(num):
        if get(i) == obj:
            return i


def _getParentPath(orig):
    mpath = _2_MDagPath(orig).pop()
    if not _2_MFnDagNode(mpath).inModel:
        mpath.pop()
    return mpath


u'''
def _searchShapeCache(cache, key, mnode):
    for k in list(cache):
        shape = cache[k]
        if not shape.isValid():
            # 無効だったら削除。
            del cache[k]
        elif shape._CyObject__data['mnode'] == mnode:
            # 目的のものなら、キャッシュを作り直し。
            del cache[k]
            cache[key] = shape
            return shape
'''

