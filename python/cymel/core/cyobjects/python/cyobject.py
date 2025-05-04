# -*- coding: utf-8 -*-
u"""
Mayaラッパーオブジェクトの抽象基底クラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import types
from uuid import UUID as _UUID
from ...common import *
from ..typeinfo import isDerivedNodeType as _isDerivedNodeType
from ..typeregistry import nodetypes
from ._api2mplug import (
    _1_mpath, _1_mnode,
    makePlugTypeInfo,
    toNonNetworkedMPlug,
)
from ._api2attrname import (
    findMPlug as _findMPlug,
    findMAttr as _findMAttr,
    findComplexMPlug as _findComplexMPlug,
    argToFindComplexMPlug as _argToFindComplexMPlug,
    IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES,
    _MayaAPI2RuntimeError, _MayaAPI2Errors,
)
import maya.api.OpenMaya as _api2
import maya.OpenMaya as _api1

__all__ = [
    'IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES',
    'BIT_DAGNODE', 'BIT_TRANSFORM', 'BIT_SHAPE',
    'CyObject', 'O',
    'cyObjects', 'Os',
    'ModuleForSel',
    'UUID_ATTR_NAME',
]

UUID_ATTR_NAME = 'uuid'  #: Maya標準ではなくPython機能で生成するUUIDを保持するアトリビュート。

_MFn = _api2.MFn
_2_MObject = _api2.MObject
_2_MDagPath = _api2.MDagPath
_2_MPlug = _api2.MPlug
_2_MSelectionList = _api2.MSelectionList
_2_MObjectHandle = _api2.MObjectHandle
_2_MFnDagNode = _api2.MFnDagNode
_2_MFnAttribute = _api2.MFnAttribute

_MFn_kDagNode = _MFn.kDagNode
_MFn_kTransform = _MFn.kTransform
_MFn_kShape = _MFn.kShape
_2_getAPathTo = _2_MDagPath.getAPathTo
_2_getAllPathsTo = _2_MDagPath.getAllPathsTo
_2_getActiveSelectionList = _api2.MGlobal.getActiveSelectionList
_2_getSelectionListByName = _api2.MGlobal.getSelectionListByName

_ls = cmds.ls

_decideClass = nodetypes._NodeTypes__decideClass
_relatedNodeTypes = nodetypes.relatedNodeTypes

_object_new = object.__new__

#------------------------------------------------------------------------------
BIT_DAGNODE = 0b0001  #: ノードクラスで dagNode の特徴をサポートしていることを示す。
BIT_TRANSFORM = 0b0010  #: ノードクラスで transform の特徴をサポートしていることを示す。
BIT_SHAPE = 0b0100  #: ノードクラスで shape の特徴をサポートしていることを示す。

CY_OBJECT = 0
CY_NODE = 1
CY_PLUG = 2
CY_OBJREF = -1


#------------------------------------------------------------------------------
class CymelInvalidHandle(Exception):
    u"""
    `CyObject` が保持している API ハンドルが無効。
    """
    __slots__ = tuple()


#------------------------------------------------------------------------------
class CyObject(object):
    u"""
    Mayaラッパーオブジェクトの抽象基底クラス。

    ラッパークラスは、大きく分けて
    `.Node` と `.Plug` とがある。

    `CyObject` コンストラクタに、
    シーン中の既存ノードやプラグを特定するための名前や
    Python API 2.0 オブジェクトを指定することで、
    適切なクラスのインスタンスを得ることができる。

    ノードクラスはノードタイプごとに用意されているか自動生成される。
    プラグクラスは、システムで用意しているのは1種類だけである。
    いずれも、クラスを継承してカスタムクラスを作ることができる。

    ノードクラスの場合、
    `nodetypes.registerNodeClass <.NodeTypes.registerNodeClass>`
    でシステムに登録すると便利である。

    プラグクラスの場合、
    `CyObject.setGlobalPlugClass <setGlobalPlugClass>`
    や
    `Node.setPlugClass <.Node_c.setPlugClass>`
    を用いて、一時的に使用するクラスを指定すると便利である。
    """
    __slots__ = ('__weakref__', '__data', '__ref',)
    __glbpcls = None

    CLASS_TYPE = CY_OBJECT  #: ラッパークラスの種類を表す (0=CyObject, 1=Node, 2=Plug, -1=ObjectRef)

    def __new__(cls, src):  #, **kwargs):
        # ソースがCyObject派生インスタンスの場合、その複製か参照ラッパーを得る。
        if isinstance(src, CyObject):
            return _anyClsObjByObj(cls, src)

        # ソースが文字列の場合、名前からシーンオブジェクトを検索する。
        if isinstance(src, BASESTR):
            return _anyClsObjByName(cls, src)

        # ソースが API2 MDagPath の場合。
        if isinstance(src, _2_MDagPath):
            mnode = src.node()
            mfn = _mnodeFn(src, mnode)
            if not mfn.inModel:
                raise ValueError('world (not a model) MDagPath specified')
            return _nodeClsObjByAPI2(cls, src, mnode, mfn, src)

        # ソースが API2 MObject の場合。
        if isinstance(src, _2_MObject):
            return _nodeClsObjByMObj(cls, src)

        # ソースが API2 MPlug の場合。
        if isinstance(src, _2_MPlug):
            if src.isNetworked:
                #raise ValueError('Networked plug is specified')
                src = toNonNetworkedMPlug(src)
            return _plugClsObjByMPlug(cls, src, src)

        # その他の場合、文字列として評価する。
        return _anyClsObjByName(cls, str(src))

    # bool 評価時に __len__ が呼ばれないようにするために、特に Plug で重要。
    if IS_PYTHON2:
        def __nonzero__(self):
            return True
    else:
        def __bool__(self):
            return True

    def __hash__(self):
        return self.__data['hash']

    def __repr__(self):
        if self.__data['isValid']():
            try:
                return "%s('%s')" % (type(self).__name__, self.__data['getname']())
            except:
                return "<%s at %0.16X; unexpected error>" % (type(self).__name__, id(self))
        elif self.__data['isAlive']():
            return "<%s at %0.16X; invalid handle>" % (type(self).__name__, id(self))
        else:
            return "<%s at %0.16X; dead internal reference>" % (type(self).__name__, id(self))

    def __str__(self):
        self.checkValid()
        return self.__data['getname']()

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)

    def __unicode__(self):
        self.checkValid()
        return self.__data['getname']()

    def __eq__(self, other):
        return self.__data['eq'](self, other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def isValid(self):
        u"""
        内部ハンドルが正常な状態かどうかを得る。

        `isAlive` が真でも、オブジェクトが削除されている場合は無効と判断される。

        :rtype: `bool`
        """
        return self.__data['isValid']()

    def isAlive(self):
        u"""
        内部ハンドルがメモリ上に存在しているかどうかを得る。

        オブジェクトが削除されていても、undo可能な状態で残っていれば真となる。

        :rtype: `bool`
        """
        return self.__data['isAlive']()

    def checkValid(self):
        u"""
        内部ハンドルの有効性チェック。無効なら `.CymelInvalidHandle` エラーとなる。
        """
        if not self.__data['isValid']():
            raise CymelInvalidHandle('%s at %0.16X' % (type(self).__name__, id(self)))

    def name(self):
        u"""
        オブジェクトのユニーク名を得る。

        オブジェクトの種類に応じて、
        ノード名、DAGパーシャルパス名、それらを含むプラグ名などが得られる。

        :rtype: `str`
        """
        self.checkValid()
        return self.__data['getname']()

    def name_(self):
        u"""
        `checkValid` を省略して、オブジェクトのユニーク名を得る。

        オブジェクトの種類に応じて、
        ノード名、DAGパーシャルパス名、それらを含むプラグ名などが得られる。

        :rtype: `str`
        """
        return self.__data['getname']()

    def node(self):
        u"""
        ノードを得る。

        :rtype: `.Node` 派生クラス
        """
        raise NotImplementedError('CyObject.node')

    def internalData(self):
        u"""
        内部データを返す。

        派生クラスで内部データを拡張する場合にオーバーライドする。
        その場合、 `newObject` クラスメソッドもオーバーライドし、
        拡張に対応させる。

        内部データはブラックボックスであるものとし、
        拡張データでは基底のデータも内包させる必要がある。
        """
        return self.__data

    @classmethod
    def newObject(cls, data):
        u"""
        内部データとともにインスタンスを生成する。

        内部データはブラックボックスであるものとし、
        本メソッドをオーバーライドする場合も、
        基底メソッドを呼び出して処理を完遂させなければならない。

        内部データを拡張する場合は `internalData` も
        オーバーライドすること。

        :type cls: `type`
        :param cls: 生成するインスタンスのクラス。
        :param data: インスタンスにセットする内部データ。
        :rtype: 指定クラス
        """
        obj = _object_new(cls)
        obj.__data = data
        obj.__ref = None
        #trackDestruction(obj)
        return obj

    @staticmethod
    def globalPlugClass():
        u"""
        グローバル設定のプラグクラスを得る。

        これは、 `setGlobalPlugClass` で変更可能。

        :rtype: `type`
        """
        return CyObject.__glbpcls

    @staticmethod
    def setGlobalPlugClass(pcls=None):
        u"""
        グローバル設定のプラグクラスをセットする。

        :param `type` cls:
            `.Plug` 派生クラス。
            None を指定するとクリアする。
        """
        global _defaultPlugCls
        if _defaultPlugCls is None:
            _defaultPlugCls = pcls
        CyObject.__glbpcls = pcls or _defaultPlugCls

    @classmethod
    def ls(cls, *args, **kwargs):
        u"""
        :mayacmd:`ls` コマンドの結果をクラスに適合するものに限定してオブジェクトとして得る。

        :rtype: `list`
        """
        isNode = cls.CLASS_TYPE is CY_NODE
        if isNode:
            typs = _relatedNodeTypes(cls)
            kwargs['type'] = typs
            # o=True が必要なら、オプションで指定されるものとする。

        names = _ls(*args, **kwargs)
        num = len(names)
        if not num:
            return names

        sel = _2_MSelectionList()
        for name in names:
            sel.add(name)
        num = sel.length()

        if isNode:
            if hasattr(cls, '_verifyNode'):
                return [x for x in [_getNodeObjBySelIdx(sel, i, cls) for i in range(num)] if x]
            else:
                return [_getNodeObjBySelIdx(sel, i, None) for i in range(num)]

        objMap = {} if num > 1 else None

        if cls.CLASS_TYPE is CY_PLUG:
            return [x for x in [_getPlugObjBySelIdx(sel, i, cls, objMap) for i in range(num)] if x]
        elif cls.CLASS_TYPE is CY_OBJREF:
            return [_getObjRefBySelIdx(sel, i, cls, objMap) for i in range(num)]
        else:
            return [_getObjectBySelIdx(sel, i, objMap) for i in range(num)]

    @classmethod
    def checktype(cls, obj):
        u"""
        指定したオブジェクトがクラスにマッチするかチェックする。

        `CyObject` 派生オブジェクトを指定した場合、
        マッチすればそれ自身、
        マッチしない場合は None が返される。

        それ以外の値（文字列や Python API 2.0 オブジェクトなど
        `CyObject` コンストラクタに指定可能なもの）を指定した場合、
        マッチすれば適切な型の `CyObject` 派生オブジェクト、
        マッチしない場合は None が返される。

        :param obj: チェックするオブジェクト。
        :rtype: `CyObject` or None
        """
        if not isinstance(obj, CyObject):
            try:
                obj = CyObject(obj)
            except:
                return
        if isinstance(obj, cls):
            return obj

    @classmethod
    def _py_byUUID(cls, val, candidates=EMPTY_TUPLE, py=False):
        if candidates:
            chk = cls.checktype
            objs = [chk(x) for x in candidates]
            objs = [x for x in candidates if x]
        else:
            objs = cls.ls()

        if isinstance(val, BASESTR):
            val = _UUID(val)
        elif isinstance(val, Iterable):
            uuids = set([(x if isinstance(x, _UUID) else _UUID(x)) for x in val])
            return [x for x in objs if x.hasAttr(UUID_ATTR_NAME) and _UUID(x.plug_(UUID_ATTR_NAME).get()) in uuids]
        return [x for x in objs if x.hasAttr(UUID_ATTR_NAME) and val == _UUID(x.plug_(UUID_ATTR_NAME).get())]

    if MAYA_VERSION < (2016,):
        byUUID = _py_byUUID

    else:
        @classmethod
        def byUUID(cls, val, candidates=EMPTY_TUPLE, py=False):
            u"""
            UUID からノードリストを得る。

            重複も起こり得るので、戻り値はリストである。

            :type val: `.UUID`
            :param val:
                単一の UUID かそのリスト。
                個々の UUID の型は `.UUID` か `str` を指定できる。
            :param `iterable` candidates:
                py=True の場合の候補を事前に絞りたい場合に指定する。
            :param `bool` py:
                Maya 標準機能ではなく uuid というアトリビュートに保存されているものから得る。
                2016 未満では常に True 扱いとなる。
            :rtype: `list`
            """
            if py:
                return cls._py_byUUID(val, candidates)
            elif isinstance(val, BASESTR):
                return cls.ls(val)
            elif isinstance(val, Iterable):
                return cls.ls([str(x) for x in val])
            else:
                return cls.ls(str(val))
            # NOTE:
            #   MayaObject() にそのまま指定できるようにしたいと考えたが、
            #   py オプションをどうするかという問題と、
            #   MSelectionList.add() での MUuid 指定は C++ や API1 では可能だが
            #   API2 ではサポートされていないため、保留にしている。

_defaultPlugCls = None  #: Plug が import 後にセットされる。

O = CyObject  #: `CyObject` の別名。

_O_ls = O.ls


def cyObjects(val):
    u"""
    名前リストなどから `CyObject` のリストを得る。

    文字列でも文字列のリストでも受けられ、
    None などの場合は空リストと解釈されるので、
    Mayaコマンドの戻り値をそのまま受けられることが多い。

    引数がどのようなものでも、戻り値のタイプは `list` となる。

    :param iterable val:
        ノード名やプラグ名や同等の評価が可能なもの、
        またはそれらのリスト。
    :rtype: `list`
    """
    if not val:
        return []
    elif isinstance(val, _SINGLE_SRCTYPES):
        return [O(val)]
    else:
        return [O(v) for v in val]

Os = cyObjects  #: `cyObjects` の別名。

_SINGLE_SRCTYPES = (BASESTR, _2_MObject, _2_MDagPath, _2_MPlug)


#------------------------------------------------------------------------------
def _getObjectRef(*args):
    global _getObjectRef, _newNodeRefFromData, _newPlugRefFromData
    from .objectref import _getObjectRef, _newNodeRefFromData, _newPlugRefFromData
    return _getObjectRef(*args)


def _newNodeRefFromData(*args):
    global _getObjectRef, _newNodeRefFromData, _newPlugRefFromData
    from .objectref import _getObjectRef, _newNodeRefFromData, _newPlugRefFromData
    return _newNodeRefFromData(*args)


def _newPlugRefFromData(*args):
    global _getObjectRef, _newNodeRefFromData, _newPlugRefFromData
    from .objectref import _getObjectRef, _newNodeRefFromData, _newPlugRefFromData
    return _newPlugRefFromData(*args)


#------------------------------------------------------------------------------
def _makeNodeData(mpath, mnode, mfn, dummy=None):
    u"""
    Node の内部データを構築する。
    """
    mhdl = _2_MObjectHandle(mnode)
    isAlive = mhdl.isAlive
    data = {
        'hash': mhdl.hashCode(),
        'isAlive': isAlive,
        'isValid': mhdl.isValid,
        'mnode': mnode,
        'mfn': mfn,
        'nodetype': mfn.typeName,
        'getname': mfn.partialPathName if mpath else mfn.name,
        'plugcls': None,
    }

    if mpath:
        data['mpath'] = mpath
        if mnode.hasFn(_MFn_kTransform):
            data['shape'] = [{}, {}]
        elif mnode.hasFn(_MFn_kShape):
            data['transform'] = None

        def eq(self, other):
            if isAlive() and isinstance(other, CyObject) and other._CyObject__data['isAlive']():
                if (
                    (self.refclass() if self.CLASS_TYPE is CY_OBJREF else self).TYPE_BITS and
                    (other.refclass() if other.CLASS_TYPE is CY_OBJREF else other).TYPE_BITS
                ):
                    return mpath == other._CyObject__data['mpath']
                else:
                    return mnode == other._CyObject__data['mnode']
            return False

    else:
        def eq(self, other):
            return (
                isAlive() and isinstance(other, CyObject) and
                other._CyObject__data['isAlive']() and
                mnode == other._CyObject__data['mnode']
            )
    data['eq'] = eq
    return data


def _makePlugData(noderef, mplug, typeinfo=None, typename=None, attrname=None):
    u"""
    Plug の内部データを構築する。
    """
    # NOTE: システムでは徹底しているのでデバッグ用。通常は、ユーザー指定のチェック用に CyObject.__new__ でのみ行う。
    #if mplug.isNetworked:
    #    raise ValueError('Networked plug is specified')

    if not typeinfo:
        typeinfo = makePlugTypeInfo(mplug.attribute(), typename)
    if not attrname:
        attrname = '.' + mplug.partialName(includeNonMandatoryIndices=True, includeInstancedIndices=True)
    noderef_data = noderef._CyObject__data
    node_getname = noderef_data['getname']
    data = {
        'hash': hash((noderef_data['hash'], attrname)),
        'mplug': mplug,
        'noderef': noderef,
        'attrname': attrname,
        'typeinfo': typeinfo,
        'getname': lambda: node_getname() + attrname,
        'elemIdxAttrs': None,
    }

    attr_isAlive = typeinfo['isAlive']
    if attr_isAlive:
        node_isAlive = noderef_data['isAlive']
        node_isValid = noderef_data['isValid']
        node_hasAttr = noderef_data['mfn'].hasAttribute
        keyname = _getAttrKeyName(typeinfo)
        data['isValid'] = lambda: attr_isAlive() and node_isValid() and node_hasAttr(keyname)
        isAlive = lambda: attr_isAlive() and node_isAlive()
    else:
        data['isValid'] = noderef_data['isValid']
        isAlive = noderef_data['isAlive']
    data['isAlive'] = isAlive

    def eq(self, other):
        if isAlive() and isinstance(other, CyObject):
            dt = other._CyObject__data
            return (
                'mplug' in dt and dt['isAlive']() and
                mplug == dt['mplug'] and attrname == dt['attrname']
            )
        return False
    data['eq'] = eq

    return data


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    def _getAttrKeyName(typeinfo):
        return '.' + typeinfo['mfn'].pathName(False, False)  # 先頭にドットが重複しても問題ない

else:
    def _getAttrKeyName(typeinfo):
        return typeinfo['shortname']


def _initAPI1Objects(data):
    u"""
    API1 オブジェクトを初期化する。
    """
    if 'mfn1' in data:
        return

    if 'mplug' in data:
        nodedata = data['noderef']._CyObject__data
        _initAPI1Objects(nodedata)
        mfnnode = nodedata['mfn1']

        # mplug のパスを得て分解。
        attrTkns = _argToFindComplexMPlug(data['mplug'].info.split('.')[1:])

        # ノードからプラグを取得。
        # MPlug から得たパスなので _findMPlug には strict=True を指定でき、それ以上のチェックも不要。
        try:
            # 末尾のプラグを得る。
            mplug1 = _findMPlug(mfnnode, attrTkns, False, True)
            leafIdx = attrTkns.pop(-1)[1]

            # 上位のロジカルインデックスを選択する。
            for i, (name, idx) in enumerate(attrTkns):
                if idx is not None and idx >= 0:  # API1では、負だとエラーになる。
                    mplug1.selectAncestorLogicalIndex(idx, _findMAttr(mfnnode, attrTkns, i, True))

            # 末尾のロジカルインデックスを選択する。
            if leafIdx is not None and leafIdx >= 0:
                mplug1.selectAncestorLogicalIndex(leafIdx)
            data['mplug1'] = mplug1
            data['mfn1'] = getattr(_api1, type(data['typeinfo']['mfn']).__name__)(mplug1.attribute())
        except RuntimeError:
            data['mplug1'] = None
            data['mfn1'] = None

    elif 'mpath' in data:
        mpath1 = _1_mpath(data['getname']())
        data['mpath1'] = mpath1
        data['mnode1'] = mpath1.node()
        data['mfn1'] = getattr(_api1, type(data['mfn']).__name__)(mpath1)

    else:  #if 'mnode' in data:
        mnode1 = _1_mnode(data['getname']())
        data['mnode1'] = mnode1
        data['mfn1'] = getattr(_api1, type(data['mfn']).__name__)(mnode1)


def _setPlugCache(node, plug):
    u"""
    Node に Plug をキャッシュする。

    Plug の後に Node を作った場合に、任意でキャッシュをセットすることができる。
    """
    cache = node._Node_c__plugCache.get(plug._CyObject__data['attrname'])
    if cache is None:
        node._Node_c__plugCache[plug._CyObject__data['attrname']] = {id(type(plug)): plug}
    else:
        cache[id(type(plug))] = plug


def _newNodePlug(pcls, node, mplug, typeinfo=None, typename=None):
    u"""
    Node から Plug インスタンスを得る。

    Node にキャッシュが作られ、キャッシュがヒットすれば再利用される。
    """
    attrname = '.' + mplug.partialName(includeNonMandatoryIndices=True, includeInstancedIndices=True)
    key = id(pcls)

    cache = node._Node_c__plugCache.get(attrname)
    if cache:
        plug = cache.get(key)
        if plug:
            if plug.isValid():
                return plug
            # キャッシュ生成後に、アトリビュートが削除され、同じ名前で追加し直された場合など。
            cache.clear()
            data = _makePlugData(_getObjectRef(node), mplug, typeinfo, typename, attrname)
        else:
            for k in cache:
                data = cache[k]._CyObject__data
                break
    else:
        cache = {}
        node._Node_c__plugCache[attrname] = cache
        data = _makePlugData(_getObjectRef(node), mplug, typeinfo, typename, attrname)

    plug = pcls.newObject(data)
    cache[key] = plug
    return plug


def _newNodeRefPlug(pcls, noderef, mplug, typeinfo=None, typename=None):
    u"""
    Node の ObjectRef から Plug インスタンスを得る。

    Node の参照が生きていれば、Node にキャッシュが作られ、キャッシュがヒットすれば再利用される。
    """
    node = noderef.object()
    if node:
        return _newNodePlug(pcls, node, mplug, typeinfo, typename)
    else:
        return pcls.newObject(_makePlugData(noderef, mplug, typeinfo, typename))


def _decideNodeClsFromData(data):
    u"""
    ノード内部データからクラスを決定する。
    """
    return _decideClass(data['getname'](), data['mfn'].typeName, lambda: data['mfn'])


#def _newNodeFromData(data):
#    u"""
#    ノード内部データのみから Node インスタンスを生成する。
#    """
#    return _decideNodeClsFromData(data).newObject(data)


def _newNodeObjByArgs(args):
    u"""
    `_makeNodeData` と同じ引数リストから Node インスタンスを生成する。
    """
    data = _makeNodeData(*args)
    mfn = args[2]
    return _decideClass(
        args[-1] if len(args) == 4 else data['getname'](),
        mfn.typeName, lambda: mfn).newObject(data)


def _newNodeRefByArgs(args):
    u"""
    `_makeNodeData` と同じ引数リストから Node の ObjectRef を生成する。
    """
    return _newNodeRefFromData(_makeNodeData(*args))


def _newNodeObjByMPath(mpath):
    u"""
    API2 MDagPath から Node インスタンスを生成する。
    """
    mnode = mpath.node()
    mfn = _mnodeFn(mpath, mnode)
    return _decideClass(
        mpath.partialPathName(), mfn.typeName, lambda: mfn
    ).newObject(_makeNodeData(mpath, mnode, mfn))


#------------------------------------------------------------------------------
def _anyClsObjByObj(cls, obj):
    u"""
    クラス指定と CyObject 派生インスタンスから、その複製か参照ラッパーを得る。
    """
    if cls is CyObject:
        cls = type(obj)
    elif cls.CLASS_TYPE is CY_OBJREF:
        return _getObjectRef(obj, cls)
    elif obj.CLASS_TYPE is CY_NODE:
        _checkNodeCls(cls, obj._CyObject__data['mfn'], obj.name(), obj)
    elif obj.CLASS_TYPE is CY_PLUG:
        _checkPlugCls(cls, obj)
    else:
        cls = type(obj)
    return cls.newObject(obj._CyObject__data)


def _nodeClsObjByAPI2(cls, mpath, mnode, mfn, src, name=None):
    u"""
    クラス指定と API2 オブジェクトから Node か ObjectRef インスタンスを得る。
    """
    if cls is CyObject:
        cls = _decideClass(name or (mpath.partialPathName() if mpath else mfn.name()), mfn.typeName, lambda: mfn)
    elif cls.CLASS_TYPE is CY_OBJREF:
        return _newNodeRefFromData(_makeNodeData(mpath, mnode, mfn), cls)
    else:
        _checkNodeCls(cls, mfn, name or (mpath.partialPathName() if mpath else mfn.name()), src)
    return cls.newObject(_makeNodeData(mpath, mnode, mfn))


def _nodeClsObjByMObj(cls, mnode):
    u"""
    クラス指定と API2 MObject から Node か ObjectRef インスタンスを得る。
    """
    if mnode.hasFn(_MFn_kDagNode):
        mpath = _2_getAPathTo(mnode)
        return _nodeClsObjByAPI2(cls, mpath, mnode, _mnodeFn(mpath, mnode), mnode)
    else:
        mfn = _mnodeFn(mnode, mnode)
        return _nodeClsObjByAPI2(cls, None, mnode, mfn, mnode)


def _nodeClsObjByName(cls, name):
    u"""
    クラス指定とノード名から Node か ObjectRef インスタンスを得る。
    """
    sel = _2_MSelectionList()
    try:
        sel.add(name)
    except:
        raise KeyError('not exist: ' + name)

    try:
        mpath = sel.getDagPath(0)
    except TypeError:
        mnode = sel.getDependNode(0)
        return _nodeClsObjByAPI2(cls, None, mnode, _mnodeFn(mnode, mnode), name, name)
    else:
        mnode = mpath.node()
        return _nodeClsObjByAPI2(cls, mpath, mnode, _mnodeFn(mpath, mnode), name, name)


def _plugClsObjByMPlug(cls, mplug, src, nodeArgs=None):
    u"""
    クラス指定と API2 MPlug から Plug オブジェクトインスタンスを得る。
    """
    if cls is CyObject:
        noderef = _newNodeRefFromData(_makeNodeData(*(nodeArgs or _node3ArgsByMPlug(mplug))))
        cls = CyObject._CyObject__glbpcls
    elif cls.CLASS_TYPE is CY_OBJREF:
        noderef = _newNodeRefFromData(_makeNodeData(*(nodeArgs or _node3ArgsByMPlug(mplug))))
        return _newPlugRefFromData(_makePlugData(noderef, mplug))
    else:
        _checkPlugCls(cls, src)
        noderef = _newNodeRefFromData(_makeNodeData(*(nodeArgs or _node3ArgsByMPlug(mplug))))
    return _newNodeRefPlug(cls, noderef, mplug)


def _anyClsObjByName(cls, name):
    u"""
    クラス指定と名前から Node か Plug オブジェクトインスタンスを得る。
    """
    # ノード名指定ならノードを得る。
    tkns = name.split('.')
    if len(tkns) == 1:
        return _nodeClsObjByName(cls, name)

    # ノード名が指定されているなら、そのノードの API2 オブジェクトを得る。
    nodename = tkns[0]
    if nodename:
        sel = _2_MSelectionList()
        try:
            sel.add(nodename)
        except:
            raise KeyError('not exist: ' + name)
        try:
            mpath = sel.getDagPath(0)
        except TypeError:
            mnode = sel.getDependNode(0)
            mpath = None
            mfn = _mnodeFn(mnode, mnode)
        else:
            mnode = mpath.node()
            mfn = _mnodeFn(mpath, mnode)

    # ノード名が省略されているなら、カレントセレクションから得る。
    else:
        sel = _2_getActiveSelectionList()
        try:
            mplug = sel.getPlug(0)
        except IndexError:
            raise KeyError('not exist: ' + name)
        except TypeError:
            pass
        else:
            # getPlugがエラーにならない場合があるので isNull をチェック。
            if not mplug.isNull:
                # TODO: 選択中のプラグの下位のプラグを得る。
                raise NotImplementedError('inferiror plug from selection')

        try:
            mpath = sel.getDagPath(0)
        except TypeError:
            mnode = sel.getDependNode(0)
            mpath = None
            mfn = _mnodeFn(mnode, mnode)
            #nodename = mfn.name()
        else:
            mnode = mpath.node()
            mfn = _mnodeFn(mpath, mnode)
            #nodename = mpath.partialPathName()

    # ノードからプラグを取得。
    argToFind = _argToFindComplexMPlug(tkns[1:])
    try:
        mplug = _findComplexMPlug(mfn, argToFind)

    # 得られなかったらシェイプからの取得も試みる。
    except _MayaAPI2Errors:
        if not mnode.hasFn(_MFn_kTransform):
            raise KeyError('not exist: ' + name)
        try:
            mpath.extendToShape()
        except _MayaAPI2RuntimeError:
            raise KeyError('not exist: ' + name)

        mnode = mpath.node()
        mfn = _mnodeFn(mpath, mnode)
        try:
            mplug = _findComplexMPlug(mfn, argToFind)
        except _MayaAPI2Errors:
            raise KeyError('not exist: ' + name)
        #nodename = mpath.partialPathName()

    return _plugClsObjByMPlug(cls, mplug, name, (mpath, mnode, mfn))


#------------------------------------------------------------------------------
def _checkNodeCls(cls, mfn, nodename, src):
    u"""
    ノード用に指定されたクラスが問題ないかチェックする。

    指定クラスは少なことも Node の派生でなければならず、
    それに紐付いたノードタイプに実際のノードタイプがマッチしなければならない。
    """
    typeName = mfn.typeName
    for typ in _relatedNodeTypes(cls):
        if _isDerivedNodeType(typeName, typ):
            # たとえ未登録のカスタム派生クラスでも、このメソッドがあればチェックされる。
            verify = getattr(cls, '_verifyNode', None)
            if not verify or verify(mfn, nodename):
                return
            break
    raise TypeError('not matched to class ' + cls.__name__ + ': '+ repr(src))


def _checkPlugCls(cls, src=None):
    u"""
    プラグ用に指定されたクラスが問題ないかチェックする。
    """
    if not issubclass(cls, _defaultPlugCls):
        raise TypeError('not matched to class ' + cls.__name__ + ': '+ repr(src))


#------------------------------------------------------------------------------
def _mnodeFn(mpath_or_mobj, mobj, default=None):
    u"""
    ノードの :mayaapi2:`MObject` に対応したファンクションセットを得る。

    :mayaapi2:`MFnDagNode` 系のファンクションセットは
    :mayaapi2:`MObject` か :mayaapi2:`MDagPath` のどちらから生成するかで
    サポートされる機能が違ってくるので注意。

    なお、 |mayaapi2| に未実装なファンクションセットも結構あるので、
    そういった場合は :mayaapi2:`MFnDependencyNode` など抽象的なものになる。

    :param mpath_or_mobj:
        ファンクションセットを生成したいノードの :mayaapi2:`MDagPath` か
        :mayaapi2:`MObject` 。
    :param mobj:
        ファンクションセットを生成したいノードの :mayaapi2:`MObject` 。
    :param default:
        オブジェクトのタイプ専用のファンクションセットが見つからない場合の
        デフォルトをクラスで指定する。
        省略可能で、その場合は内部テーブルから適切なものが探される。
    :returns: ファンクションセットオブジェクト。

    .. warning::
        ジオメトリシェイプに対応したファンクションセット（ :mayaapi2:`MFnMesh`
        など）は、ジオメトリ情報を持っていない空のシェイプをアサインすると、
        あらゆるメソッドがエラーになってしまうので、
        その場合、本関数は :mayaapi2:`MFnDagNode` を生成する。
    """
    # apiType をキーに辞書から得る。
    apiType = mobj.apiType()
    cls = _APITYPE_FNNODE_DICT.get(apiType)

    # 辞書から得られない場合。
    if not cls:
        if default:
            # デフォルトが指定されたなら、それを使う。
            cls = default
        else:
            # 内部辞書から適切なものを探し、辞書を更新する。
            for key in _FNNODE_APITYPES:
                if mobj.hasFn(key):
                    cls = _APITYPE_FNNODE_DICT[key]
                    _APITYPE_FNNODE_DICT[apiType] = cls
                    break
            if not cls:
                raise TypeError('Unknown API Fn Type %s(%d)' % (mobj.apiTypeStr, apiType))

    # ジオメトリを持っていないジオメトリシェイプのファンクションセットはエラーになるので特別処理する。
    try:
        mfn = cls(mpath_or_mobj)  # 2022.0 までは通るが 2022.1 以降は ValueError となる。
        mfn.typeId  # RuntimeError となる。
        return mfn
    except:  # (RuntimeError, ValueError)
        return _2_MFnDagNode(mpath_or_mobj)


def _initFnNodeDict():
    # そのバージョンのノード MFn クラスを得る。
    #[x for x in [getattr(_api2, x) for x in dir(_api2) if x.startswith('MFn')] if _api2.MFnDependencyNode in x.mro()]

    defs = []
    for keyname, clsname in [
        ('kCamera', 'MFnCamera'),  # API2: 2015
        ('kMesh', 'MFnMesh'),
        ('kNurbsCurve', 'MFnNurbsCurve'),  # API2: 2016
        ('kNurbsSurface', 'MFnNurbsSurface'),  # API2: 2016
        ('kTransform', 'MFnTransform'),
        ('kDagNode', 'MFnDagNode'),
        ('kContainer', 'MFnContainerNode'),  # API2: 2016.5
        ('kReference', 'MFnReference'),  # API2: 2016.5, C++: 2013.5
        ('kSet', 'MFnSet'),  # API2: 2016.5
        ('kDependencyNode', 'MFnDependencyNode'),
    ]:
        try:
            defs.append((getattr(_MFn, keyname), getattr(_api2, clsname)))
        except AttributeError:
            pass
    return dict(defs), [x[0] for x in defs]

_APITYPE_FNNODE_DICT, _FNNODE_APITYPES = _initFnNodeDict()


#------------------------------------------------------------------------------
class ModuleForSel(types.ModuleType):
    u"""
    現在のセレクションを反映させるプロパティを追加するモジュールクラス。
    """
    def __init__(self, name):
        u"""
        既存モジュール名を指定して置き換える。
        """
        base = sys.modules[name]
        super(ModuleForSel, self).__init__(name)
        for x in dir(base):
            setattr(self, x, getattr(base, x))
        sys.modules[base.__name__] = self

    @property
    def sel(self):
        u"""
        現在選択されている最初の `.CyObject` を得るプロパティ。

        `selobj` を引数無し(i=0)で呼び出すこととほぼ等しいが、
        何も選択されていない状態だと None となり、エラーにはならない。

        :rtype: `.CyObject` or None
        """
        sel = _2_getActiveSelectionList()
        if sel.length():
        #    return _getObjectBySelIdx(sel, 0)
            return _getSel0WithCache(sel)
        # 選択無しで参照したら、キャッシュをクリアするようにする（明示的に解放できるようにする意図）。
        global _LAST_SEL
        _LAST_SEL = None

    @property
    def selection(self):
        u"""
        現在選択されている `.CyObject` のリストを得るプロパティ。

        `selected` を引数無しで呼び出すことと等しい。
        """
        return self.selected()

    @staticmethod
    def selobj(i=0):
        u"""
        現在選択されている i 番目の `.CyObject` を得る。

        :param `int` i: 参照するセレクションインデックス。
        :rtype: `.CyObject`
        """
        sel = _2_getActiveSelectionList()
        if not i:
            if sel.length():
                return _getSel0WithCache(sel)
        elif 0 <= i < sel.length():
            return _getObjectBySelIdx(sel, i)
        raise IndexError('invalid selection index: ' + str(i))

    @staticmethod
    def selected(sel=None, **kwargs):
        u"""
        セレクションから `CyObject` リストを得る。

        :param sel:
            セレクション情報。
            省略時は現在のセレクションから取得される。

            1つの文字列か `.CyObject` を指定すると、それが `list` 化されて得られる。

            API2 の :mayaapi2:`MSelectionList` も指定できる。

            シーケンスを指定すると、
            セレクションとして解釈された上で `CyObject` リストが得られる。
            シーケンス内は文字列か `CyObject` を混在できる。
        :param kwargs:
            その他に :mayacmd:`ls` コマンドのオプションを指定可能。
        :rtype: `list`
        """
        # 単一CyObject指定の場合、kwargs条件がマッチすればそれを返す。
        if isinstance(sel, CyObject):
            if kwargs and not _ls(sel, **kwargs):
                return []
            return [sel]

        # sel指定無しの場合は、カレントセレクションから。
        if not sel:
            if kwargs:
                kwargs['sl'] = True
                sel = _strsToSelList(_ls(**kwargs))
            else:
                sel = _2_getActiveSelectionList()
            objMap = _objMapFor_getObjectBySelIdx()

        # 単一文字列の指定の場合。
        elif isinstance(sel, BASESTR):
            if kwargs:
                sel = _strsToSelList(_ls(sel, **kwargs))
            else:
                sel = _2_getSelectionListByName(sel)
            objMap = _objMapFor_getObjectBySelIdx()

        # MSelectionList指定の場合。
        elif isinstance(sel, _2_MSelectionList):
            if kwargs:
                sel = _strsToSelList(_ls(sel.getSelectionStrings(), **kwargs))
            objMap = _objMapFor_getObjectBySelIdx()

        # その他（シーケンスとして評価）の場合、そこに含まれる CyObject を優先して返す。
        else:
            srcs = list(sel)
            res = [x for x in srcs if isinstance(x, CyObject)]
            if len(res) == len(srcs):
                return res

            objMap = _objMapFor_getObjectBySelIdx()
            for x in res:
                objMap[x.name()] = x

            sel = _2_getSelectionListByName(str(srcs[0]))
            for x in srcs[1:]:
                sel.merge(_2_getSelectionListByName(str(x)))

        return [_getObjectBySelIdx(sel, i, objMap) for i in range(sel.length())]


#------------------------------------------------------------------------------
def _getSel0WithCache(sel):
    global _LAST_SEL

    # MPlug を取得。
    try:
        mplug = sel.getPlug(0)
    except TypeError:
        mplug = None
    else:
        if mplug.isNull:
            mplug = None

    # MPlug が得られたら、プラグとする。
    if mplug:
        # セレクションからは MDagPath は得られないので MPlug からノードを得る。
        mpath, mnode = _getMPlugNode(mplug)

        # キャッシュがあれば再利用する。
        if _LAST_SEL and _LAST_SEL.isValid():
            dt = _LAST_SEL._CyObject__data

            # キャッシュがプラグなら、それを再利用できればする。またはノードだけでも再利用できればする。
            if _LAST_SEL.CLASS_TYPE is CY_PLUG:
                noderef = dt['noderef']
                if _isSameNodeData(noderef._CyObject__data, mpath, mnode):
                    if dt['attrname'][1:] != mplug.partialName(includeNonMandatoryIndices=True, includeInstancedIndices=True):
                        #print("### reusing cached plug's node, and new plug ###");
                        _LAST_SEL = _newNodeRefPlug(CyObject._CyObject__glbpcls, noderef, mplug)
                    #else:
                    #    print("### reusing cached plug ###");
                    return _LAST_SEL

            # キャッシュがノードなら、ノードだけでも再利用できればする。
            elif _isSameNodeData(dt, mpath, mnode):
                _LAST_SEL = _newNodePlug(CyObject._CyObject__glbpcls, _LAST_SEL, mplug)
                #print("### reusing cached node, and new plug ###");
                return _LAST_SEL

        # キャッシュが利用できなければ新規に生成。
        _LAST_SEL = _newNodeRefPlug(
            CyObject._CyObject__glbpcls,
            _newNodeRefFromData(_makeNodeData(mpath, mnode, _mnodeFn(mpath or mnode, mnode))),
            mplug)

    # MPlug が得られなかったら、ノードとする。
    else:
        # ノードの MDagPath や MObject を取得。
        try:
            mpath = sel.getDagPath(0)
        except TypeError:
            mpath = None
            mnode = sel.getDependNode(0)
        else:
            mnode = mpath.node()

        # キャッシュがあれば再利用する。
        if _LAST_SEL and _LAST_SEL.isValid():
            dt = _LAST_SEL._CyObject__data

            # キャッシュがプラグなら、そのノードを再利用できればする。
            if _LAST_SEL.CLASS_TYPE is CY_PLUG:
                noderef = dt['noderef']
                if _isSameNodeData(noderef._CyObject__data, mpath, mnode):
                    _LAST_SEL = noderef()
                    #print("### reusing cached plug's node ###");
                    return _LAST_SEL

            # キャッシュがノードなら、それを再利用できればする。
            elif _isSameNodeData(dt, mpath, mnode):
                #print("### reusing cached node ###");
                return _LAST_SEL

        # キャッシュが利用できなければ新規に生成。
        if mpath:
            _LAST_SEL = _newNodeObjByArgs((mpath, mnode, _mnodeFn(mpath, mnode), mpath.partialPathName()))
        else:
            mfn = _mnodeFn(mnode, mnode)
            _LAST_SEL = _newNodeObjByArgs((mpath, mnode, mfn, mfn.name()))

    return _LAST_SEL

_LAST_SEL = None


def _isSameNodeData(data, mpath, mnode):
    if mpath:
        mp = data.get('mpath')
        return mp and mp == mpath
    return mnode == data['mnode']


def _objMapFor_getObjectBySelIdx():
    if _LAST_SEL and _LAST_SEL.isValid():
        if _LAST_SEL.CLASS_TYPE is CY_PLUG:
            #ref = _LAST_SEL.noderef()
            #return {ref.name_(): (ref, [_LAST_SEL])}

            # _getObjectBySelIdx は重複アイテムの再利用を考慮した実装ではないため、
            # プラグを再利用させるために、ノード実体化してプラグキャッシュ化する。
            node = _LAST_SEL.node()
            return {node.name_(): (node, None)}
        else:
            return {_LAST_SEL.name_(): (_LAST_SEL, None)}
    return {}


def _strsToSelList(strs):
    sel = _2_getSelectionListByName(strs[0])
    for s in strs[1:]:
        sel.merge(_2_getSelectionListByName(s))
    return sel


#------------------------------------------------------------------------------
def _getObjectBySelIdx(sel, idx, objMap=None):
    u"""
    検証済みセレクションインデックスから Node か Plug オブジェクトインスタンスを得る。

    objMap には Node ごとに、ノードとプラグをキャッシュする。
    MSelectionList にアイテムが重複することはないので、
    同じアイテムの再利用を目的とするわけではない。
    Plug 間で同じノードの ObjectRef をシェアし、さらにその Node も
    実体化される際にはその中に Plug もキャッシュされることを仕向ける。
    """
    try:
        mplug = sel.getPlug(idx)
    except TypeError:
        mplug = None
    else:
        if mplug.isNull:
            mplug = None

    if objMap is None:
        if mplug:
            return _newNodeRefPlug(CyObject._CyObject__glbpcls, _newNodeRefFromData(_makeNodeData(*_node3ArgsByMPlug(mplug))), mplug)
        else:
            return _newNodeObjByArgs(_node4ArgsBySelIdx(sel, idx))

    else:
        if mplug:
            nodeArgs = _node4ArgsByMPlug(mplug)
        else:
            nodeArgs = _node4ArgsBySelIdx(sel, idx)
        name = nodeArgs[-1]
        obj = objMap.get(name)

        # (node, plugs) をキャッシュする。
        # plugs が None なら node は Node 実体。
        # plugs が Plug list なら node は ObjectRef となる。
        # node が ObjectRef の間は plugs に Plug が蓄積される。
        if mplug:
            if obj:
                obj, plugs = obj
                if plugs is None:
                    plug = _newNodeRefPlug(CyObject._CyObject__glbpcls, _getObjectRef(obj), mplug)
                else:
                    plug = _newNodeRefPlug(CyObject._CyObject__glbpcls, obj, mplug)
                    plugs.append(plug)
            else:
                obj = _newNodeRefFromData(_makeNodeData(*nodeArgs))
                plug = _newNodeRefPlug(CyObject._CyObject__glbpcls, obj, mplug)
                objMap[name] = (obj, [plug])
            return plug

        else:
            if obj:
                node, plugs = obj
                if plugs:
                    node = node()
                    for p in plugs:
                        _setPlugCache(node, p)
            else:
                node = _newNodeObjByArgs(nodeArgs)
            objMap[name] = (node, None)
            return node


def _getObjRefBySelIdx(sel, idx, cls, objMap=None):
    u"""
    検証済みセレクションインデックスから ObjectRef インスタンスを得る。
    """
    if objMap is None:
        # objMap が指定されなければ、キャッシュで共有はしないので、
        # Node や Plug のインスタンスを作らずに、いきなり ObjectRef を作る。
        # Plug を Node にキャッシュもされない。
        try:
            mplug = sel.getPlug(idx)
        except TypeError:
            mplug = None
        else:
            if mplug.isNull:
                mplug = None

        if mplug:
            return _newPlugRefFromData(_makePlugData(_newNodeRefFromData(_makeNodeData(*_node3ArgsByMPlug(mplug))), mplug), cls)
        else:
            return _newNodeRefFromData(_makeNodeData(*_node3ArgsBySelIdx(sel, idx)), cls)

    else:
        # objMap が指定された場合、Plug を Node にキャッシュすることも考慮し、
        # 一度 Node や Plug のインスタンスを作ってから ObjectRef でラップする。
        return _getObjectRef(_getObjectBySelIdx(sel, idx, objMap), cls)


def _getNodeObjBySelIdx(sel, idx, basecls=None):
    u"""
    検証済みセレクションインデックスから Node オブジェクトインスタンスを得る。

    MSelectionList 内での重複はありえないため共有キャッシュは不要。
    """
    try:
        mplug = sel.getPlug(idx)
    except TypeError:
        mplug = None
    else:
        if mplug.isNull:
            mplug = None
    if mplug:
        nodeArgs = _node4ArgsByMPlug(mplug)
    else:
        nodeArgs = _node4ArgsBySelIdx(sel, idx)

    name = nodeArgs[-1]
    mfn = nodeArgs[-2]
    cls = _decideClass(name, mfn.typeName, lambda: mfn, basecls)

    if cls:
        return cls.newObject(_makeNodeData(*nodeArgs))


def _getPlugObjBySelIdx(sel, idx, pcls, objMap=None):
    u"""
    検証済みセレクションインデックスから Plug オブジェクトインスタンスを得る。

    objMap に Node の ObjectRef をキャッシュして、複数の Plug でシェアさせる。
    MSelectionList 内での重複はありえないため Plug はキャッシュしない。
    Node は ObjectRef にするだけなので Node にも Plug はキャッシュされない。
    """
    try:
        mplug = sel.getPlug(idx)
    except TypeError:
        return
    if mplug.isNull:
        return

    if objMap is None:
        return _newNodeRefPlug(pcls, _newNodeRefFromData(_makeNodeData(*_node3ArgsByMPlug(mplug))), mplug)

    else:
        nodeArgs = _node4ArgsByMPlug(mplug)
        name = nodeArgs[-1]
        noderef = objMap.get(name)
        if not noderef:
            noderef = _newNodeRefFromData(_makeNodeData(*nodeArgs))
            objMap[name] = noderef
        return _newNodeRefPlug(pcls, noderef, mplug)


#------------------------------------------------------------------------------
#def _node3ArgsByObj(mpath, mnode):
#    return mpath, mnode, _mnodeFn(mpath or mnode, mnode)


#def _node4ArgsByObj(mpath, mnode):
#    if mpath:
#        return mpath, mnode, _mnodeFn(mpath, mnode), mpath.partialPathName()
#    else:
#        mfn = _mnodeFn(mnode, mnode)
#        return None, mnode, mfn, mfn.name()


def _node3ArgsBySelIdx(sel, idx):
    u"""
    検証済みセレクションインデックスから、ノード用の3個の引数を得る。
    """
    try:
        mpath = sel.getDagPath(idx)
    except TypeError:
        mnode = sel.getDependNode(idx)
        return None, mnode, _mnodeFn(mnode, mnode)
    else:
        mnode = mpath.node()
        return mpath, mnode, _mnodeFn(mpath, mnode)


def _node4ArgsBySelIdx(sel, idx):
    u"""
    検証済みセレクションインデックスから、ノード用の4個（3個+名前）の引数を得る。
    """
    try:
        mpath = sel.getDagPath(idx)
    except TypeError:
        mnode = sel.getDependNode(idx)
        mfn = _mnodeFn(mnode, mnode)
        return None, mnode, mfn, mfn.name()
    else:
        mnode = mpath.node()
        return mpath, mnode, _mnodeFn(mpath, mnode), mpath.partialPathName()


def _node3ArgsByMPlug(mplug):
    u"""
    API2 MPlug からノード用の3個の引数を得る。

    worldSpace プラグならインスタンスインデックが加味される。
    """
    mpath, mnode = _getMPlugNode(mplug)
    if mpath:
        return mpath, mnode, _mnodeFn(mpath, mnode)
    else:
        mfn = _mnodeFn(mnode, mnode)
        return None, mnode, mfn


def _node4ArgsByMPlug(mplug):
    u"""
    API2 MPlug からノード用の4個（3個+名前）の引数を得る。

    worldSpace プラグならインスタンスインデックが加味される。
    """
    mpath, mnode = _getMPlugNode(mplug)
    if mpath:
        return mpath, mnode, _mnodeFn(mpath, mnode), mpath.partialPathName()
    else:
        mfn = _mnodeFn(mnode, mnode)
        return None, mnode, mfn, mfn.name()


def _getMPlugNode(mplug):
    u"""
    MPlug からノードを得る。

    worldSpace プラグならインスタンスインデックスが加味される。

    :returns: MDagPath, MObject
    """
    mnode = mplug.node()
    if mnode.hasFn(_MFn_kDagNode):
        if _2_MFnAttribute(mplug.attribute()).worldSpace:
            # NOTE: getAllPathsTo で得たものをそのまま使うとクラッシュすることがあるので複製。
            idx = 0
            mpaths = _2_getAllPathsTo(mnode)
            if len(mpaths) >= 2:
                root = mplug
                isElem = root.isElement
                c = root.array() if isElem else root
                while c.isChild:
                    root = c.parent()
                    isElem = root.isElement
                    c = root.array() if isElem else root
                if isElem:
                    idx = max(0, root.logicalIndex())
            return _2_MDagPath(mpaths[idx]), mnode
        else:
            return _2_getAPathTo(mnode), mnode
    else:
        return None, mnode

