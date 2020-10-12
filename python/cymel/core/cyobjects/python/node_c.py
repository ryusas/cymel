# -*- coding: utf-8 -*-
u"""
`.Node` クラスでサポートする機能の中核。
"""
from ...common import *
from ..typeinfo import isDerivedNodeType as _isDerivedNodeType
from ..typeregistry import nodetypes
from .cyobject import (
    CyObject,
    _initAPI1Objects,
    _newNodePlug,
    _argsToFindComplexMPlug,
    _findComplexMPlug,
    _node4ArgsByMPlug,
    _newNodeObjByMPath,
    BIT_TRANSFORM,
)
from .objectref import _getObjectRef
from .plug_c import _evalConnList, _apiobject_error
from ._api2mplug import (
    toNonNetworkedMPlug,
    getConnWithoutUC,
)
import maya.api.OpenMaya as _api2
import maya.OpenMaya as _api1

__all__ = ['keyForDepthFirst', 'keyForBreadthFirst', 'keyForPathLength']

_MFn_kJoint = _api2.MFn.kJoint
_2_MDagPath = _api2.MDagPath
_2_MPlug = _api2.MPlug
_2_MPlug_connectedTo = _2_MPlug.connectedTo
_2_MFnAttribute = _api2.MFnAttribute
_2_MFnDagNode = _api2.MFnDagNode

_1_MDagPath = _api1.MDagPath

_createNode = cmds.createNode
_namespace = cmds.namespace
_namespaceInfo = cmds.namespaceInfo

_relatedNodeTypes = nodetypes.relatedNodeTypes

_RE_NAMESAPACE_match = re.compile(r'(.*?)([^:]+)$').match


#------------------------------------------------------------------------------
class Node_c(CyObject):
    u"""
    `.Node` クラスでサポートする機能の中核。
    """
    __slots__ = ('__plugCache',)

    CLASS_TYPE = 1  #: ラッパークラスの種類が `.Node` であることを表す。
    TYPE_BITS = 0  #: クラスでサポートしているノードの特徴を表す。

    def __new__(cls, *args, **kwargs):
        u"""
        固定引数無しでのクラスインスタンス生成時のノード生成をサポート。
        """
        if not args:
            return cls(cls.createNode(**kwargs))
        return CyObject.__new__(cls, *args)

    @classmethod
    def createNode(cls, **kwargs):
        u"""
        クラスに関連付けられたタイプのノードを生成する。

        このメソッド自体は生成されたノードの名前（文字列）が返されるが、
        固定引数無しでクラスインスタンスを生成する場合に内部的に呼び出される。

        :rtype: `str`

        .. note::
            `nodetypes.registerNodeClass <.NodeTypes.registerNodeClass>`
            で登録するカスタムノードクラスでは、
            ``_verifyNode`` メソッドの条件を満たすための処理を追加するために
            オーバーライドすることを推奨する。
        """
        clsname = cls.__name__
        typs = _relatedNodeTypes(cls)
        if len(typs) > 1:
            raise TypeError('multiple nodetypes related for: ' + clsname)
        if 'n' not in kwargs and 'name' not in kwargs:
            kwargs['n'] = clsname[0].lower() + clsname[1:] + '#'
        return _createNode(typs[0], **kwargs)

    @classmethod
    def newObject(cls, data):
        u"""
        内部データとともにインスタンスを生成する。

        内部データはブラックボックスであるものとし、
        本メソッドをオーバーライドする場合も、
        基底メソッドを呼び出して処理を完遂させなければならない。

        内部データを拡張する場合は `~.CyObject.internalData` も
        オーバーライドすること。

        :type cls: `type`
        :param cls: 生成するインスタンスのクラス。
        :param data: インスタンスにセットする内部データ。
        :rtype: 指定クラス
        """
        obj = super(Node_c, cls).newObject(data)
        obj.__plugCache = {}
        return obj

    def isInstanceOf(self, other):
        u"""
        たとえDAGパスが違っても同一ノードであるかどうか。

        `.DagNode` 派生クラスの
        インスタンスでなければ == による比較と同じである。

        :rtype: `bool`
        """
        return self.isAlive() and self._CyObject__data['mnode'] == other._CyObject__data['mnode']

    def __getattr__(self, name):
        u"""
        シンプルな名前（エイリアス名も可）からノードのアトリビュートを得る。
        """
        if name == '__apiobject__':
            raise _apiobject_error
        mplug = self.__findMPlug(name)
        if mplug:
            return _newNodePlug(self.plugClass(), self, mplug)
        if self.isTransform():
            shape = self._shape()
            if shape:
                mplug = shape.__findMPlug(name)
                if mplug:
                    return _newNodePlug(shape.plugClass(), shape, mplug)
        raise AttributeError('no attribute exists: %s.%s' % (self.name_(), name))

    def __findMPlug(self, name):
        mfn = self.mfn()
        try:
            return mfn.findPlug(name, False)
        except RuntimeError:
            mattr = mfn.findAlias(name)
            if not mattr.isNull():
                return mfn.findPlug(mattr, False)

    def hasAttr(self, name, alias=True, shape=True):
        u"""
        指定した名前のアトリビュートが在るかどうか。

        :param `bool` alias: エイリアス名を認める。
        :param `bool` shape: シェイプからも探す。
        :rtype: `bool`
        """
        mfn = self.mfn()
        if mfn.hasAttribute(name) or (alias and not mfn.findAlias(name).isNull()):
            return True
        if shape and self.isTransform():
            shape = self._shape()
            if shape:
                mfn = shape.mfn()
                return mfn.hasAttribute(name) or (alias and not mfn.findAlias(name).isNull())
        return False

    def node(self):
        u"""
        ノードを得る（このオブジェクト自身が得られる）。

        :rtype: `.Node` 派生クラス
        """
        return self

    def plugClass(self):
        u"""
        プラグクラスを得る。

        これは、 `setPlugClass` や
        `.CyObject.setGlobalPlugClass`
        で変更可能。

        :rtype: `type`
        """
        return self._CyObject__data['plugcls'] or CyObject._CyObject__glbpcls

    def thisPlugClass(self):
        u"""
        このオブジェクトに直接設定されたプラグクラスを得る。

        未設定なら None が返される。

        これは、 `setPlugClass` で変更可能。

        :rtype: `type` or None
        """
        return self._CyObject__data['plugcls']

    def setPlugClass(self, pcls=None):
        u"""
        このインスタンスのみに有効なプラグクラスをセットする。

        :param `type` cls:
            `.Plug` 派生クラス。
            None を指定するとクリアする。
        """
        self._CyObject__data['plugcls'] = pcls

    def type(self):
        u"""
        ノードタイプ名を得る。

        :rtype: `str`
        """
        return self._CyObject__data['nodetype']

    def isType(self, typename):
        u"""
        指定ノードタイプの派生型かどうか。

        :param `str` typename: ノードタイプ名。
        :rtype: `bool`
        """
        return _isDerivedNodeType(self._CyObject__data['nodetype'], typename, self._CyObject__data['getname']())

    def hasFn(self, fn):
        u"""
        指定ファンクションタイプと互換性があるかどうか。

        :param `int` fn: :mayaapi2:`MFn` タイプ。
        :rtype: `bool`
        """
        return self.mnode().hasFn(fn)

    def isDagNode(self):
        u"""
        DAGノードかどうか。

        :rtype: `bool`
        """
        return 'mpath' in self._CyObject__data

    def isTransform(self):
        u"""
        transform 派生ノードかどうか。

        :rtype: `bool`
        """
        return 'shape' in self._CyObject__data

    def isShape(self):
        u"""
        shape 派生ノードかどうか。

        :rtype: `bool`
        """
        return 'transform' in self._CyObject__data

    def isJoint(self):
        u"""
        joint 派生ノードかどうか。

        :rtype: `bool`
        """
        return self.mnode().hasFn(_MFn_kJoint)

    def mnode(self):
        u"""
        Python API 2 の :mayaapi2:`MObject` を得る。

        :rtype: :mayaapi2:`MObject`
        """
        self.checkValid()
        return self._CyObject__data['mnode']

    def mnode_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 2 の :mayaapi2:`MObject` を得る。

        :rtype: :mayaapi2:`MObject`
        """
        return self._CyObject__data['mnode']

    def mnode1(self):
        u"""
        Python API 1 の :mayaapi1:`MObject` を得る。

        :rtype: :mayaapi1:`MObject`
        """
        self.checkValid()
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mnode1']

    def mnode1_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 1 の :mayaapi1:`MObject` を得る。

        :rtype: :mayaapi1:`MObject`
        """
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mnode1']

    def mfn(self):
        u"""
        Python API 2 のファンクションセットを得る。

        :rtype: :mayaapi2:`MFnDependencyNode` の派生
        """
        self.checkValid()
        return self._CyObject__data['mfn']

    def mfn_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 2 のファンクションセットを得る。

        :rtype: :mayaapi2:`MFnDependencyNode` の派生
        """
        return self._CyObject__data['mfn']

    def mfn1(self):
        u"""
        Python API 1 のファンクションセットを得る。

        :rtype: :mayaapi1:`MFnDependencyNode` の派生
        """
        self.checkValid()
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mfn1']

    def mfn1_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 1 のファンクションセットを得る。

        :rtype: :mayaapi1:`MFnDependencyNode` の派生
        """
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mfn1']

    def mpath(self):
        u"""
        Python API 2 の :mayaapi2:`MDagPath` を得る。

        得られる :mayaapi2:`MDagPath` は内部データの複製であるため、
        書き換えても問題ない。

        DAGパスをサポートするクラスのインスタンスでなくても、
        実際のノードがDAGノードなら得ることができる。

        :rtype: :mayaapi2:`MDagPath` or None
        """
        if 'mpath' in self._CyObject__data:
            self.checkValid()
            return _2_MDagPath(self._CyObject__data['mpath'])

    def mpath_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 2 の :mayaapi2:`MDagPath` を得る。

        :rtype: :mayaapi2:`MDagPath`
        """
        return _2_MDagPath(self._CyObject__data['mpath'])

    def _mpath(self):
        u"""
        Python API 2 の :mayaapi2:`MDagPath` を複製せずに得る。

        :rtype: :mayaapi2:`MDagPath`

        .. warning::
            内部で保持している :mayaapi2:`MDagPath` がそのまま返されるので、
            得た後の取り扱いには注意が必要。
        """
        self.checkValid()
        return self._CyObject__data['mpath']

    def _mpath_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 2 の :mayaapi2:`MDagPath` を複製せずに得る。

        :rtype: :mayaapi2:`MDagPath`

        .. warning::
            内部で保持している :mayaapi2:`MDagPath` がそのまま返されるので、
            得た後の取り扱いには注意が必要。
        """
        return self._CyObject__data['mpath']

    def mpath1(self):
        u"""
        Python API 1 の :mayaapi1:`MDagPath` を得る。

        得られる :mayaapi1:`MDagPath` は内部データの複製であるため、
        書き換えても問題ない。

        DAGパスをサポートするクラスのインスタンスでなくても、
        実際のノードがDAGノードなら得ることができる。

        :rtype: :mayaapi1:`MDagPath` or None
        """
        self.checkValid()
        _initAPI1Objects(self._CyObject__data)
        if 'mpath1' in self._CyObject__data:
            return _1_MDagPath(self._CyObject__data['mpath1'])

    def mpath1_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 1 の :mayaapi1:`MDagPath` を得る。

        :rtype: :mayaapi1:`MDagPath`
        """
        _initAPI1Objects(self._CyObject__data)
        return _1_MDagPath(self._CyObject__data['mpath1'])

    def _mpath1(self):
        u"""
        Python API 1 の :mayaapi1:`MDagPath` を複製せずに得る。

        :rtype: :mayaapi1:`MDagPath`

        .. warning::
            内部で保持している :mayaapi1:`MDagPath` がそのまま返されるので、
            得た後の取り扱いには注意が必要。
        """
        self.checkValid()
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mpath1']

    def _mpath1_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 1 の :mayaapi1:`MDagPath` を複製せずに得る。

        :rtype: :mayaapi1:`MDagPath`

        .. warning::
            内部で保持している :mayaapi1:`MDagPath` がそのまま返されるので、
            得た後の取り扱いには注意が必要。
        """
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mpath1']

    def hasUniqueName(self):
        u"""
        ノード名がユニークであるかどうかを得る。

        :rtype: `bool`
        """
        return self.mfn().hasUniqueName()

    def isDefaultNode(self):
        u"""
        デフォルトノードかどうか。

        :rtype: `bool`
        """
        return self.mfn().isDefaultNode

    def isFromReferencedFile(self):
        u"""
        リファレンスファイルのノードかどうか。

        :rtype: `bool`
        """
        return self.mfn().isFromReferencedFile

    def isLocked(self):
        u"""
        ロックされているかどうか。

        :rtype: `bool`
        """
        return self.mfn().isLocked

    def isShared(self):
        u"""
        共有ノードかどうか。

        :rtype: `bool`
        """
        return self.mfn().isShared

    def isRenamable(self):
        u"""
        リネーム可能かどうか。

        :rtype: `bool`
        """
        mfn = self.mfn()
        return not(mfn.isShared or mfn.isLocked or mfn.isFromReferencedFile)

    def pluginName(self):
        u"""
        プラグインノードの場合は、そのプラグイン名を得る。

        :rtype: `str`
        """
        return self.mfn().pluginName

    def mtypeId(self):
        u"""
        API2 の :mayaapi2:`MTypeId` を得る。

        :rtype: :mayaapi2:`MTypeId`
        """
        return self.mfn().typeId

    if MAYA_VERSION >= (2016,):
        def _uuid(self):
            u"""
            UUID を得る。

            :rtype: `str`
            """
            return str(self.mfn().uuid())

    def nodeName(self, removeNamespace=False):
        u"""
        DAGパスを含まないノード名を得る。

        :param `bool` removeNamespace: ネームスペースを含めない。
        :rtype: `str`
        """
        if removeNamespace:
            return _RE_NAMESAPACE_match(self.mfn().name()).group(2)
        else:
            return self.mfn().name()

    def nodeName_(self):
        u"""
        `~.CyObject.checkValid` を省略して、DAGパスを含まないノード名を得る。

        :rtype: `str`
        """
        return self.mfn_().name()

    def namespace(self, relative=False):
        u"""
        ネームスペースを得る。

        デフォルトでは、
        常に : で始まる絶対ネームスペースが得られる。

        :param `bool` relative:
            相対ネームスペースを得る。

            Maya の相対ネームスペースモードが ON の場合は
            カレントネームスペースから、
            OFF の場合は ルートネームスペースからの
            相対ネームスペースとなる。
        :rtype: `str`
        """
        # ノード名も mfn.namespace も Maya の相対ネームスペースモードの影響を受けるが、
        # mfn.namespace 以下のようになっており、一部がノード名の場合と異なるため、
        # ノード名に合わせた取得方法にしている。
        # - ルートネームスペースは常に '' が返される（ノード名では : となる）。
        # - カレントネームスペースは絶対で返される（ノード名では無しになる）。
        # - カレントの下位にない場合は絶対で返される（ノード名でも同じ）。
        # - カレントの下位のネームスペースは相対で返される（ノード名でも同じ）。
        if relative:
            return _RE_NAMESAPACE_match(self.mfn().name()).group(1)
        else:
            ns = self.mfn().namespace
            if not ns:
                return ':'
            elif ns.startswith(':'):
                return ns
            elif _namespace(q=True, rel=True):
                return _namespaceInfo(cur=True, an=True) + ':' + ns
            else:
                return ':' + ns

    u'''
    def mplug(self, name):
        u"""
        `~.CyObject.checkValid` を省略して、ノードのアトリビュートの :mayaapi2:`MPlug` を得る。

        :param `str` name:
            アトリビュートを特定する名前。
            単一の名前に限らず、コンパウンド階層や
            マルチインデックスも混在して指定できる。
        :rtype: :mayaapi2:`MPlug`
        """
        self.checkValid()
        return self.mplug_(name)

    def mplug_(self, name):
        u"""
        `~.CyObject.checkValid` を省略して、ノードのアトリビュートの :mayaapi2:`MPlug` を得る。

        :param `str` name:
            アトリビュートを特定する名前。
            単一の名前に限らず、コンパウンド階層や
            マルチインデックスも混在して指定できる。
        :rtype: :mayaapi2:`MPlug`
        """
        tkns = name.split('.')
        ancestorIdxs, leafName, leafIdx = _argsToFindComplexMPlug(tkns)
        try:
            return _findComplexMPlug(self._CyObject__data['mfn'], ancestorIdxs, leafName, leafIdx)
        except RuntimeError:
            if self.isTransform():
                shape = self._shape()
                if shape:
                    try:
                        return _findComplexMPlug(shape._CyObject__data['mfn'], ancestorIdxs, leafName, leafIdx)
                    except RuntimeError:
                        pass
            raise AttributeError('no attribute exists: %s.%s' % (self.name_(), name))
    '''

    def plug(self, name, pcls=None):
        u"""
        ノードのアトリビュートを得る。

        Python属性としても同じように取得できるが、
        Pythonの名前と衝突する場合のためにこのメソッドがある。

        :param `str` name:
            アトリビュートを特定する名前。
            単一の名前に限らず、コンパウンド階層や
            マルチインデックスも混在して指定できる。
        :param `type` pcls:
            得たいプラグオブジェクトのクラス。
            省略時は `plugClass` で得られる
            現在のデフォルトプラグクラスが使用される。
        :rtype: `.Plug`
        """
        self.checkValid()
        return self.plug_(name, pcls)

    def plug_(self, name, pcls=None):
        u"""
        `~.CyObject.checkValid` を省略して、ノードのアトリビュートを得る。

        :param `str` name:
            アトリビュートを特定する名前。
            単一の名前に限らず、コンパウンド階層や
            マルチインデックスも混在して指定できる。
        :param `type` pcls:
            得たいプラグオブジェクトのクラス。
            省略時は `plugClass` で得られる
            現在のデフォルトプラグクラスが使用される。
        :rtype: `.Plug`
        """
        tkns = name.split('.')
        ancestorIdxs, leafName, leafIdx = _argsToFindComplexMPlug(tkns)
        try:
            mplug = _findComplexMPlug(self._CyObject__data['mfn'], ancestorIdxs, leafName, leafIdx)
        except RuntimeError:
            if self.isTransform():
                shape = self._shape()
                if shape:
                    try:
                        mplug = _findComplexMPlug(shape._CyObject__data['mfn'], ancestorIdxs, leafName, leafIdx)
                    except RuntimeError:
                        pass
                    else:
                        return _newNodePlug(pcls or shape.plugClass(), shape, mplug)
            raise AttributeError('no attribute exists: %s.%s' % (self.name_(), name))
        else:
            return _newNodePlug(pcls or self.plugClass(), self, mplug)

    def connections(
        self,
        s=True, d=True, c=False, t=None, et=False, scn=False,
        source=True, destination=True, connections=False,
        type=None, exactType=False, skipConversionNodes=False,
        asPair=False, asNode=False,
        index=None, pcls=None,
    ):
        u"""
        コネクトされているプラグやノードのリストを得る。

        :param `bool` s|source:
            上流のコネクションを得る。
        :param `bool` d|destination:
            下流のコネクションを得る。
        :param `bool` c|connections|asPair:
            コネクト元のプラグもエアで得る。
        :param `str` t|type:
            指定したノードタイプに限定する。
        :param `bool` et|exactType:
            type指定の場合に、派生タイプを許容せずに
            指定タイプとの厳密な一致のみとするかどうか。
        :param `bool` scn|skipConversionNodes:
            unitConversion系ノードをスキップするかどうか。
        :param `bool` asNode:
            コネクト先をプラグではなくノードで得る。
        :param `int` index:
            結果を1つだけ得る場合にインデックスを指定する。
            負数も指定可能。
            結果は `list` ではなく単一となる（得られない場合は None ）。
            範囲外を指定してもエラーにはならず None となる。
        :param pcls:
            得たいプラグオブジェクトのクラス。
            省略時は `plugClass` で得られる
            現在のデフォルトプラグクラスが使用される。
        :rtype: `list`
        """
        self.checkValid()

        source &= s
        destination &= d
        asPair |= c
        asPair |= connections
        type = type or t
        exactType |= et
        getConn = getConnWithoutUC if skipConversionNodes or scn else _2_MPlug_connectedTo

        # 得られたコネクト先を一旦保持するための処理。
        # このメソッドの途中であっても Networked のまま保持するのは危険であるため、
        # 即 Non-Networked 化するか Node を得るための情報に変換しておく。
        if asNode:
            toKeep = _node4ArgsByMPlug
        else:
            toKeep = toNonNetworkedMPlug

        # 得られたコネクションを results に追加する処理。
        if asPair:
            def addMPlugs(marr, fromMPlug):
                fromMPlug = toNonNetworkedMPlug(fromMPlug)
                results.extend([(fromMPlug, toKeep(x)) for x in marr])
        else:
            def addMPlugs(marr, *args):
                results.extend([toKeep(x) for x in marr])

        # コネクションを収集。
        results = []
        for mplug in self._CyObject__data['mfn'].getConnections():
            marr = getConn(mplug, source, destination)
            if marr:
                addMPlugs(marr, mplug)
        addMPlugs = None

        # 得た結果を共通ルーチンで加工して返す。
        if not pcls:
            pcls = (asPair or not asNode) and self.plugClass()
        return _evalConnList(self, results, not asNode and pcls, asPair and pcls, index, type, exactType)

    def inputs(self, **kwargs):
        u"""
        上流のコネクションを得る。

        `connections` に s=True, d=False を指定することと同等であり、
        その他のオプションも全て指定可能。
        """
        return self.connections(True, False, **kwargs)

    def outputs(self, **kwargs):
        u"""
        下流のコネクションを得る。

        `connections` に s=False, d=True を指定することと同等であり、
        その他のオプションも全て指定可能。
        """
        return self.connections(False, True, **kwargs)

    def worldSpacePlugs(self, pcls=None):
        u"""
        ワールド空間出力プラグのリストを得る。

        :param `type` pcls:
            得たいプラグオブジェクトのクラス。
            省略時は `plugClass` で得られる
            現在のデフォルトプラグクラスが使用される。
        :rtype: `list`
        """
        if 'mpath' in self._CyObject__data:
            mfnnode = self.mfn()
            mfn_attr = mfnnode.attribute
            mattrs = [mfn_attr(i) for i in range(mfnnode.attributeCount())]
            findPlug = mfnnode.findPlug
            pcls = pcls or self.plugClass()
            return [
                _newNodePlug(pcls, self, findPlug(x, False))
                for x in mattrs if _2_MFnAttribute(x).worldSpace]
        else:
            return []

    def plugsAffectsWorldSpace(self, pcls=None):
        u"""
        ワールド空間出力に影響を与えるプラグのリストを得る。

        :param `type` pcls:
            得たいプラグオブジェクトのクラス。
            省略時は `plugClass` で得られる
            現在のデフォルトプラグクラスが使用される。
        :rtype: `list`
        """
        if 'mpath' in self._CyObject__data:
            mfnnode = self.mfn()
            mfn_attr = mfnnode.attribute
            mattrs = [mfn_attr(i) for i in range(mfnnode.attributeCount())]
            findPlug = mfnnode.findPlug
            pcls = pcls or self.plugClass()
            return [
                _newNodePlug(pcls, self, findPlug(x, False))
                for x in mattrs if _2_MFnAttribute(x).affectsWorldSpace]
        else:
            return []

    # どのクラスでも transform から shape のプラグを得られるようにするために Node クラスで実装が必要。
    def _shape(self, idx=0, intermediates=False):
        u"""
        `~.CyObject.checkValid` を省略して、 :mayanode:`transform` から :mayanode:`shape` ノードを得る。

        :param `int` idx:
            得たいシェイプのインデックス。

            intermediates オプションによって、
            同じインデックスでも得られるものが変わることがある。
            無効なインデックスを指定するとエラーではなく None となる。

            Python的な負のインデックスも指定可能。
        :param `bool` intermediates:
            インターミディエイトオブジェクトも含めるかどうか。
        :rtype: `.Shape` or None
        """
        orig = self._CyObject__data['mpath']

        # intermediate を含めるなら子ノードを数えてインデックスにマッチング。
        # この過程で cache0 と cache1 の両方のインデックスが確定する。
        if intermediates:
            get = orig.child
            mobjs = [get(i) for i in range(orig.childCount())]
            mobjs = [x for x in mobjs if x.hasFn(_MFn_kShape)]
            if idx < 0:
                idx += len(mobjs)
                if idx < 0:
                    return
            mnode = None
            k0 = 0  # not intermediate
            k1 = 0  # all
            for mobj in mobjs:
                if k1 == idx:
                    mnode = mobj
                    if _2_MFnDagNode(mobj).isIntermediateObject:
                        k0 = None
                    break
                k1 += 1
                if not _2_MFnDagNode(mobj).isIntermediateObject:
                    k0 += 1
            if mnode:
                return self.__getShapeWithCache(k0, k1, mnode)

        # intermediate を含めないなら MDagPath からインデックス指定で直接取得可能。
        # ただし、キャッシュが古い可能性があるので、MDagPath は毎回取得し直す。
        # cache0 のインデックスしか確定しないが、キャッシュ利用時は両方から探されるの良いものとする。
        else:
            if idx < 0:
                idx += orig.numberOfShapesDirectlyBelow()
                if idx < 0:
                    return
            mpath = _2_MDagPath(orig)
            try:
                mpath.extendToShape(idx)
            except RuntimeError:
                return
            return self.__getShapeWithCache(idx, None, mpath.node(), mpath)

    def __getShapeWithCache(self, k0, k1, mnode, mpath=None):
        u"""
        シェイプを1つキャッシュとともに得るための共通ルーチン。

        :param `int` k0:
            インターミディエイト含まないキャッシュのインデックス。
        :param `int` k1:
            インターミディエイトも含むキャッシュのインデックス。
        :param mnode: シェイプの :mayaapi2:`MObject` 。
        :param mpath: シェイプの :mayaapi2:`MDagPath` 。
        :rtype: `.Shape`
        """
        cache0, cache1 = self._CyObject__data['shape']

        # not intermediate (0) に有効なキャッシュが在れば再利用、無ければエントリを削除する。
        shape = cache0.get(k0)
        if shape:
            if shape.isValid() and shape._CyObject__data['mnode'] == mnode:
                if k1 is not None:
                    cache1[k1] = shape
                return shape
            del cache0[k0]

        # all (1) に有効なキャッシュが在れば再利用、無ければエントリを削除する。
        shape = cache1.get(k1)
        if shape:
            if shape.isValid() and shape._CyObject__data['mnode'] == mnode:
                if k0 is not None:
                    cache0[k0] = shape
                return shape
            del cache1[k1]

        # not intermediate (0) キャッシュの他のエントリも探す。
        if k0 is not None:
            shape = _searchShapeCache(cache0, k0, mnode)
            if shape:
                return shape

        # all (1) キャッシュの他のエントリも探す。
        if k1 is not None:
            shape = _searchShapeCache(cache1, k1, mnode)
            if shape:
                return shape

        # 新規生成し、相互キャッシュを生成。
        shape = _newNodeObjByMPath(mpath or self.mpath_().push(mnode))
        if k0 is not None:
            cache0[k0] = shape
        if k1 is not None:
            cache1[k1] = shape
        if self.TYPE_BITS & BIT_TRANSFORM:
            # shape の transform キャッシュは Transform 派生クラスに限るものとする。
            shape._CyObject__data['transform'] = _getObjectRef(self).weakref()
        return shape


#------------------------------------------------------------------------------
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


#------------------------------------------------------------------------------
def keyForDepthFirst(node):
    u"""
    ノードリストをDAG階層の深さ優先ソートするためのキー関数。

    DAGノードなら
    `~.DagNodeMixin.siblingIndices`
    の結果を、そうでなければ空リストを返す。

    :type node: `.Node`
    :param node: 検査するノード。
    :ryype: `list`
    """
    return node.siblingIndices() if node.isDagNode() else []


def keyForBreadthFirst(node):
    u"""
    ノードリストをDAG階層の幅優先ソートするためのキー関数。

    DAGノードなら
    `~.DagNodeMixin.lengthAndSiblingIndices`
    の結果を、そうでなければ 0 と空リストを返す。

    同じパス長のノードの順序が保証されなくて構わないなら、
    `keyForPathLength` を利用すると少し処理が軽い。

    :type node: `.Node`
    :param node: 検査するノード。
    :ryype: (int, `list`)
    """
    return node.lengthAndSiblingIndices() if node.isDagNode() else (0, [])


def keyForPathLength(node):
    u"""
    ノードリストをDAGパス長（階層の深さ）でソートするためのキー関数。

    `keyForBreadthFirst` に似ているが、それよりも単純で、
    同じパス長のノードの順序が保証されない。

    DAGノードなら
    `~.DagNodeMixin.pathLength`
    の結果を、そうでなければ 0 を返す。

    :type node: `.Node`
    :param node: 検査するノード。
    :rtype: `int`
    """
    return node.pathLength() if node.isDagNode() else 0

