# -*- coding: utf-8 -*-
u"""
:mayanode:`reference` ノードタイプラッパークラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ..typeregistry import nodetypes, _FIX_SLOTS
from ...utils.namespace import _mayaNS, RelativeNamespace
from .cyobject import CyObject
import maya.api.OpenMaya as _api2
import itertools

__all__ = ['Reference']

_from_iterable = itertools.chain.from_iterable

_MFn_kDagNode = _api2.MFn.kDagNode
_MFn_kReference = _api2.MFn.kReference
_2_getAllPathsTo = _api2.MDagPath.getAllPathsTo
_2_NullObj = _api2.MObject.kNullObj
if MAYA_VERSION >= (2016, 5):
    _2_MFnReference = _api2.MFnReference

_referenceQuery = cmds.referenceQuery
_file = cmds.file


#------------------------------------------------------------------------------
class Reference(nodetypes.parentBasicNodeClass('reference')):
    u"""
    :mayanode:`reference` ノードタイプラッパークラス。
    """
    if _FIX_SLOTS:
        __slots__ = tuple()

    @classmethod
    def byFilename(cls, fname, all=False):
        u"""
        解決済みのファイル名からリファレンスノードを得る。

        :param `str` fname:
            解決済みのファイル名。
        :param `bool` all:
            コピー番号なしのファイル名を指定して、
            それに対応する全てのリストを得る。
        :rtype: `Referemce` or None
        """
        if all:
            fmt = fname + '{%s}'
            return [
                (fname if x == '0' else (fmt % x))
                for x in _file(fname, q=True, cnl=True)
            ]
        r = _referenceQuery(fname, rfn=True)
        return r and cls(r)

    if MAYA_VERSION >= (2016, 5):
        def filename(self, unresolved=False, withoutPath=False, withoutCopyNumber=False):
            u"""
            ファイル名を得る。

            :param `bool` unresolved:
                指定されているファイル名をそのまま得る。
                環境変数を含んでいたり、実際は存在しないパスの場合が有り得る。
            :param `bool` withoutPath:
                パスを含まないファイル名のみを得る。
            :param `bool` withoutCopyNumber:
                同名ファイルの2つめ以降に付加されるコピー番号を含めない。
            :rtype: `str`
            """
            return _safe_call(self.mfn().fileName, '', not unresolved, withoutPath, not withoutCopyNumber)

        def associatedNamespace(self):
            u"""
            関連付けられたネームスペースを得る。

            :rtype: `.Namespace`
            """
            return _mayaNS(_safe_call(self.mfn().associatedNamespace, ':', False))

        def parent(self):
            u"""
            親リファレンスノードを得る。

            :rtype: `Reference` or None
            """
            mnode = _safe_call(self.mfn().parentReference, _2_NullObj)
            if not mnode.isNull():
                return CyObject(mnode)

        def children(self):
            u"""
            子リファレンスノードのリストを得る。

            :rtype: `list`
            """
            return [CyObject(x) for x in _safe_call(self.mfn().nodes, EMPTY_TUPLE) if x.hasFn(_MFn_kReference)]

        def root(self):
            u"""
            ルートリファレンスノードを得る。

            :rtype: `Reference`
            """
            parent = self.parent()
            if parent:
                return parent.root()
            return self

        def isRoot(self):
            u"""
            ルートリファレンスノードかどうか。

            :rtype: `bool`
            """
            return _safe_call(self.mfn().parentReference, _2_NullObj).isNull()

        def nodes(self):
            u"""
            含まれているノードのリストを得る。

            :rtype: `list`
            """
            mpathsArr = []
            pool = mpathsArr.append
            results = [_mnodeToNode(x, pool) for x in _safe_call(self.mfn().nodes, EMPTY_TUPLE)]
            if mpathsArr:
                results.extend(_from_iterable([[CyObject(x) for x in mps[1:]] for mps in mpathsArr]))
            return results

        def containsNode(self, node):
            u"""
            指定ノードを含んでいるかどうか。

            :type node: `.Node`
            :param node: チェックするノード。
            :rtype: `bool`
            """
            return _safe_call(self.mfn().containsNode, False, node.mnode())

        def containsNodeExactly(self, node):
            u"""
            指定ノードを直接含んでいるかどうか。

            :type node: `.Node`
            :param node: チェックするノード。
            :rtype: `bool`
            """
            return _safe_call(self.mfn().containsNodeExactly, False, node.mnode())

        def isLoaded(self):
            u"""
            リファレンスがロードされているかどうか。

            :rtype: `bool`
            """
            return _safe_call(self.mfn().isLoaded, False)

        def isExportEditsFile(self):
            u"""
            リファレンス編集ファイル (editMA や editMB) かどうか。

            :rtype: `bool`
            """
            return _safe_call(self.mfn().isExportEditsFile, False)

        def isReferenceLocked(self):
            u"""
            リファレンスがロックされているかどうか。

            :rtype: `bool`
            """
            return _safe_call(self.mfn().isLocked, False)

        def isLocked(self):
            u"""
            ロックされているかどうか。

            :rtype: `bool`
            """
            return super(_2_MFnReference, self.mfn()).isLocked

    else:
        def filename(self, unresolved=False, withoutPath=False, withoutCopyNumber=False):
            u"""
            ファイル名を得る。

            :param `bool` unresolved:
                指定されているファイル名をそのまま得る。
                環境変数を含んでいたり、実際は存在しないパスの場合が有り得る。
            :param `bool` withoutPath:
                パスを含まないファイル名のみを得る。
            :param `bool` withoutCopyNumber:
                同名ファイルの2つめ以降に付加されるコピー番号を含めない。
            :rtype: `str`
            """
            return _safe_call(_referenceQuery, '', f=True, un=unresolved, shn=withoutPath, wcn=withoutCopyNumber)

        def associatedNamespace(self):
            u"""
            関連付けられたネームスペースを得る。

            :rtype: `.Namespace`
            """
            # 相対ネームスペースモードに影響されず、常に絶対ネームスペースが返される。ルートも : が返される。
            return _mayaNS(_safe_call(_referenceQuery, ':', self, ns=True))

        def parent(self):
            u"""
            親リファレンスノードを得る。

            :rtype: `Reference` or None
            """
            parent = _safe_call(_referenceQuery, None, self, rfn=True, p=True)
            if parent:
                return CyObject(parent)

        def children(self):
            u"""
            子リファレンスノードのリストを得る。

            :rtype: `list`
            """
            return [CyObject(x) for x in (_safe_call(_referenceQuery, None, self, rfn=True, ch=True) or EMPTY_TUPLE)]

        def root(self):
            u"""
            ルートリファレンスノードを得る。

            :rtype: `Reference`
            """
            name = self.name()
            root = _safe_call(_referenceQuery, name, name, rfn=True, tr=True)
            return self if root == name else CyObject(root)

        def isRoot(self):
            u"""
            ルートリファレンスノードかどうか。

            :rtype: `bool`
            """
            name = self.name()
            return _safe_call(_referenceQuery, name, name, rfn=True, tr=True) == name

        def nodes(self):
            u"""
            含まれているノードのリストを得る。

            :rtype: `list`
            """
            results = _safe_call(_referenceQuery, None, self, n=True, dp=True) or EMPTY_TUPLE
            results = [CyObject(x) for x in results]
            results.extend(_from_iterable([x.instances(True) for x in results if x.isDagNode()]))
            return results

        def containsNode(self, node):
            u"""
            指定ノードを含んでいるかどうか。

            :type node: `.Node`
            :param node: チェックするノード。
            :rtype: `bool`
            """
            ref = self.name()
            try:
                names = _referenceQuery(ref, n=True, dp=True)
            except:
                return False

            if node.isDagNode():
                if node.instanceIndex():
                    node = node.instance(0)
                name = node.name_()
                if '|' in name:
                    name = node.fullPath()
            else:
                name = node.name_()

            return (names and name in names) or _containsNode(ref, name)

        def containsNodeExactly(self, node):
            u"""
            指定ノードを直接含んでいるかどうか。

            :type node: `.Node`
            :param node: チェックするノード。
            :rtype: `bool`
            """
            names = _safe_call(_referenceQuery, None, self, n=True, dp=True)
            if not names:
                return False

            if node.isDagNode():
                if node.instanceIndex():
                    node = node.instance(0)
                name = node.name_()
                if '|' in name:
                    name = node.fullPath()
            else:
                name = node.name_()
            return name in names

        def isLoaded(self):
            u"""
            ロードされているかどうか。

            :rtype: `bool`
            """
            return _safe_call(_referenceQuery, False, self, il=True)

        def isExportEditsFile(self):
            u"""
            リファレンス編集ファイル (editMA や editMB) かどうか。

            :rtype: `bool`
            """
            return _safe_call(_referenceQuery, False, self, iee=True)

    fileName = filename  #: `filename` の別名。
    associatedNS = associatedNamespace  #: `associatedNamespace` の別名。
    referenceNode = parent  #: `parent` の別名。

    def iterBreadthFirst(self):
        u"""
        リファレンス階層を幅優先反復する。

        :rtype: yield `Reference`
        """
        return iterTreeBreadthFirst([self], lambda x: x.children())

    def iterDepthFirst(self):
        u"""
        リファレンス階層を深さ優先反復する。

        :rtype: yield `Reference`
        """
        return iterTreeDepthFirst([self], lambda x: x.children())

    def load(self):
        u"""
        ロードする。
        """
        return _file(loadReference=self)

    def unload(self):
        u"""
        アンロードする。
        """
        return _file(rfn=self, unloadReference=True)

    def lockReference(self, val=True):
        u"""
        リファレンスをロック、又はアンロックする。

        :param `bool` val: ロック状態値。
        """
        return _file(self.filename(), lockReference=val)

    def unlockReference(self):
        u"""
        リファレンスをアンロックする。
        """
        return _file(self.filename(), lockReference=False)

    def removeReference(self):
        u"""
        リファレンスを削除する。
        """
        return _file(self.filename(), rr=True)

    def importReference(self):
        u"""
        リファレンスをインポートする。
        """
        return _file(self.filename(), ir=True)

    def editStrings(self, command=None, fail=False, success=True, namespace=True):
        u"""
        編集コマンドリストを得る。

        :param `str` command:
            コマンドの種類を指定する。
            有効な値は、'addAttr'、'connectAttr'、'deleteAttr'、'disconnectAttr'、
            'parent'、'setAttr'、'lock'、および'unlock'である。
        :param `bool` fail:
            失敗したコマンドを得るかどうか。
        :param `bool` success:
            成功したコマンドを得るかどうか。
        :param `bool` namespace:
            リファレンスによるネームスペースを付加するかどうか。
            付加されるのは、親リファレンスのローカルネームスペースまで。
        :rtype: `list`
        """
        if command:
            return _safe_call(_referenceQuery, [], self, es=True, fld=fail, scs=success, sns=namespace, ec=command)
        else:
            return _safe_call(_referenceQuery, [], self, es=True, fld=fail, scs=success, sns=namespace)

    def editNodes(self, command=None, fail=False, success=True):
        u"""
        編集コマンドのノードリストを得る。

        可能な限り cymel のノードオブジェクトが返されるが、
        見つからない場合は文字列のまま返される。

        :param `str` command:
            コマンドの種類を指定する。
            有効な値は、'addAttr'、'connectAttr'、'deleteAttr'、'disconnectAttr'、
            'parent'、'setAttr'、'lock'、および'unlock'である。
        :param `bool` fail:
            失敗したコマンドを得るかどうか。
        :param `bool` success:
            成功したコマンドを得るかどうか。
        :rtype: `list`
        """
        if command:
            names = _safe_call(_referenceQuery, None, self, en=True, fld=fail, scs=success, sns=True,  ec=command)
        else:
            names = _safe_call(_referenceQuery, None, self, en=True, fld=fail, scs=success, sns=True)
        if names:
            # showNamespace(sns)=True では、親リファレンスのローカルネームスペースが付加されるので、
            # その親の相対ネームスペースモードで評価する。
            objDict = {}
            parent = self.parent()
            if parent:
                parent = parent.parent()
                if parent:
                    with RelativeNamespace(parent.associatedNamespace()):
                        return [_getRefEditsNode(x, objDict) for x in names]
            return [_getRefEditsNode(x, objDict) for x in names]
        return []

    def editAttrs(self, command=None, fail=False, success=True):
        u"""
        編集コマンドのアトリビュート名リストを得る。

        :param `str` command:
            コマンドの種類を指定する。
            有効な値は、'addAttr'、'connectAttr'、'deleteAttr'、'disconnectAttr'、
            'parent'、'setAttr'、'lock'、および'unlock'である。
        :param `bool` fail:
            失敗したコマンドを得るかどうか。
        :param `bool` success:
            成功したコマンドを得るかどうか。
        :rtype: `list`
        """
        if command:
            return _safe_call(_referenceQuery, [], self, ea=True, fld=fail, scs=success,  ec=command)
        else:
            return _safe_call(_referenceQuery, [], self, ea=True, fld=fail, scs=success)

    def editPlugs(self, command=None, fail=False, success=True):
        u"""
        編集コマンドのプラグリストを得る。

        可能な限り cymel のプラグオブジェクトが返されるが、
        見つからない場合は文字列のまま返される。

        :param `str` command:
            コマンドの種類を指定する。
            有効な値は、'addAttr'、'connectAttr'、'deleteAttr'、'disconnectAttr'、
            'parent'、'setAttr'、'lock'、および'unlock'である。
        :param `bool` fail:
            失敗したコマンドを得るかどうか。
        :param `bool` success:
            成功したコマンドを得るかどうか。
        :rtype: `list`
        """
        nodes = self.editNodes(command, fail, success)
        if not nodes:
            return nodes
        if command:
            attrs = _referenceQuery(self.name_(), ea=True, fld=fail, scs=success,  ec=command)
        else:
            attrs = _referenceQuery(self.name_(), ea=True, fld=fail, scs=success)
        return [
            (x.plug_(y) if isinstance(x, CyObject) and x.hasAttr(y) else (x + '.' + y))
            for x, y in zip(nodes, attrs)]

nodetypes.registerNodeClass(Reference, 'reference')


def _safe_call(proc, default, *args, **kwargs):
    u"""
    安全にコールする。エラー時はdefaultを返す。
    """
    try:
        return proc(*args, **kwargs)
    except:
        return default


def _mnodeToNode(mnode, pool_mpaths):
    u"""
    MObject から Node を得る。
    """
    if mnode.hasFn(_MFn_kDagNode):
        mpaths = _2_getAllPathsTo(mnode)
        if len(mpaths) >= 2:
            pool_mpaths(mpaths)
        return CyObject(mpaths[0])
    else:
        return CyObject(mnode)


def _containsNode(ref, name):
    u"""
    リファレンスにノードが含まれるかどうかを文字列ベースで比較。
    """
    for ref in (_referenceQuery(ref, rfn=True, ch=True) or EMPTY_TUPLE):
        names = _referenceQuery(ref, n=True, dp=True)
        if (names and name in names) or _containsNode(ref, name):
            return True
    return False


def _getRefEditsNode(name, objDict):
    u"""
    Reference Edits 中のノード実体を得る。
    """
    res = objDict.get(name)
    if res:
        return res
    try:
        res = CyObject(name)
    except KeyError:
        # ノード名はフルDAGパスで書かれているが、
        # 構造が変わった場合も Reference Edits はそこそこ機能するので、
        # それに倣い、なんとか見つける。
        tkns = name.split('|')
        while len(tkns) > 1:
            tkns = tkns[1:]
            try:
                res = CyObject('|'.join(tkns))
            except KeyError:
                pass
            else:
                break

    if res:
        objDict[name] = res
        return res
    else:
        objDict[name] = name
        return name

