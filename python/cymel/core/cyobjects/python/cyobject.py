# -*- coding: utf-8 -*-
u"""
Mayaラッパーオブジェクトの抽象基底クラス。
"""
import sys
import types
from ...common import *
from ..typeinfo import isDerivedNodeType as _isDerivedNodeType
from ..typeregistry import nodetypes
from ._api2mplug import (
    _1_mpath, _1_mnode,
    makePlugTypeInfo,
)
import maya.api.OpenMaya as _api2
import maya.OpenMaya as _api1

__all__ = [
    'BIT_DAGNODE', 'BIT_TRANSFORM', 'BIT_SHAPE',
    'CyObject', 'O',
    'cyObjects', 'Os',
    'ModuleForSel',
]

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
#_2_getSelectionListByName = _api2.MGlobal.getSelectionListByName

_ls = cmds.ls

_decideClass = nodetypes._NodeTypes__decideClass
_relatedNodeTypes = nodetypes.relatedNodeTypes

_object_new = object.__new__

#------------------------------------------------------------------------------
BIT_DAGNODE = 0b0001  #: ノードクラスで dagNode の特徴をサポートしていることを示す。
BIT_TRANSFORM = 0b0010  #: ノードクラスで transform の特徴をサポートしていることを示す。
BIT_SHAPE = 0b0100  #: ノードクラスで shape の特徴をサポートしていることを示す。


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

    CLASS_TYPE = 0  #: ラッパークラスの種類を表す (0=CyObject, 1=Node, 2=Plug, -1=ObjectRef)

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
                raise ValueError('Networked plug is specified')
            return _plugClsObjByMPlug(cls, src, src)

        # その他の場合、文字列として評価する。
        return _anyClsObjByName(cls, str(src))

    def __nonzero__(self):
        # bool 評価などで __len__ が呼ばれないようにするためにも非常に重要。
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
        isNode = cls.CLASS_TYPE is 1
        if isNode:
            typs = _relatedNodeTypes(cls)
            kwargs['type'] = typs

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

        if cls.CLASS_TYPE is 2:
            return [x for x in [_getPlugObjBySelIdx(sel, i, cls, objMap) for i in range(num)] if x]
        elif cls.CLASS_TYPE is -1:
            return [_getObjRefBySelIdx(sel, i, cls, objMap) for i in range(num)]
        else:
            return [_getObjectBySelIdx(sel, i, objMap) for i in range(num)]

    if MAYA_VERSION >= (2016,):
        @classmethod
        def fromUUID(cls, val):
            u"""
            UUID からノードリストを得る。

            重複も起こり得るので、戻り値はリストである。

            :param `str` val:
                単一のUUIDかそのリスト。
            :rtype: `list`
            """
            return [cls(x) for x in (_ls(val) or EMPTY_TUPLE)]

_defaultPlugCls = None  #: Plug が import 後にセットされる。

O = CyObject  #: `CyObject` の別名。


def cyObjects(val):
    u"""
    名前リストなどから `CyObject` のリストを得る。

    :param iterable val:
        ノード名やプラグ名や同等の評価が可能なもののリスト。
        単一の名前の場合はそれのみのリスト、
        None などの場合は空リストと解釈されるので、
        Mayaコマンドの返値をそのまま受けられることが多い。
    :rtype: `list`
    """
    if not vals:
        return []
    elif isinstance(val, BASESTR):
        return [O(val)]
    else:
        return [O(v) for v in val]

Os = cyObjects  #: `cyObjects` の別名。


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
                    (self.refclass() if self.CLASS_TYPE is -1 else self).TYPE_BITS and
                    (other.refclass() if other.CLASS_TYPE is -1 else other).TYPE_BITS
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
    node_getname = noderef._CyObject__data['getname']
    data = {
        'hash': hash((noderef._CyObject__data['hash'], attrname)),
        'mplug': mplug,
        'noderef': noderef,
        'attrname': attrname,
        'typeinfo': typeinfo,
        'getname': lambda: node_getname() + attrname,
        'elemIdxAttrs': None,
    }

    attr_isAlive = typeinfo['isAlive']
    if attr_isAlive:
        node_isAlive = noderef._CyObject__data['isAlive']
        node_isValid = noderef._CyObject__data['isValid']
        node_hasAttr = noderef._CyObject__data['mfn'].hasAttribute
        shortname = typeinfo['shortname']
        data['isValid'] = lambda: attr_isAlive() and node_isValid() and node_hasAttr(shortname)
        isAlive = lambda: attr_isAlive() and node_isAlive()
    else:
        data['isValid'] = noderef._CyObject__data['isValid']
        isAlive = noderef._CyObject__data['isAlive']
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

        # ノードからプラグを得る為に、マルチプラグのインデックスを収集する。
        attrTkns = [s.split('[') for s in data['mplug'].info.split('.')[1:]]
        ss = attrTkns.pop(-1)
        leafName = ss[0]
        leafIdx = int(ss[1][:-1]) if len(ss) > 1 else None
        ancestorIdxs = [(ss[0], int(ss[1][:-1])) for ss in attrTkns if len(ss) > 1]

        # ノードからプラグを取得。
        try:
            # 末尾のプラグを得る。
            mplug1 = mfnnode.findPlug(leafName, False)

            # 上位のロジカルインデックスを選択する。
            for name, i in ancestorIdxs:
                mplug1.selectAncestorLogicalIndex(i, mfnnode.attribute(name))

            # 末尾のロジカルインデックスを選択する。
            if leafIdx is not None:
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
            return plug
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
        args[-1] if len(args) is 4 else data['getname'](),
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
    elif cls.CLASS_TYPE is -1:
        return _getObjectRef(obj, cls)
    elif obj.CLASS_TYPE is 1:
        _checkNodeCls(cls, obj._CyObject__data['mfn'], obj.name(), obj)
    elif obj.CLASS_TYPE is 2:
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
    elif cls.CLASS_TYPE is -1:
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
    elif cls.CLASS_TYPE is -1:
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
    if len(tkns) is 1:
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
            if mplug.isNull:
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
    ancestorIdxs, leafName, leafIdx = _argsToFindComplexMPlug(tkns[1:])
    try:
        mplug = _findComplexMPlug(mfn, ancestorIdxs, leafName, leafIdx)

    # 得られなかったらシェイプからの取得も試みる。
    except RuntimeError:
        if not mnode.hasFn(_MFn_kTransform):
            raise KeyError('not exist: ' + name)
        try:
            mpath.extendToShape()
        except RuntimeError:
            raise KeyError('not exist: ' + name)

        mnode = mpath.node()
        mfn = _mnodeFn(mpath, mnode)
        try:
            mplug = _findComplexMPlug(mfn, ancestorIdxs, leafName, leafIdx)
        except RuntimeError:
            raise KeyError('not exist: ' + name)
        #nodename = mpath.partialPathName()

    return _plugClsObjByMPlug(cls, mplug, name, (mpath, mnode, mfn))


#------------------------------------------------------------------------------
def _checkNodeCls(cls, mfn, nodename, src=None):
    u"""
    ノード用に指定されたクラスが問題ないかチェックしつつクラスを決定する。

    指定クラスは少なことも Node の派生でなければならず、
    それに紐付いたノードタイプに実際のノードタイプがマッチしなければならない。
    """
    for typ in _relatedNodeTypes(cls):
        if _isDerivedNodeType(mfn.typeName, typ):
            # たとえ未登録のカスタム派生クラスでも、このメソッドがあればチェックされる。
            verify = getattr(cls, '_verifyNode', None)
            if not verify or verify(mfn, nodename):
                return True
    if src:
        raise TypeError('not matched to class ' + cls.__name__ + ': '+ repr(src))
    return False


def _checkPlugCls(cls, src=None):
    u"""
    プラグ用に指定されたクラスが問題ないかチェックしつつクラスを決定する。
    """
    if issubclass(cls, _defaultPlugCls):
        return True
    if src:
        raise TypeError('not matched to class ' + cls.__name__ + ': '+ repr(src))
    return False


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
        mfn = cls(mpath_or_mobj)
        mfn.typeId
        return mfn
    except RuntimeError:
        return _2_MFnDagNode(mpath_or_mobj)


def _initFnNodeDict():
    # そのバージョンのノード MFn クラスを得る。
    #[x for x in [getattr(_api2, x) for x in dir(_api2) if x.startswith('MFn')] if _api2.MFnDependencyNode in x.mro()]

    defs = []
    for keyname, clsname in [
        ('kCamera', 'MFnCamera'),
        ('kMesh', 'MFnMesh'),
        ('kNurbsCurve', 'MFnNurbsCurve'),
        ('kNurbsSurface', 'MFnNurbsSurface'),
        ('kTransform', 'MFnTransform'),
        ('kDagNode', 'MFnDagNode'),
        ('kContainer', 'MFnContainerNode'),
        ('kReference', 'MFnReference'),
        ('kSet', 'MFnSet'),
        ('kDependencyNode', 'MFnDependencyNode'),
    ]:
        try:
            defs.append((getattr(_MFn, keyname), getattr(_api2, clsname)))
        except AttributeError:
            pass
    return dict(defs), [x[0] for x in defs]

_APITYPE_FNNODE_DICT, _FNNODE_APITYPES = _initFnNodeDict()


#------------------------------------------------------------------------------
def _findComplexMPlug(mfnnode, ancestorIdxs, leafName, leafIdx, wantNetworked=False):
    u"""
    プラグ階層途中の省略表記やインデックス -1 などにも対応して MPlug を得る。

    :param `iterable` ancestorIdxs:
        途中のマルチアトリビュート部のインデックスを選択する為の
        名前とインデックスのペアのシーケンス。
    :param `str` leafName:
        末尾のアトリビュート名。
    :param `int` leafIdx:
        末尾がマルチエレメントの場合のインデックス。
        そうでない場合は None を指定。
    """
    # 末尾のプラグを得る。
    if ancestorIdxs or leafIdx is not None:
        mplug = mfnnode.findPlug(leafName, wantNetworked)
    else:
        # コンパウンドやマルチエレメントでない名前が指定された場合はエイリアス名の可能性がある。
        try:
            mplug = mfnnode.findPlug(leafName, wantNetworked)
        except RuntimeError:
            mattr = mfnnode.findAlias(leafName)
            if mattr.isNull():
                raise
            mplug = mfnnode.findPlug(mattr, False)

    # 上位のロジカルインデックスを選択する。
    for name, idx in ancestorIdxs:
        mplug.selectAncestorLogicalIndex(idx, mfnnode.attribute(name))

    # 末尾のロジカルインデックスを選択する。
    if leafIdx is not None:
        if wantNetworked:
            mplug = mplug.elementByLogicalIndex(leafIdx)
        else:
            mplug.selectAncestorLogicalIndex(leafIdx)
    return mplug


def _argsToFindComplexMPlug(attrPathTkns):
    u"""
    プラグ名トークンから _findComplexMPlug の為の引数を構成する。

    :param `iterable` attrPathTkns:
        ノード名部分を含まないアトリビュートパスを
        ドッドで分離したリスト。
    :returns: ancestorIdxs, leafName, leafIdx
    """
    attrTkns = [s.split('[') for s in attrPathTkns]
    ss = attrTkns.pop(-1)
    leafName = ss[0]
    leafIdx = int(ss[1][:-1]) if len(ss) > 1 else None
    return [(ss[0], int(ss[1][:-1])) for ss in attrTkns if len(ss) > 1], leafName, leafIdx


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

        `selobj` を引数無し(i=0)で呼び出すことと等しい。

        :rtype: `.CyObject` or None
        """
        sel = _2_getActiveSelectionList()
        if sel.length():
            return _getObjectBySelIdx(sel, 0)

    @property
    def selection(self):
        u"""
        現在選択されている `.CyObject` のリストを得るプロパティ。

        `selected` を引数無しで呼び出すことと等しい。
        """
        return self.selected()

    @staticmethod
    def selobj(self, i=0):
        u"""
        現在選択されている i 番目の `.CyObject` を得る。

        :param `int` i: 参照するセレクションインデックス。
        :rtype: `.CyObject`
        """
        sel = _2_getActiveSelectionList()
        if 0 <= i < sel.length():
            return _getObjectBySelIdx(sel, i)
        raise IndexError('invalid selection index: ' + str(i))

    @staticmethod
    def selected(sel=None):
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
        :rtype: `list`
        """
        if not sel:
            sel = _2_getActiveSelectionList()
            objMap = {}
            return [_getObjectBySelIdx(sel, i, objMap) for i in range(sel.length())]

        if isinstance(sel, CyObject):
            return [sel]

        objMap = {}

        if isinstance(sel, BASESTR):
            sel = _2_getSelectionListByName(sel)
            return [_getObjectBySelIdx(sel, i, objMap) for i in range(sel.length())]

        if isinstance(sel, _2_MSelectionList):
            return [_getObjectBySelIdx(sel, i, objMap) for i in range(sel.length())]

        sel = list(sel)
        objs = [x for x in sel if isinstance(x, CyObject)]
        if len(objs) == len(sel):
            return objs
        objs = dict([(x.name(), x) for x in objs])

        mayasel = _2_getSelectionListByName(str(sel[0]))
        for x in sel[1:]:
            mayasel.merge(_2_getSelectionListByName(str(x)))

        res = [_getObjectBySelIdx(mayasel, i, objMap) for i in range(mayasel.length())]
        if objs:
            return [objs.get(x.name_(), x) for x in res]
        return res


#------------------------------------------------------------------------------
def _getObjectBySelIdx(sel, idx, objMap=None):
    u"""
    検証済みセレクションインデックスから Node か Plug オブジェクトインスタンスを得る。

    objMap には Node ごとに、ノードとプラグをキャッシュし、
    同じノードのプラグは同じ ObjectRef をシェアし、
    さらにそのノードも実体化されるなら、その中に Plug もキャッシュされる。
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
            return _newNodeRefPlug(CyObject._CyObject__glbpcls, _newNodeRefFromData(_makeNodeData(*_node3ArgsBySelIdx(sel, idx))), mplug)
        else:
            return _newNodeObjByArgs(_node4ArgsBySelIdx(sel, idx))

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
            return _newPlugRefFromData(_makePlugData(_newNodeRefFromData(_makeNodeData(*_node3ArgsBySelIdx(sel, idx))), mplug), cls)
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
        return _newNodeRefPlug(pcls, _newNodeRefFromData(_makeNodeData(*_node3ArgsBySelIdx(sel, idx))), mplug)

    else:
        nodeArgs = _node4ArgsBySelIdx(sel, idx)
        name = nodeArgs[-1]
        noderef = objMap.get(name)
        if not noderef:
            noderef = _newNodeRefFromData(_makeNodeData(*nodeArgs))
            objMap[name] = noderef
        return _newNodeRefPlug(pcls, noderef, mplug)


#------------------------------------------------------------------------------
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
    mnode = mplug.node()
    if mnode.hasFn(_MFn_kDagNode):
        if _2_MFnAttribute(mplug.attribute()).worldSpace:
            mpaths = _2_getAllPathsTo(mnode)
            if len(mpaths) > 2:
                while mplug.isChild:
                    mplug = mplug.parent()
                mpath = mpaths[max(0, mplug.logicalIndex())]
            else:
                mpath = mpaths[0]
        else:
            mpath = _2_getAPathTo(mnode)
        return mpath, mnode, _mnodeFn(mpath, mnode)
    else:
        mfn = _mnodeFn(mnode, mnode)
        return None, mnode, mfn


def _node4ArgsByMPlug(mplug):
    u"""
    API2 MPlug からノード用の4個（3個+名前）の引数を得る。

    worldSpace プラグならインスタンスインデックが加味される。
    """
    mnode = mplug.node()
    if mnode.hasFn(_MFn_kDagNode):
        if _2_MFnAttribute(mplug.attribute()).worldSpace:
            mpaths = _2_getAllPathsTo(mnode)
            if len(mpaths) > 2:
                while mplug.isChild:
                    mplug = mplug.parent()
                mpath = mpaths[max(0, mplug.logicalIndex())]
            else:
                mpath = mpaths[0]
        else:
            mpath = _2_getAPathTo(mnode)
        return mpath, mnode, _mnodeFn(mpath, mnode), mpath.partialPathName()
    else:
        mfn = _mnodeFn(mnode, mnode)
        return None, mnode, mfn, mfn.name()

