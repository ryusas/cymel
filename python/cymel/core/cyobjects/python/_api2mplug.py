# -*- coding: utf-8 -*-
u"""
API2 の :mayaapi2:`MPlug` による操作のサポート。
"""
from ...common import *
from ..datatypes import Matrix, Transformation
import maya.api.OpenMaya as _api2
import maya.OpenMaya as _api1

__all__ = [
    'nonNetworkedElemMPlug', 'toNonNetworkedElemMPlug',
    'nonNetworkedMPlug', 'toNonNetworkedMPlug',

    'getConnWithoutUC',
    'getMPlugName',

    'makePlugTypeInfo', 'fixUnitTypeInfo',
    'mplugGetRawValue', 'mplugGetUnitValue',
    'dataToValue',
    'attrToRawValue', 'unitAttrToRawValue',
    'attrToUnitValue', 'unitAttrToUnitValue',
    'attrFromRawValue', 'attrFromUnitValue',
    'mplugCurrentValueSetter',
    'mplugApiValueSetter',
    'mplug_get_nums',
    'mplug_get_xformmatrix',
    'mplug_get_matrix',
]

#------------------------------------------------------------------------------
if MAYA_VERSION < (2015,):
    raise NotImplementedError('The python version of cymel.core is only supported starting with Maya 2015.')
#------------------------------------------------------------------------------

_MFn = _api2.MFn
_MFn_kDagNode = _MFn.kDagNode
_2_MObjectHandle = _api2.MObjectHandle
_2_MPlug = _api2.MPlug
_2_MFnDagNode = _api2.MFnDagNode
_2_MFnDependencyNode = _api2.MFnDependencyNode
_2_MFnAttribute = _api2.MFnAttribute
_2_MFnNumericAttribute = _api2.MFnNumericAttribute
_2_MFnTypedAttribute = _api2.MFnTypedAttribute
_2_MFnTypedAttribute = _api2.MFnTypedAttribute
_2_MFnNumericData = _api2.MFnNumericData
_2_MFnMatrixData = _api2.MFnMatrixData
_2_MFnStringData = _api2.MFnStringData
_2_MFnStringArrayData = _api2.MFnStringArrayData
_2_MFnDoubleArrayData = _api2.MFnDoubleArrayData
_2_MFnIntArrayData = _api2.MFnIntArrayData
_2_MFnVectorArrayData = _api2.MFnVectorArrayData
_2_MFnPointArrayData = _api2.MFnPointArrayData
_2_MAngle = _api2.MAngle
_2_MDistance = _api2.MDistance
_2_MTime = _api2.MTime
_2_MMatrix = _api2.MMatrix
_2_MFloatMatrix = _api2.MFloatMatrix
_2_MVector = _api2.MVector
_2_MPoint = _api2.MPoint
_2_MColor = _api2.MColor
_2_MFloatVector = _api2.MFloatVector
#_2_MFloatVectorArray = _api2.MFloatVectorArray
#_2_MPointArray = _api2.MPointArray
if MAYA_VERSION >= (2016,):
    _2_MFnMatrixArrayData = _api2.MFnMatrixArrayData

_2_MObject_kNullObj = _api2.MObject.kNullObj

_2_MAngle_uiUnit = _2_MAngle.uiUnit
_2_MAngle_rawToUI = _2_MAngle.internalToUI
#_2_MAngle_uiToRaw = _2_MAngle.uiToInternal
_2_MAngle_asUI = lambda x: x.asUnits(_2_MAngle_uiUnit())
_2_MAngle_fromUI = lambda x: _2_MAngle(x, _2_MAngle_uiUnit())

_2_MDistance_uiUnit = _2_MDistance.uiUnit
_2_MDistance_rawToUI = _2_MDistance.internalToUI
#_2_MDistance_uiToRaw = _2_MDistance.uiToInternal
_2_MDistance_asUI = lambda x: x.asUnits(_2_MDistance_uiUnit())
_2_MDistance_fromUI = lambda x: _2_MDistance(x, _2_MDistance_uiUnit())

_2_MTime_uiUnit = _2_MTime.uiUnit
_2_MTime_kSeconds = _2_MTime.kSeconds
_2_MTime_rawToUI = lambda x: _2_MTime(x, _2_MTime_kSeconds).asUnits(_2_MTime_uiUnit())
#_2_MTime_uiToRaw = lambda x: _2_MTime(x, _2_MTime_uiUnit()).asUnits(_2_MTime_kSeconds)
_2_MTime_asUI = lambda x: x.asUnits(_2_MTime_uiUnit())
_2_MTime_asRaw = lambda x: x.asUnits(_2_MTime_kSeconds)
_2_MTime_fromRaw = lambda x: _2_MTime(x, _2_MTime_kSeconds)
_2_MTime_fromUI = lambda x: _2_MTime(x, _2_MTime_uiUnit())

_MFnData_kMatrix = _api2.MFnData.kMatrix
_MFn_kMatrixData = _MFn.kMatrixData
_MFn_kInvalid = _MFn.kInvalid

_1_MDagPathArray = _api1.MDagPathArray
_1_MDagPath_getAllPathsTo = _api1.MDagPath.getAllPathsTo
_1_MSelectionList = _api1.MSelectionList
_1_MGlobal_getActiveSelectionList = _api1.MGlobal.getActiveSelectionList
_1_MObject = _api1.MObject
_1_MDagPath = _api1.MDagPath
_1_MFnDependencyNode = _api1.MFnDependencyNode
_1_MObject_kNullObj = _api1.cvar.MObject_kNullObj
_api1_executeCommand = _api1.MGlobal.executeCommand

_setAttr = cmds.setAttr
_getAttr = cmds.getAttr

_X_fromSetAttrCmds = Transformation.fromSetAttrCmds

_UnitConvTypes = frozenset([_MFn.kUnitConversion, _MFn.kUnitToTimeConversion, _MFn.kTimeToUnitConversion])

_RE_ADDATTR_AT_search = re.compile(r'-at "([^"]+)"').search
_RE_ADDATTR_DT_search = re.compile(r'-dt "([^"]+)"').search
_RE_ADDATTR_ATDT_search = re.compile(r'-(at|dt) "([^"]+)"').search


def _through(x):
    return x


#------------------------------------------------------------------------------
def nonNetworkedElemMPlug(multi, elem):
    u"""
    マルチ要素が Networked なら Non-Networked に補正する。

    :type multi: :mayaapi2:`MPlug`
    :param multi: Non-Networked なマルチ MPlug 。
    :type elem: :mayaapi2:`MPlug`
    :param elem: 何らかの手段で取得した要素 MPlug 。
    :rtype: :mayaapi2:`MPlug`
    """
    if elem.isNetworked:
        return _2_MPlug(multi).selectAncestorLogicalIndex(elem.logicalIndex())
    return elem


def toNonNetworkedElemMPlug(multi, elem):
    u"""
    Networked なマルチ要素を Non-Networked に補正する。

    :type multi: :mayaapi2:`MPlug`
    :param multi: Non-Networked なマルチ MPlug 。
    :type elem: :mayaapi2:`MPlug`
    :param elem: 何らかの手段で取得した要素 MPlug 。
    :rtype: :mayaapi2:`MPlug`
    """
    return _2_MPlug(multi).selectAncestorLogicalIndex(elem.logicalIndex())


def nonNetworkedMPlug(mplug):
    u"""
    MPlug が Networked なら Non-Networked に補正する。

    :type mplug: :mayaapi2:`MPlug`
    :param mplug: 何らかの手段で取得した MPlug 。
    :rtype: :mayaapi2:`MPlug`
    """
    if mplug.isNetworked:
        # toNonNetworkedMPlug と同じ処理。
        mattr = mplug.attribute()
        if mp.isElement:
            idxAttrs = [(mplug.logicalIndex(), mattr)]
            mp = mplug.array()
        else:
            idxAttrs = []
            mp = mplug
        while mp.isChild:
            mp = mp.parent()
            if mp.isElement:
                idxAttrs.append((mp.logicalIndex(), mp.attribute()))
                mp = mp.array()

        mplug = _2_MPlug(mplug.node(), mattr)
        for idxAttr in idxAttrs:
            mplug.selectAncestorLogicalIndex(*idxAttr)

    return mplug


def toNonNetworkedMPlug(mplug):
    u"""
    Networked な MPlug を Non-Networked に補正する。

    :type mplug: :mayaapi2:`MPlug`
    :param mplug: 何らかの手段で取得した MPlug 。
    :rtype: :mayaapi2:`MPlug`
    """
    mattr = mplug.attribute()
    if mp.isElement:
        idxAttrs = [(mplug.logicalIndex(), mattr)]
        mp = mplug.array()
    else:
        idxAttrs = []
        mp = mplug
    while mp.isChild:
        mp = mp.parent()
        if mp.isElement:
            idxAttrs.append((mp.logicalIndex(), mp.attribute()))
            mp = mp.array()

    mplug = _2_MPlug(mplug.node(), mattr)
    for idxAttr in idxAttrs:
        mplug.selectAncestorLogicalIndex(*idxAttr)

    return mplug


#------------------------------------------------------------------------------
def getConnWithoutUC(mplug, source, destination):
    u"""
    MPlug から unitConversion系ノードをスキップしてコネクションを得る。
    """
    results = list(mplug.connectedTo(source, destination))
    i = len(results)
    while i:
        i -= 1
        mnode = results[i].node()
        if mnode.apiType() in _UnitConvTypes:
            conn = None
            name = results[i].info.split('.')[-1]
            if name == 'output':
                conn = _2_MFnDependencyNode(mnode).findPlug('input', True).connectedTo(True, False)
            elif name == 'input':
                conn = _2_MFnDependencyNode(mnode).findPlug('output', True).connectedTo(False, True)
            if conn:
                n = len(conn)
                if n is 1:
                    results[i] = conn[0]
                else:
                    results[i:] = list(conn) + results[i + 1:]
    return results


def getMPlugName(mplug):
    u"""
    MPlug からノード名を含むユニーク名を得る。
    """
    # DAGノードでなければ簡単に得られる。
    mobj = mplug.node()
    if not mobj.hasFn(_MFn_kDagNode):
        return mplug.info

    # まず、ノード名抜きでアトリビュート名を得る。
    attrname = mplug.partialName(includeNonMandatoryIndices=True, includeInstancedIndices=True)
    mfnnode = _2_MFnDagNode(mobj)

    # worldSpace アトリビュートの場合は、そのインデックスにマッチした DAG パスを得る。
    if _2_MFnAttribute(mplug.attribute()).worldSpace:
        root = _mplugRoot(mplug)
        if root.isElement:
            idx = root.logicalIndex()
            if idx > 0:
                # API2 だとクラッシュする場合がある(Maya2012_SAP_SP1 win で確認)ので API1 を使う。
                arr1 = _1_MDagPathArray()
                _1_MDagPath_getAllPathsTo(_1_mnode(mfnnode.partialPathName()), arr1)
                return arr1[idx].partialPathName() + '.' + attrname

    # worldSpace でないか、１個めのインスタンスで良い場合はその DAG パスを得る。
    return mfnnode.partialPathName() + '.' + attrname


def _mplugRoot(mplug):
    u"""
    MPlug のルートを得る（最上位がマルチエレメントならエレメントのまま）。
    """
    c = mplug.array() if mplug.isElement else mplug
    while c.isChild:
        mplug = c.parent()
        c = mplug.array() if mplug.isElement else mplug
    return mplug


#------------------------------------------------------------------------------
def _1_mnode(name):
    u"""
    ノード名から API1 MObject を得る。
    """
    sel = _1_MSelectionList()
    sel.add(name)
    mobj = _1_MObject()
    sel.getDependNode(0, mobj)
    return mobj


def _1_mpath(name):
    u"""
    ノード名から API1 MObject を得る。
    """
    sel = _1_MSelectionList()
    sel.add(name)
    mpath = _1_MDagPath()
    sel.getDagPath(0, mpath, _1_MObject_kNullObj)
    return mpath


u'''
def _mplugToAPI1(mplug):
    u"""
    API2 の MPlug から API1 の MPlug を得る。
    """
    names = mplug.info.split('.')
    mfnnode = _1_MFnDependencyNode(_1_mnode(names[0]))

    # ノードからプラグを得る為に、マルチプラグのインデックスを収集する。
    attrTkns = [s.split('[') for s in names[1:]]
    ss = attrTkns.pop(-1)
    leafName = ss[0]
    leafIdx = int(ss[1][:-1]) if len(ss) > 1 else None
    ancestorIdxs = [(ss[0], int(ss[1][:-1])) for ss in attrTkns if len(ss) > 1]

    # ノードからプラグを取得。
    try:
        # 末尾のプラグを得る。
        mplug = mfnnode.findPlug(leafName, False)

        # 上位のロジカルインデックスを選択する。
        for name, idx in ancestorIdxs:
            mplug.selectAncestorLogicalIndex(idx, mfnnode.attribute(name))

        # 末尾のロジカルインデックスを選択する。
        if leafIdx is not None:
            mplug.selectAncestorLogicalIndex(leafIdx)
        return mplug
    except RuntimeError:
        pass
'''


#------------------------------------------------------------------------------
def makePlugTypeInfo(mattr, typename=None):
    u"""
    `.Plug` のタイプ情報をセットする。
    """
    ft = mattr.apiType()
    cls = _APITYPE_MFNATTR_DICT_get(ft, _2_MFnAttribute)
    mfn = cls(mattr)
    attrs = {
        'mfn': mfn,
        'isAlive': _2_MObjectHandle(mattr).isAlive if (mfn.dynamic or mfn.extension) else None,
        'shortname': mfn.shortName,
    }

    if typename:
        attrs['typename'] = typename
    else:
        # 判別できないと '' になるが、ほぼ有り得ないはず。
        p = _GET_MFNATTR_TYPE_DICT_get(cls)
        attrs['typename'] = p(mfn) if p else _mobjAttrType(ft, mfn)

    return attrs


def fixUnitTypeInfo(typeinfo):
    u"""
    サブタイプ（数値コンパウンド下のタイプ）を含む情報をフィックスする。

    `.Plug` の checkValid は済んでいること。
    """
    if 'unittype' not in typeinfo:
        m = _RE_NUMERIC_COMPOUND_match(typeinfo['typename'])
        if m:
            subtype = _APITYPE_ATTRTYPE_DICT_get(typeinfo['mfn'].child(0).apiType())
            if subtype:
                typeinfo['subtype'] = subtype
                typeinfo['unittype'] = typeinfo['typename'] + subtype
            else:
                typeinfo['subtype'] = m.group(1)
                typeinfo['unittype'] = typeinfo['typename']
        else:
            typeinfo['unittype'] = typeinfo['typename']


#def numChildrenOfNumericCompound(typename):
#    m = _RE_NUMERIC_COMPOUND_match(typename)
#    return int(m.group(2)) if m else 0

_RE_NUMERIC_COMPOUND_match = re.compile(r'(short|long|float|double)(\d)$').match


_APITYPE_MFNATTR_DICT = {
    _MFn.kNumericAttribute: _api2.MFnNumericAttribute,
    _MFn.kTypedAttribute: _api2.MFnTypedAttribute,
    _MFn.kEnumAttribute: _api2.MFnEnumAttribute,
    _MFn.kCompoundAttribute: _api2.MFnCompoundAttribute,
    _MFn.kGenericAttribute: _api2.MFnGenericAttribute,
    _MFn.kMessageAttribute: _api2.MFnMessageAttribute,

    _MFn.kDoubleAngleAttribute: _api2.MFnUnitAttribute,
    _MFn.kDoubleLinearAttribute: _api2.MFnUnitAttribute,
    _MFn.kFloatAngleAttribute: _api2.MFnUnitAttribute,
    _MFn.kFloatLinearAttribute: _api2.MFnUnitAttribute,
    _MFn.kTimeAttribute: _api2.MFnUnitAttribute,

    _MFn.kAttribute2Short: _api2.MFnNumericAttribute,
    _MFn.kAttribute3Short: _api2.MFnNumericAttribute,
    _MFn.kAttribute2Int: _api2.MFnNumericAttribute,
    _MFn.kAttribute3Int: _api2.MFnNumericAttribute,
    _MFn.kAttribute2Float: _api2.MFnNumericAttribute,
    _MFn.kAttribute3Float: _api2.MFnNumericAttribute,
    _MFn.kAttribute2Double: _api2.MFnNumericAttribute,
    _MFn.kAttribute3Double: _api2.MFnNumericAttribute,
    _MFn.kAttribute4Double: _api2.MFnNumericAttribute,

    _MFn.kMatrixAttribute: _api2.MFnMatrixAttribute,
    _MFn.kFloatMatrixAttribute: _api2.MFnMatrixAttribute,

    #_MFn.???: _api2.MFnLightDataAttribute,
}  #: アトリビュート MObject のタイプから MFnAttribute 派生クラスを得る辞書。
_APITYPE_MFNATTR_DICT_get = _APITYPE_MFNATTR_DICT.get


def _mobjAttrType(apitype, mfn):
    u"""
    :mayaapi2:`MObject` のAPIタイプからアトリビュートタイプ名を得る。
    """
    res = _APITYPE_ATTRTYPE_DICT_get(apitype)
    if res:
        return res
    m = _RE_ADDATTR_ATDT_search(mfn.getAddAttrCmd(False))
    return ':'.join(m.groups()) if m else ''

_APITYPE_ATTRTYPE_DICT = {
    _MFn.kEnumAttribute: 'enum',
    _MFn.kCompoundAttribute: 'compound',
    _MFn.kGenericAttribute: 'generic',
    _MFn.kMessageAttribute: 'message',
    _MFn.kDoubleAngleAttribute: 'doubleAngle',
    _MFn.kDoubleLinearAttribute: 'doubleLinear',
    _MFn.kFloatAngleAttribute: 'floatAngle',
    _MFn.kFloatLinearAttribute: 'floatLinear',
    _MFn.kTimeAttribute: 'time',

    _MFn.kMatrixAttribute: 'at:matrix',
    _MFn.kFloatMatrixAttribute: 'fltMatrix',

    _MFn.kAttribute2Short: 'short2',
    _MFn.kAttribute3Short: 'short3',
    _MFn.kAttribute2Int: 'long2',
    _MFn.kAttribute3Int: 'long3',
    _MFn.kAttribute2Float: 'float2',
    _MFn.kAttribute3Float: 'float3',
    _MFn.kAttribute2Double: 'double2',
    _MFn.kAttribute3Double: 'double3',
    _MFn.kAttribute4Double: 'double4',
}  #: アトリビュート MObject のタイプからアトリビュートタイプ名を得る辞書。
_APITYPE_ATTRTYPE_DICT_get = _APITYPE_ATTRTYPE_DICT.get


def _numericAttrTypeName(mfn):
    u"""
    MFnNumericAttribute からタイプ名を得る。
    """
    res = _NUMERIC_ATTRTYPE_DICT_get(mfn.numericType())
    if res:
        return res
    m = _RE_ADDATTR_AT_search(mfn.getAddAttrCmd(False))
    return m.group(1) if m else ''

_NUMERIC_ATTRTYPE_DICT = {
    _2_MFnNumericData.kBoolean: 'bool',
    _2_MFnNumericData.kByte: 'byte',
    _2_MFnNumericData.kChar: 'char',
    _2_MFnNumericData.kShort: 'short',
    _2_MFnNumericData.kLong: 'long',
    _2_MFnNumericData.kFloat: 'float',
    _2_MFnNumericData.kDouble: 'double',

    # 以下は MObject.apiType() によって判別がつくもの。
    _2_MFnNumericData.k2Short: 'short2',
    _2_MFnNumericData.k3Short: 'short3',
    _2_MFnNumericData.k2Long: 'long2',
    _2_MFnNumericData.k3Long: 'long3',
    _2_MFnNumericData.k2Float: 'float2',
    _2_MFnNumericData.k3Float: 'float3',
    _2_MFnNumericData.k2Double: 'double2',
    _2_MFnNumericData.k3Double: 'double3',
    _2_MFnNumericData.k4Double: 'double4',
}  #: 数値型アトリビュートのタイプからアトリビュートタイプ名を得る辞書。
_NUMERIC_ATTRTYPE_DICT_get = _NUMERIC_ATTRTYPE_DICT.get

_AT_TYPENAME_SET = frozenset(
    list(_APITYPE_ATTRTYPE_DICT.values()) + list(_NUMERIC_ATTRTYPE_DICT.values())
)  #: -at のアトリビュート型名セット。


def _typedAttrTypeName(mfn):
    u"""
    MFnTypedAttribute からタイプ名を得る。
    """
    res = _DATA_ATTRTYPE_DICT_get(mfn.attrType())
    if res:
        return res
    m = _RE_ADDATTR_DT_search(mfn.getAddAttrCmd(False))
    if m:
        # 通常は -at が使われるタイプの -dt 版の場合は、判別用の接頭辞を付加する。
        res = m.group(1)
        return ('dt:' + res) if res in _AT_TYPENAME_SET else res
    return ''

_DATA_ATTRTYPE_DICT = {
    #_api2.MFnData.kInvalid:
    #_api2.MFnData.kNumeric:
    #_api2.MFnData.kPlugin:  # プラグインデータの場合これにならず kInvalid となる（apiType は kPluginData）。
    #_api2.MFnData.kPluginGeometry:
    _api2.MFnData.kString: 'string',
    _api2.MFnData.kMatrix: 'matrix',  # -dt の方。
    _api2.MFnData.kStringArray: 'stringArray',
    _api2.MFnData.kDoubleArray: 'doubleArray',
    _api2.MFnData.kFloatArray: 'floatArray',
    _api2.MFnData.kIntArray: 'Int32Array',
    _api2.MFnData.kPointArray: 'pointArray',
    _api2.MFnData.kVectorArray: 'vectorArray',
    _api2.MFnData.kComponentList: 'componentList',
    _api2.MFnData.kMesh: 'mesh',
    _api2.MFnData.kLattice: 'lattice',
    _api2.MFnData.kNurbsCurve: 'nurbsCurve',
    _api2.MFnData.kNurbsSurface: 'nurbsSurface',
    _api2.MFnData.kSphere: 'sphere',
    #_api2.MFnData.kDynArrayAttrs:
    #_api2.MFnData.kDynSweptGeometry:
    _api2.MFnData.kSubdSurface: 'subd',
    _api2.MFnData.kNObject: 'Nobject',
    _api2.MFnData.kNId: 'Nid',
    #_api2.MFnData.kAny:
}  #: データ型アトリビュートのタイプからアトリビュートタイプ名を得る辞書。
if MAYA_VERSION >= (2016,):
    _DATA_ATTRTYPE_DICT[_api2.MFnData.kMatrixArray] = 'matrixArray'
_DATA_ATTRTYPE_DICT_get = _DATA_ATTRTYPE_DICT.get


_GET_MFNATTR_TYPE_DICT = {
    _2_MFnNumericAttribute: _numericAttrTypeName,
    _2_MFnTypedAttribute: _typedAttrTypeName,
    #_2_MFnUnitAttribute: _unitAttrType,  # double/float の判別が出来ない。
}
_GET_MFNATTR_TYPE_DICT_get = _GET_MFNATTR_TYPE_DICT.get


def _makeUnsupportedType(typename):
    def proc(v):
        raise ValueError('attribute type not supported: ' + typename)


#------------------------------------------------------------------------------
def _mplug_get_generic(mplug):
    u"""
    generic 型 :mayaapi2:`MPlug` から値を得る。

    数値、数値データ、文字列、matrix に対応。

    単位付き型の場合は内部単位となる。

    :param mplug: :mayaapi2:`MPlug`
    :returns: 数値かリスト。
    """
    try:
        mobj = mplug.asMObject()
    except RuntimeError:
        try:
            return mplug.asDouble()
        except:
            return mplug.asString()
    return dataToValue(mobj, mplug)


def mplug_get_nums(mplug):
    return _2_MFnNumericData(mplug.asMObject()).getData()


def mplug_get_xformmatrix(mplug):
    # NOTE: Null のときは asMObject() 自体がコケるので isNull() できない。
    try:
        mobj = mplug.asMObject()
    except:
        return
    dt = _2_MFnMatrixData(mobj)
    if dt.isTransformation():
        return _dataValueByParsing(mobj, 'matrix', mplug, _X_fromSetAttrCmds)
    else:
        return Matrix(dt.matrix())


def mplug_get_matrix(mplug):
    try:
        return _dataTo_matrix(mplug.asMObject())
    except:
        pass


def _mplug_get_stringArray(mplug):
    try:
        return _dataTo_stringArray(mplug.asMObject())
    except:
        pass


def _mplug_get_doubleArray(mplug):
    try:
        return _dataTo_doubleArray(mplug.asMObject())
    except:
        pass


def _mplug_get_floatArray(mplug):
    try:
        #return _dataTo_floatArray(mplug.asMObject())  # NOTE: API2 には MFnFloatArrayData は実装されていない。
        mplug.asMObject()
    except:
        pass
    else:
        return _getAttr(getMPlugName(mplug)) or []


def _mplug_get_Int32Array(mplug):
    try:
        return _dataTo_Int32Array(mplug.asMObject())
    except:
        pass


def _mplug_get_vectorArray(mplug):
    try:
        return _dataTo_vectorArray(mplug.asMObject())
    except:
        pass


def _mplug_get_pointArray(mplug):
    try:
        #return _dataTo_pointArray(mplug.asMObject())  # NOTE: API2のバグのため得られない（2012でも2020でも確認）。
        mplug.asMObject()
    except:
        pass
    else:
        return [_2_MPoint(x) for x in (_getAttr(getMPlugName(mplug)) or EMPTY_TUPLE)]


def _mplug_get_distance(mp):
    return _2_MDistance_rawToUI(mp.asDouble())


def _mplug_get_angle(mp):
    return _2_MAngle_rawToUI(mp.asDouble())


def _mplug_get_time(mp):
    return _2_MTime_rawToUI(mp.asDouble())


def _mplug_get_distances(mp):
    return [_2_MDistance_rawToUI(x) for x in _2_MFnNumericData(mp.asMObject()).getData()]


def _mplug_get_angles(mp):
    return [_2_MAngle_rawToUI(x) for x in _2_MFnNumericData(mp.asMObject()).getData()]


#def _mplug_get_times(mp):
#    return [_2_MTime_rawToUI(x) for x in _2_MFnNumericData(mp.asMObject()).getData()]


_MPLUG_GETVAL_DICT = {
    'bool': lambda p: p.asBool(),
    'char': lambda p: p.asChar(),
    'short': lambda p: p.asShort(),
    'long': lambda p: p.asInt(),
    'float': lambda p: p.asFloat(),
    'double': lambda p: p.asDouble(),
}
_MPLUG_GETVAL_DICT.update({
    'byte': _MPLUG_GETVAL_DICT['char'],
    'enum': _MPLUG_GETVAL_DICT['short'],

    'floatLinear': _MPLUG_GETVAL_DICT['float'],
    'floatAngle': _MPLUG_GETVAL_DICT['float'],
    'doubleLinear': _MPLUG_GETVAL_DICT['double'],
    'doubleAngle': _MPLUG_GETVAL_DICT['double'],
    'time': _MPLUG_GETVAL_DICT['double'],

    'string': lambda p: p.asString(),

    'matrix': mplug_get_xformmatrix,
    'at:matrix': mplug_get_matrix,
    'fltMatrix': mplug_get_matrix,

    'generic': _mplug_get_generic,

    'stringArray': _mplug_get_stringArray,
    'doubleArray': _mplug_get_doubleArray,
    'floatArray': _mplug_get_floatArray,
    'Int32Array': _mplug_get_Int32Array,
    'vectorArray': _mplug_get_vectorArray,
    'pointArray': _mplug_get_pointArray,

    'short2': mplug_get_nums,
    'short3': mplug_get_nums,
    'long2': mplug_get_nums,
    'long3': mplug_get_nums,
    'float2': mplug_get_nums,
    'float3': mplug_get_nums,
    'double2': mplug_get_nums,
    'double3': mplug_get_nums,
    'double4': mplug_get_nums,
})

_MPLUG_GETUVAL_DICT = dict(_MPLUG_GETVAL_DICT)
_MPLUG_GETUVAL_DICT.update({
    'doubleLinear': _mplug_get_distance,
    'floatLinear': _mplug_get_distance,
    'doubleAngle': _mplug_get_angle,
    'floatAngle': _mplug_get_angle,
    'time': _mplug_get_time,

    'float2floatLinear': _mplug_get_distances,
    'float3floatLinear': _mplug_get_distances,
    'double2doubleLinear': _mplug_get_distances,
    'double3doubleLinear': _mplug_get_distances,
    'double4doubleLinear': _mplug_get_distances,

    'float2floatAngle': _mplug_get_angles,
    'float3floatAngle': _mplug_get_angles,
    'double2doubleAngle': _mplug_get_angles,
    'double3doubleAngle': _mplug_get_angles,
    'double4doubleAngle': _mplug_get_angles,

    #'double2time': _mplug_get_times,
    #'double3time': _mplug_get_times,
    #'double4time': _mplug_get_times,
})


def _makePlugValueGetter(tbl_get):
    def getter(mplug, ttype):
        proc = tbl_get(ttype)

        if mplug.isArray:
            elem = mplug.elementByPhysicalIndex
            if not proc:
                def proc(mp):
                    try:
                        mobj = mplug.asMObject()
                    except:
                        return
                    return _dataValueByParsing(mobj, typ, mp)
                typ = ttype.split(':')[-1]
            return [proc(elem(i)) for i in range(mplug.numElements())]

        if proc:
            return proc(mplug)
        try:
            mobj = mplug.asMObject()
        except:
            return
        return _dataValueByParsing(mobj, ttype.split(':')[-1], mplug)

    return getter

mplugGetRawValue = _makePlugValueGetter(_MPLUG_GETVAL_DICT.get)
mplugGetUnitValue = _makePlugValueGetter(_MPLUG_GETUVAL_DICT.get)


#------------------------------------------------------------------------------
def dataToValue(mobj, mplug=None):
    u"""
    データ MObject から値を得る。
    """
    dtype = mobj.apiType()
    proc = _DATATOVAL_DICT_get(dtype)
    if proc:
        return proc(mobj)
    if dtype != _MFn_kInvalid:  # if not mobj.isNull()
        typ = _DATA_APITYPE_TYPE_DICT_get(dtype)
        if typ:
            try:
                return _dataValueByParsing(mobj, typ, mplug)
            except:
                pass
        raise ValueError('data type not supported: ' + mobj.apiTypeStr)


def _dataTo_xformmatrix(mobj):
    dt = _2_MFnMatrixData(mobj)
    if dt.isTransformation():
        return _dataValueByParsing(mobj, 'matrix', None, _X_fromSetAttrCmds)
    else:
        return Matrix(dt.matrix())


def _dataTo_matrix(mobj):
    return Matrix(_2_MFnMatrixData(mobj).matrix())


def _dataTo_string(mobj):
    return _2_MFnStringData(mobj).string()


def _dataTo_stringArray(mobj):
    return _2_MFnStringArrayData(mobj).array()


def _dataTo_doubleArray(mobj):
    return list(_2_MFnDoubleArrayData(mobj).array())


def _dataTo_Int32Array(mobj):
    return list(_2_MFnIntArrayData(mobj).array())


def _dataTo_vectorArray(mobj):
    return _2_MFnVectorArrayData(mobj).array()


# NOTE: API2 には MFnFloatArrayData は実装されていない。
#def _dataTo_floatArray(mobj):
#    return list(_2_MFnFloatArrayData(mobj).array())


# NOTE: API2のバグのため得られない（2012でも2020でも確認）。
#def _dataTo_pointArray(mobj):
#    return _2_MFnPointArrayData(mobj).array()


# NOTE: 2016以降サポートだが、API2のバグのため得られない。
#def _dataTo_matrixArray(mobj):
#    return _2_MFnMatrixArrayData(mobj).array()


def _dataTo_nums(mobj):
    return _2_MFnNumericData(mobj).getData()


_DATATOVAL_DICT = {  #kData:
    _MFn.kStringData: _dataTo_string,

    _MFn.kMatrixData: _dataTo_xformmatrix,
    _MFn.kMatrixFloatData: _dataTo_matrix,

    _MFn.kStringArrayData: _dataTo_stringArray,
    _MFn.kDoubleArrayData: _dataTo_doubleArray,
    _MFn.kIntArrayData: _dataTo_Int32Array,
    _MFn.kVectorArrayData: _dataTo_vectorArray,

    #_MFn.kFloatArrayData: _dataTo_floatArray,  # NOTE: API2 には MFnFloatArrayData は実装されていない。
    #_MFn.kFloatVectorArrayData:
    #_MFn.kPointArrayData: _dataTo_pointArray,  # NOTE: API2のバグのため得られない（2012でも2020でも確認）。
    #_MFn.kInt64ArrayData: (2016.5以降)
    #_MFn.kUInt64ArrayData: (MFnUInt64ArrayData)
    #_MFn.kMatrixArrayData: _dataTo_matrixArray,  # NOTE: 2016以降サポートだが、API2のバグのため得られない。

    #_MFn.kComponentListData: (MFnComponentListData)

#kNumericData: (MFnNumericData)
    _MFn.kData2Short: _dataTo_nums,
    _MFn.kData3Short: _dataTo_nums,
    _MFn.kData2Int: _dataTo_nums,
    _MFn.kData3Int: _dataTo_nums,
    _MFn.kData2Float: _dataTo_nums,
    _MFn.kData3Float: _dataTo_nums,
    _MFn.kData2Double: _dataTo_nums,
    _MFn.kData3Double: _dataTo_nums,
    _MFn.kData4Double: _dataTo_nums,

#kGeometryData (MFnGeometryData)
    #_MFn.kBezierCurveData:
    #_MFn.kFluidData:
    #_MFn.kLatticeData: (MFnLAtticeData)
    #_MFn.kMeshData: (MFnMeshData)
    #_MFn.kNurbsCurveData: (MFnNurbsCurveData)
    #_MFn.kNurbsSurfaceData: (MFnNurbsSurfaceData)
    #_MFn.kSubdivData: (MFnSubdData)

    #_MFn.kDynArrayAttrsData:
    #_MFn.kDynSweptGeometryData: (MFnDynSweptGeometryData)  # NOTE: API1 にも API2 にも未実装。

    #_MFn.kSphereData: (MFnSphereData)  # NOTE: API2 には未実装。
    #_MFn.kNObjectData: (MFnNObjectData)  # NOTE: API1 にも API2 にも未実装。
    #_MFn.kNIdData: (MFnNIdData)  # NOTE: API1 にも API2 にも未実装。

#kPluginData (MFnPluginData)
#kPluginGeometryData
}
_DATATOVAL_DICT_get = _DATATOVAL_DICT.get

_DATA_APITYPE_TYPE_DICT = {
    _MFn.kStringData: 'string',

    _MFn.kMatrixData: 'matrix',
    _MFn.kMatrixFloatData: 'fltMatrix',

    _MFn.kStringArrayData: 'stringArray',
    _MFn.kDoubleArrayData: 'doubleArray',
    _MFn.kFloatArrayData: 'floatArray',
    _MFn.kIntArrayData: 'Int32Array',
    _MFn.kVectorArrayData: 'vectorArray',
    _MFn.kFloatVectorArrayData: 'floatVectorArray',
    _MFn.kPointArrayData: 'pointArray',

    _MFn.kComponentListData: 'componentList',

#kNumericData: (MFnNumericData)
    _MFn.kData2Short: 'short2',
    _MFn.kData3Short: 'short3',
    _MFn.kData2Int: 'long2',
    _MFn.kData3Int: 'long3',
    _MFn.kData2Float: 'float2',
    _MFn.kData3Float: 'float3',
    _MFn.kData2Double: 'double2',
    _MFn.kData3Double: 'double3',
    _MFn.kData4Double: 'double4',

#kGeometryData (MFnGeometryData)
    #_MFn.kBezierCurveData:
    _MFn.kFluidData: 'fluid',
    _MFn.kLatticeData: 'lattice',
    _MFn.kMeshData: 'mesh',
    _MFn.kNurbsCurveData: 'nurbsCurve',
    _MFn.kNurbsSurfaceData: 'nurbsSurface',
    _MFn.kSubdivData: 'subd',

    #_MFn.kDynArrayAttrsData:
    #_MFn.kDynSweptGeometryData:

    _MFn.kNObjectData: 'Nobject',
    _MFn.kNIdData: 'Nid'

#kPluginData (MFnPluginData)
#kPluginGeometryData
}
if MAYA_VERSION >= (2016, 5):
    _DATA_APITYPE_TYPE_DICT[_MFn.kInt64ArrayData] = 'Int64Array'
    #_MFn.kUInt64ArrayData:
elif MAYA_VERSION >= (2016,):
    _DATA_APITYPE_TYPE_DICT[_MFn.kMatrixArrayData] = 'matrixArray'
_DATA_APITYPE_TYPE_DICT_get = _DATA_APITYPE_TYPE_DICT.get


#------------------------------------------------------------------------------
def _obj_value(v):
    return v.value


def _obj_values(v):
    return [(x and x.value) for x in v]


def _distances_rawToUI(v):
    return [_2_MDistance_rawToUI(x) for x in v]


def _angles_rawToUI(v):
    return [_2_MAngle_rawToUI(x) for x in v]


#def _times_rawToUI(v):
#    return [_2_MTime_rawToUI(x) for x in v]


def _distances_asUI(v):
    return [(x and _2_MDistance_asUI(x)) for x in v]


def _angles_asUI(v):
    return [(x and _2_MAngle_asUI(x)) for x in v]


#def _times_asUI(v):
#    return [(x and _2_MTime_asUI(x)) for x in v]


def _bug_2_MTime_asUI(v):
    return _2_MTime_rawToUI(v.value)


_ATTR_TO_VAL_DICT = {
    'bool': _through,
    'char': _through,
    'short': _through,
    'long': _through,
    'float': _through,
    'double': _through,
    'byte': _through,
    'enum': _through,

    'floatLinear': _obj_value,
    'floatAngle': _obj_value,
    'doubleLinear': _obj_value,
    'doubleAngle': _obj_value,
    'time': _2_MTime_asRaw,  # NOTE: bugの場合は _obj_value

    'string': lambda x: (None if x.isNull() else _dataTo_string(x)),

    'matrix': lambda x: (None if x.isNull() else _dataTo_xformmatrix(x)),
    'at:matrix': Matrix,  #lambda x: (None if x.isNull() else _dataTo_matrix(x)),
    'fltMatrix': Matrix,  #lambda x: (None if x.isNull() else _dataTo_matrix(x)),

    'short2': list,
    'short3': list,
    'long2': list,
    'long3': list,
    'float2': list,
    'float3': list,
    'double2': list,
    'double3': list,
    'double4': list,

    'generic': donothing,  # everytime None

    'stringArray': lambda x: (None if x.isNull() else _dataTo_stringArray(x)),
    'doubleArray': lambda x: (None if x.isNull() else _dataTo_doubleArray(x)),
    #'floatArray': lambda x: (None if x.isNull() else _dataTo_floatArray(x)),  # NOTE: API2 には MFnFloatArrayData は実装されていない。
    'Int32Array': lambda x: (None if x.isNull() else _dataTo_Int32Array(x)),
    'vectorArray': lambda x: (None if x.isNull() else _dataTo_vectorArray(x)),
    #'pointArray': lambda x: (None if x.isNull() else _dataTo_pointArray(x)),  # NOTE: API2のバグのため得られない（2012でも2020でも確認）。
    #'matrixArray': lambda x: (None if x.isNull() else _dataTo_matrixArray(x)),  # NOTE: 2015以降サポートだが、API2のバグのため得られない。
}

_UATTR_TO_VAL_DICT = dict(_ATTR_TO_VAL_DICT)
_UATTR_TO_VAL_DICT.update({
    'float2floatLinear': _obj_values,
    'float3floatLinear': _obj_values,
    'double2doubleLinear': _obj_values,
    'double3doubleLinear': _obj_values,
    'double4doubleLinear': _obj_values,

    'float2floatAngle': _obj_values,
    'float3floatAngle': _obj_values,
    'double2doubleAngle': _obj_values,
    'double3doubleAngle': _obj_values,
    'double4doubleAngle': _obj_values,

    #'double2time': _obj_values,
    #'double3time': _obj_values,
    #'double4time': _obj_values,
})

_ATTR_TO_UVAL_DICT = dict(_ATTR_TO_VAL_DICT)
_ATTR_TO_UVAL_DICT.update({
    'doubleLinear': _2_MDistance_asUI,
    'floatLinear': _2_MDistance_asUI,
    'doubleAngle': _2_MAngle_asUI,
    'floatAngle': _2_MAngle_asUI,
    'time': _2_MTime_asUI,  # NOTE: bugの場合は _bug_2_MTime_asUI,

    'float2floatLinear': _distances_rawToUI,
    'float3floatLinear': _distances_rawToUI,
    'double2doubleLinear': _distances_rawToUI,
    'double3doubleLinear': _distances_rawToUI,
    'double4doubleLinear': _distances_rawToUI,

    'float2floatAngle': _angles_rawToUI,
    'float3floatAngle': _angles_rawToUI,
    'double2doubleAngle': _angles_rawToUI,
    'double3doubleAngle': _angles_rawToUI,
    'double4doubleAngle': _angles_rawToUI,

    #'double2time': _times_rawToUI,
    #'double3time': _times_rawToUI,
    #'double4time': _times_rawToUI,
})

_UATTR_TO_UVAL_DICT = dict(_ATTR_TO_UVAL_DICT)
_UATTR_TO_UVAL_DICT.update({
    'float2floatLinear': _distances_asUI,
    'float3floatLinear': _distances_asUI,
    'double2doubleLinear': _distances_asUI,
    'double3doubleLinear': _distances_asUI,
    'double4doubleLinear': _distances_asUI,

    'float2floatAngle': _angles_asUI,
    'float3floatAngle': _angles_asUI,
    'double2doubleAngle': _angles_asUI,
    'double3doubleAngle': _angles_asUI,
    'double4doubleAngle': _angles_asUI,

    #'double2time': _times_asUI,
    #'double3time': _times_asUI,
    #'double4time': _times_asUI,
})


def _makeAttrToValueFilter(tbl_get):
    def filter(val, ttype, hasMTimeBug=False):
        if ttype == 'time':
            return (mtimeProc1 if hasMTimeBug else mtimeProc0)(val)
        proc = tbl_get(ttype)
        if proc:
            return proc(val)
        return _dataValueByParsing(val, ttype.split(':')[-1])

    # NOTE: MFnUnitAttribute の MTime の特定の値のバグ対策。
    #   time の MFnUnitAttribute の getMin(), getMax(), getSoftMin(), getSoftMax() の MTime 参照は、
    #   本来は単位に準ずる値である value に内部単位(kSeconds)の値がセットされた値になるというバグがある。
    #   （MDistance や MAngle の value は内部単位なので MTime だけ特別）
    #   しかし default の MTime 参照は正常な MTime であるため、バグに対応した処理をするかどうかを
    #   hasMTimeBug フラグによって切り分けている。
    mtimeProc0 = tbl_get('time')
    if mtimeProc0 is _2_MTime_asRaw:
        mtimeProc1 = _obj_value
    elif mtimeProc0 is _2_MTime_asUI:
        mtimeProc1 = _bug_2_MTime_asUI

    return filter

attrToRawValue = _makeAttrToValueFilter(_ATTR_TO_VAL_DICT.get)
unitAttrToRawValue = _makeAttrToValueFilter(_UATTR_TO_VAL_DICT.get)
attrToUnitValue = _makeAttrToValueFilter(_ATTR_TO_UVAL_DICT.get)
unitAttrToUnitValue = _makeAttrToValueFilter(_UATTR_TO_UVAL_DICT.get)


#------------------------------------------------------------------------------
def _dataFrom_xformmatrix(val):
    if isinstance(val, Transformation):
        tmpmp = _getCommonTempMPlug('matrix')
        lines = val.getSetAttrCmds()
        lines[0] = (lines[0] % tmpmp.info) 
        _api1_executeCommand(' '.join(lines))
        return tmpmp.asMObject()
    else:
        return _2_MFnMatrixData().create(val._Matrix__data if val else _2_MMatrix())


#def _dataFrom_matrix(val):
#    return _2_MFnMatrixData().create(val._Matrix__data if val else _2_MMatrix())
def _valueFrom_matrix(val):
    return val._Matrix__data if val else _2_MMatrix()


def _dataFrom_string(val):
    return _2_MFnStringData().create(val or '')


def _dataFrom_stringArray(val):
    return _2_MFnStringArrayData().create(val or [])


def _dataFrom_doubleArray(val):
    return _2_MFnDoubleArrayData().create(val or [])


# NOTE: API2 には MFnFloatArrayData は実装されていない。
#def _dataFrom_floatArray(val):
#    return _2_MFnFloatArrayData().create(val or [])


def _dataFrom_Int32Array(val):
    return _2_MFnIntArrayData().create(val or [])


def _dataFrom_vectorArray(val):
    return _2_MFnVectorArrayData().create(val or [])


def _dataFrom_pointArray(val):
    return _2_MFnPointArrayData().create(val or [])


def _dataFrom_matrixArray(val):
    return _2_MFnMatrixArrayData().create(val or [])


_VAL_TO_ATTR_DICT = {
    'generic': _makeUnsupportedType('generic'),

    'bool': _through,
    'char': _through,
    'short': _through,
    'long': _through,
    'float': _through,
    'double': _through,
    'byte': _through,
    'enum': _through,

    'floatLinear': _2_MDistance,
    'floatAngle': _2_MAngle,
    'doubleLinear': _2_MDistance,
    'doubleAngle': _2_MAngle,
    'time': _2_MTime_fromRaw,

    'string': _dataFrom_string,

    'matrix': _dataFrom_xformmatrix,
    'at:matrix': _valueFrom_matrix,
    'fltMatrix': _valueFrom_matrix,

    'stringArray': _dataFrom_stringArray,
    'doubleArray': _dataFrom_doubleArray,
    'Int32Array': _dataFrom_Int32Array,
    'vectorArray': _dataFrom_vectorArray,

    #'floatArray': _dataFrom_floatArray,  # NOTE: API2 には MFnFloatArrayData は実装されていない。
    #'floatVectorArray':
    'pointArray': _dataFrom_pointArray,
    #'Int64Array':
    #_MFn.kUInt64ArrayData: (MFnUInt64ArrayData)
    'matrixArray': _dataFrom_matrixArray,
}

_UVAL_TO_ATTR_DICT = dict(_VAL_TO_ATTR_DICT)
_UVAL_TO_ATTR_DICT.update({
    'floatLinear': _2_MDistance_fromUI,
    'floatAngle': _2_MAngle_fromUI,
    'doubleLinear': _2_MDistance_fromUI,
    'doubleAngle': _2_MAngle_fromUI,
    'time': _2_MTime_fromUI,
})


def _toMelLiteral(val):
    if isinstance(val, BASESTR):
        return '"' + val + '"'
    elif isinstance(val, bool):
        return 'yes' if val else 'no'
    elif isinstance(val, Number):
        return str(val)
    return ' '.join([str(x) for x in val])


def _makeAttrFromValueFilter(tbl_get):
    def filter(val, ttype):
        proc = tbl_get(ttype)
        if proc:
            return proc(val)

        typ = ttype.split(':')[-1]
        strvals = [_toMelLiteral(x) for x in val]
        tmpmp = _getCommonTempMPlug(typ)
        code = ['setAttr "%s" -type "%s"' % (tmpmp.info, typ)]
        if typ.endswith('Array'):
            code.append(str(len(val)))
        code = ' '.join(code + strvals)
        #print(code)
        try:
            _api1_executeCommand(code)
            return tmpmp.asMObject()
        except:
            raise ValueError('attribute type not supported: ' + ttype)

    return filter

attrFromRawValue = _makeAttrFromValueFilter(_VAL_TO_ATTR_DICT.get)
attrFromUnitValue = _makeAttrFromValueFilter(_UVAL_TO_ATTR_DICT.get)


#------------------------------------------------------------------------------
def mplugCurrentValueSetter(mplug, typename):
    u"""
    現在の値にセットするための関数を得る。
    """
    return _MPLUG_GET_CURVAL_SETTER_DICT_get(typename, _getCurValSetter_mobject)(mplug)


def _getCurValSetter_mobject(mplug):
    try:
        v = mplug.asMObject()
    except:
        v = _2_MObject_kNullObj
    return lambda: mplug.setMObject(v)


def _getCurValSetter_generic(mplug):
    try:
        v = mplug.asMObject()
    except:
        try:
            v = mplug.asDouble()
            return lambda: mplug.setDouble(v)
        except:
            v = _2_MObject_kNullObj
    return lambda: mplug.setMObject(v)


def _getCurValSetter_bool(mplug):
    v = mplug.asBool()
    return lambda: mplug.setBool(v)


def _getCurValSetter_char(mplug):
    v = mplug.asChar()
    return lambda: mplug.setChar(v)


def _getCurValSetter_short(mplug):
    v = mplug.asShort()
    return lambda: mplug.setShort(v)


def _getCurValSetter_long(mplug):
    v = mplug.asInt()
    return lambda: mplug.setInt(v)


def _getCurValSetter_float(mplug):
    v = mplug.asFloat()
    return lambda: mplug.setFloat(v)


def _getCurValSetter_double(mplug):
    v = mplug.asDouble()
    return lambda: mplug.setDouble(v)


_MPLUG_GET_CURVAL_SETTER_DICT = {
    'bool': _getCurValSetter_bool,
    'char': _getCurValSetter_char,
    'byte': _getCurValSetter_char,
    'short': _getCurValSetter_short,
    'enum': _getCurValSetter_short,
    'long': _getCurValSetter_long,
    'float': _getCurValSetter_float,
    'double': _getCurValSetter_double,

    'floatLinear': _getCurValSetter_double,
    'floatAngle': _getCurValSetter_double,
    'doubleLinear': _getCurValSetter_double,
    'doubleAngle': _getCurValSetter_double,
    'time': _getCurValSetter_double,
}
_MPLUG_GET_CURVAL_SETTER_DICT_get = _MPLUG_GET_CURVAL_SETTER_DICT.get


#------------------------------------------------------------------------------
def mplugApiValueSetter(typename):
    u"""
    API値（defaultなど）を現在の値にセットする関数を得る。

    - 単位付き型は MDistance, MAngle, MTime を使用。
    - 単位無しの数値型は、通常の数値。
    - 数値コンパウンドは、内部単位での数値シーケンス。
    - それら以外の場合は MObject 。
    """
    return _MPLUG_SETAPIVAL_DICT_get(typename, _setApiVal_mobject)


def _setApiVal_mobject(mplug, v):
    mplug.setMObject(v)


def _setApiVal_mmatrix(mplug, v):
    mplug.setMObject(_2_MFnMatrixData().create(v))


def _setApiVal_bool(mplug, v):
    mplug.setBool(v)


def _setApiVal_char(mplug, v):
    mplug.setChar(v)


def _setApiVal_short(mplug, v):
    mplug.setShort(v)


def _setApiVal_long(mplug, v):
    mplug.setInt(v)


def _setApiVal_float(mplug, v):
    mplug.setFloat(v)


def _setApiVal_double(mplug, v):
    mplug.setDouble(v)


def _setApiVal_angle(mplug, v):
    mplug.setMAngle(v)


def _setApiVal_distance(mplug, v):
    mplug.setMDistance(v)


def _setApiVal_time(mplug, v):
    mplug.setMTime(v)


def _makeNumDataSetter(numType):
    def setter(mplug, val):
        fndata = _2_MFnNumericData()
        mobj = fndata.create(numType)
        fndata.setData(val)
        mplug.setMObject(mobj)
    return setter


_MPLUG_SETAPIVAL_DICT = {
    'at:matrix': _setApiVal_mmatrix,
    'fltMatrix': _setApiVal_mmatrix,

    'bool': _setApiVal_bool,
    'char': _setApiVal_char,
    'byte': _setApiVal_char,
    'short': _setApiVal_short,
    'enum': _setApiVal_short,
    'long': _setApiVal_long,
    'float': _setApiVal_float,
    'double': _setApiVal_double,

    'floatLinear': _setApiVal_distance,
    'floatAngle': _setApiVal_angle,
    'doubleLinear': _setApiVal_distance,
    'doubleAngle': _setApiVal_angle,
    'time': _setApiVal_time,

    'short2': _makeNumDataSetter(_2_MFnNumericData.k2Short),
    'short3': _makeNumDataSetter(_2_MFnNumericData.k3Short),
    'long2': _makeNumDataSetter(_2_MFnNumericData.k2Int),
    'long3': _makeNumDataSetter(_2_MFnNumericData.k3Int),
    'float2': _makeNumDataSetter(_2_MFnNumericData.k2Float),
    'float3': _makeNumDataSetter(_2_MFnNumericData.k3Float),
    'double2': _makeNumDataSetter(_2_MFnNumericData.k2Double),
    'double3': _makeNumDataSetter(_2_MFnNumericData.k3Double),
    'double4': _makeNumDataSetter(_2_MFnNumericData.k4Double),
}
_MPLUG_SETAPIVAL_DICT_get = _MPLUG_SETAPIVAL_DICT.get


#------------------------------------------------------------------------------
def _parseSetAttrCmds(lines):
    u"""
    setAttr コマンドをパースして、セット可能な値として返す。
    """
    m = _RE_SETATTR_CMD_VAL_match(lines[0])
    if not m:
        raise RuntimeError('cannnot parse command')
    tkns = _RE_SETATTR_VAL_TOKENS_findall(m.group(1))
    if len(lines) > 1:
        for line in lines[1:-1]:
            tkns.extend(_RE_SETATTR_VAL_TOKENS_findall(line))
        line = lines[-1][:-1]  # 末尾の ; を取り除く。
        tkns.extend(_RE_SETATTR_VAL_TOKENS_findall(line))
    return eval('[' + ','.join([_YESNO_TO_BOOLSTR(x, x) for x in tkns]) + ']')

_RE_SETATTR_CMD_VAL_match = re.compile(r'.*setAttr .+ -type "[^"]+" (.*?);?$').match  #: setAttr のコマンド開始行にマッチ。
#_RE_SETATTR_VAL_match = re.compile(r'(.*?);?$').match  #: setAttr の後続行にマッチ。
_RE_SETATTR_VAL_TOKENS_findall = re.compile(r'((?<!\\)".*(?<!\\)"|\S+)').findall  #: setAttr 値のトークン分割。
_YESNO_TO_BOOLSTR = {'yes': 'True', 'no': 'False'}.get


def _dataValueByParsing(mobj, datatype, mplug=None, parser=None):
    u"""
    setAttr コマンドをパースすることで値を得る。
    """
    # MPlug が渡されたのなら、そこから setAttr 文字列を得る。
    # プラグに入力コネクションがあると得られないので、得られるまで上流に遡る。
    if mplug:
        lines = mplug.getSetAttrCmds()
        while not lines:
            mps = mplug.connectedTo(True, False)
            if not mps:
                break
            mplug = toNonNetworkedMPlug(mps[0])
            lines = mplug.getSetAttrCmds()
    else:
        lines = None

    # MPlug が渡されなかったか MPlug からはどうしてもコマンドを得られなかった場合、
    # 共有テンポラリアトリビュートに値をセットしてから得る。
    if not lines:
        tmpmp = _getCommonTempMPlug(datatype)
        tmpmp.setMObject(mobj)
        lines = tmpmp.getSetAttrCmds()

    # パースして値を得る。
    if parser:
        try:
            return parser(lines)
        except:
            raise ValueError('attribute type not supported: ' + datatype)
    else:
        try:
            val = _parseSetAttrCmds(lines)
        except:
            raise ValueError('attribute type not supported: ' + datatype)
        proc = _MPLUG_DECODE_DICT_get(datatype)
        return proc(val) if proc else val


def _decode_matrixArray(dt):
    if dt:
        n = dt[0]
        return [Matrix(dt[i:i + 16]) for i in range(1, 1 + n * 16, 16)]
    else:
        return dt


def _decode_floatVectorArray(dt):
    if dt:
        n = dt[0]
        return [_2_MFloatVector(dt[i:i + 3]) for i in range(1, 1 + n * 3, 3)]
    else:
        return dt


def _decode_pointArray(dt):
    if dt:
        n = dt[0]
        return [_2_MPoint(dt[i:i + 4]) for i in range(1, 1 + n * 4, 4)]
    else:
        return dt


def _decode_simpleArray(dt):
    return dt[1:]


_MPLUG_DECODE_DICT = {
    #'doubleArray': _decode_simpleArray,
    'floatArray': _decode_simpleArray,
    #'Int32Array': _decode_simpleArray,
    'Int64Array': _decode_simpleArray,

    #'stringArray': _decode_simpleArray,
    #'vectorArray': _decode_vectorArray,
    'floatVectorArray': _decode_floatVectorArray,
    'pointArray': _decode_pointArray,

    'matrixArray': _decode_matrixArray,

    #'fltMatrix': _decode_floatMatrix,  # data でも kMatrixData になるので不要ぽい。
}
_MPLUG_DECODE_DICT_get = _MPLUG_DECODE_DICT.get


def _getCommonTempMPlug(datatype):
    global _CyObject
    plug = _commonTempPlugDict_get(datatype)
    if not plug or not plug.isValid():
        if not _CyObject:
            from .cyobject import CyObject as _CyObject
        node = _CyObject('time1')
        name = _COMMON_TEMP_ATTR_PREFIX + datatype
        if not node.hasAttr(name):
            _api1_executeCommand('addAttr -ln "%s" -dt "%s" time1' % (name, datatype))
        plug = node.plug_(name)
        _commonTempPlugDict[datatype] = plug
    return plug.mplug_()
_commonTempPlugDict = {}
_commonTempPlugDict_get = _commonTempPlugDict.get
_COMMON_TEMP_ATTR_PREFIX = 'cymelCommonTemp_'
_CyObject = None

