# -*- coding: utf-8 -*-
u"""
ノードタイプ情報。
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from ..common import *

__all__ = [
    'isDerivedNodeType',
    'getInheritedNodeTypes',
    'isAbstractType',
    'dumpNodetypeTree',
    'getNodetypeTreeDict',
    'iterNodetypeTree',
]

_allNodeTypes = cmds.allNodeTypes
_nodeType = cmds.nodeType


#------------------------------------------------------------------------------
def isDerivedNodeType(nodetype, basetype, node=None):
    u"""
    ノードタイプが別のノードタイプと同じか派生型かどうかを得る。

    キャッシュされているので :mayacmd:`nodeType` コマンドなどで
    調べるより、大幅に高速である。

    :param `str` nodetype: ノードタイプ名。
    :param `str` basetype: チェックするベースタイプ名。
    :param `str` node:
        実際のノードを特定する名前。
        必須ではないが、指定すると新規に情報作成される場合にやや高速。
    :rtype: `bool`
    """
    return basetype in (
        _NODETYPE_INHERIT_SET_DICT.get(nodetype) or
        _addNodeType(nodetype, node, asSet=True)
    )


def getInheritedNodeTypes(nodetype, node=None, asSet=False):
    u"""
    ノードタイプが継承しているタイプ情報を得る。

    キャッシュされているので :mayacmd:`nodeType` コマンドなどで
    調べるより、大幅に高速である。

    指定タイプ名を含む継承タイプ名全てを得られる。
    `tuple` の場合は、昇順に並んでいる。

    :param `str` nodetype: ノードタイプ名。
    :param `str` node:
        実際のノードを特定する名前。
        必須ではないが、指定すると新規に情報作成される場合にやや高速。
    :param `bool` asSet: 結果を `frozenset` で得る。
    :rtype: `tuple` or `frozenset`
    """
    return (
        _NODETYPE_INHERIT_SET_DICT if asSet else _NODETYPE_INHERIT_DICT
    ).get(nodetype) or _addNodeType(nodetype, node, asSet=asSet)


def isAbstractType(nodetype, node=None):
    u"""
    ノードタイプが抽象タイプかどうかを得る。

    キャッシュされているので :mayacmd:`allNodeTypes` コマンドなどで
    調べるより、大幅に高速である。

    戻り値は整数で、
    0 は抽象タイプではなく、
    1 は抽象タイプ、
    2 はメタクラス（プラグインインタフェースなどのために存在するが、
    実際は本当のノードタイプではない）
    の意味となる。

    :param `str` nodetype: ノードタイプ名。
    :param `str` node:
        実際のノードを特定する名前。
        必須ではないが、指定すると新規に情報作成される場合にやや高速。
    :rtype: `int`
    """
    ret = _ABSTRACT_NODETYPE_DICT.get(nodetype)
    if ret is None:
        _updateAbstractTypeInfo(_queryDerived(nodetype, node))
        return _ABSTRACT_NODETYPE_DICT[nodetype]
    return ret


def dumpNodetypeTree(nodetype='node', writer=None, indent=2):
    u"""
    ノードタイプツリーをダンプする。

    :param `str` nodetype: 起点。これ以下をダンプする。
    :param `callable` writer: ライター。
    :param `int` indent: インデント数。
    """
    _buildNodeTypeHierarchyInfo(nodetype)

    def dump(nodetype, indent, belows):
        abstype = _ABSTRACT_NODETYPE_DICT[nodetype]
        if abstype is _ABS_META:
            writer(indent + nodetype + ' (abstract meta)')
        elif abstype:
            writer(indent + nodetype + ' (abstract)')
        else:
            writer(indent + nodetype)

        indent += spc
        children = set([x[0] for x in belows if x[1] == nodetype])
        belows = [x for x in belows if x[1] != nodetype and x[0] not in children]
        for child in sorted(children):
            dump(child, indent, belows)

    if not writer:
        writer = print

    spc = ' ' * indent
    belows = [_NODETYPE_INHERIT_DICT[x] for x, y in _NODETYPE_INHERIT_SET_DICT.items() if nodetype in y]
    belows = [x for x in belows if x[0] != nodetype]
    dump(nodetype, '', belows)


def getNodetypeTreeDict(nodetype='node'):
    u"""
    ノードタイプツリーの辞書を得る。

    キーは「ノードタイプ名」、
    値は「子タイプ名の `set` 」
    となる辞書を得られる。

    :param `str` nodetype: 起点。これ以下の情報を生成する。
    :rtype: `dict`
    """
    _buildNodeTypeHierarchyInfo(nodetype)

    result = {}

    def build(nodetype, belows):
        children = set([x[0] for x in belows if x[1] == nodetype])
        belows = [x for x in belows if x[1] != nodetype and x[0] not in children]
        result[nodetype] = children
        for child in children:
            build(child, belows)

    belows = [_NODETYPE_INHERIT_DICT[x] for x, y in _NODETYPE_INHERIT_SET_DICT.items() if nodetype in y]
    belows = [x for x in belows if x[0] != nodetype]
    build(nodetype, belows)
    return result


def iterNodetypeTree(nodetype='node', breadthFirst=False):
    dic = getNodetypeTreeDict(nodetype)
    return (iterTreeBreadthFirst if breadthFirst else iterTreeDepthFirst)(['node'], dic.get)


#------------------------------------------------------------------------------
if MAYA_VERSION < (2016, 5):
    # allNodeTypes コマンドの返す情報の間違いの修正。
    def _bugFixedAllNodeTypes():
        u"""
        :mayacmd:`allNodeTypes` コマンドによって全ノードタイプ情報を得る。
        バージョンによって `list` か `set` かは不定とする。
        """
        res = set(_allNodeTypes(ia=True))
        res.difference_update(_WRONG_TYPE_DESCS)
        res.update(_FIXED_TYPE_DESCS)
        return res

    _WRONG_TYPE_DESCS = frozenset([
        'adskAssetInstanceNode_TdnTx2D (abstract)',
        'adskAssetInstanceNode_TlightShape (abstract)',
        'adskAssetInstanceNode_TdependNode (abstract)',
    ])
    _FIXED_TYPE_DESCS = frozenset([('T' + x) for x in _WRONG_TYPE_DESCS])

    def _metaTypesForBug():
        u"""
        :mayanode:`node` タイプ情報をクエリできないMayaバージョンのために、メタタイプのリストを得る。
        """
        global _META_TYPES_FOR_BUG
        if _META_TYPES_FOR_BUG is None:
            def test(x):
                try:
                    _nodeType(x, itn=True, i=True)
                except:
                    return False
                return True
            _META_TYPES_FOR_BUG = [x for x in (
                'OGSmetaNode',
                'THarrayMapper',
                'THassembly',
                'THblendShape',
                'THcameraSet',
                'THclientDevice',
                'THconstraint',
                'THcustomTransform',
                'THdeformer',
                'THdependNode',
                'THdynEmitter',
                'THdynField',
                'THdynSpring',
                'THfluidEmitter',
                'THgeometryFilter',
                'THhardwareShader',
                'THhwShader',
                'THikSolver',
                'THikSolverNode',
                'THimagePlane',
                'THlocatorShape',
                'THmanip',
                'THmanipContainer',
                'THmotionPath',
                'THobjectSet',
                'THskinCluster',
                'THsurfaceShape',
                'THthreadedDevice',
                'TguideLineShape',
                'Tmanipulator',
                'TmetaNode',
                'Tproxy',
                'TspecialObject',
                'TsummaryObject',
                'TunderWorld',
                'Tworld',
            ) if test(x)]
        return _META_TYPES_FOR_BUG

    _META_TYPES_FOR_BUG = None

else:
    # allNodeTypes コマンドによって全ノードタイプ情報を得る。
    # バージョンによって list か set かは不定とする。
    _bugFixedAllNodeTypes = partial(_allNodeTypes, ia=True)

_FIXED_NODETYPE_INHERIT_INFO = {
    'node': ('node',),

    # 以下は 2016.5 未満で nodeType コマンドでクエリできないノードタイプの情報。
    'nurbsCurve': (
        'nurbsCurve', 'curveShape', 'controlPoint', 'deformableShape', 'geometryShape',
        'shape', 'dagNode', 'entity', 'containerBase', 'node'),
    'time': ('time', 'node'),
    'mesh': (
        'mesh', 'surfaceShape', 'controlPoint', 'deformableShape', 'geometryShape',
        'shape', 'dagNode', 'entity', 'containerBase', 'node'),
    'nurbsSurface': (
        'nurbsSurface', 'surfaceShape', 'controlPoint', 'deformableShape', 'geometryShape',
        'shape', 'dagNode', 'entity', 'containerBase', 'node'),
    'lattice': (
        'lattice', 'controlPoint', 'deformableShape', 'geometryShape',
        'shape', 'dagNode', 'entity', 'containerBase', 'node'),
    'file': ('file', 'texture2d', 'node'),
}


#------------------------------------------------------------------------------
def _addNodeType(nodetype, node=None, asSet=False):
    u"""
    ノードタイプ情報を追加する。

    :param `str` nodetype: ノードタイプ名。
    :param `str` node:
        実際のノードを特定する名前。
        必須ではないが、指定した方がやや高速。
    :param `bool` asSet: 結果をセットで得るかどうか。
    :rtype: `tuple` or `frozenset`
    """
    inherited = _queryInherited(nodetype, node)
    inheritedSet = frozenset(inherited)

    _NODETYPE_INHERIT_DICT[nodetype] = inherited
    _NODETYPE_INHERIT_SET_DICT[nodetype] = inheritedSet

    return inheritedSet if asSet else inherited


def _queryInherited(nodetype, node=None):
    u"""
    継承しているノードタイプをクエリする。

    :param `str` nodetype: ノードタイプ名。
    :param `str` node:
        実際のノードを特定する名前。
        必須ではないが、指定した方がやや高速。
    :rtype: `tuple`
    """
    try:
        if node:
            result = _nodeType(node, i=True)
        else:
            result = _nodeType(nodetype, itn=True, i=True)
    except RuntimeError:
        if nodetype == 'node':
            return ('node',)
        raise ValueError('unknown node type: ' + nodetype)

    # 無事に取得できればメタクラスも含まれる。
    if result:
        result = ucToStrList(result)
        result.reverse()
        result.append('node')
        result = tuple(result)
    # Mayaバージョンによっては何も取得できないものがある。
    else:
        #print('# cannot query node inheritance info: ' + nodetype)
        result = _FIXED_NODETYPE_INHERIT_INFO[nodetype]
    return result


def _queryDerived(nodetype, node=None):
    u"""
    派生しているノードタイプをクエリする。

    :param `str` nodetype: ノードタイプ名。
    :param `str` node:
        実際のノードを特定する名前。
        必須ではないが、指定した方がやや高速。
    :rtype: `set`
    """
    try:
        if node:
            result = _nodeType(node, d=True)
        else:
            result = _nodeType(nodetype, itn=True, d=True)
    except RuntimeError:
        if nodetype == 'node':
            return set([x.split()[0] for x in _bugFixedAllNodeTypes()] + _metaTypesForBug())
        raise ValueError('unknown node type: ' + nodetype)

    # 無事に取得できればメタクラスも含まれる。
    if result:
        result = set(result)
        result.add(nodetype)  # 通常は指定タイプも含まれるが 'node' に限り含まれないため。
        return result
    # Mayaバージョンによっては何も取得できないものがある。
    else:
        #print('# cannot query node derivation info: ' + nodetype)
        _buildNodeTypeHierarchyInfo(abstract=False)
        return set([_NODETYPE_INHERIT_DICT[x][0] for x, y in _NODETYPE_INHERIT_SET_DICT.items() if nodetype in y])


def _updateAbstractTypeInfo(typeSet):
    u"""
    指定ノードタイプについての抽象タイプ情報を更新する。
    """
    typeSet = typeSet.difference(_ABSTRACT_NODETYPE_DICT)
    if typeSet:
        puretypes = _bugFixedAllNodeTypes()  # 'node (abstract)' も含まれるがメタクラスは含まれない。
        abstypes = [x.split()[0] for x in puretypes if x.endswith('(abstract)')]
        unknownMetaSet = typeSet.difference([x.split()[0] for x in puretypes])

        _ABSTRACT_NODETYPE_DICT.update([(x, _ABS_NO) for x in typeSet])
        _ABSTRACT_NODETYPE_DICT.update([(x, _ABS_ABS) for x in abstypes] + [(x, _ABS_META) for x in unknownMetaSet])


def _buildNodeTypeHierarchyInfo(nodetype='node', abstract=True):
    u"""
    指定ノードタイプ以下の階層情報と抽象タイプ情報を更新する。
    """
    typeSet = _queryDerived(nodetype)

    for key in typeSet.difference(_NODETYPE_INHERIT_DICT):
        inherited = _queryInherited(key)
        _NODETYPE_INHERIT_DICT[key] = inherited
        _NODETYPE_INHERIT_SET_DICT[key] = frozenset(inherited)

    if abstract:
        _updateAbstractTypeInfo(typeSet)

_NODETYPE_INHERIT_DICT = {}  #: ノードタイプの上位ノードタイプtupleの辞書。
_NODETYPE_INHERIT_SET_DICT = {}  #: ノードタイプの上位ノードタイプfrozensetの辞書。
_ABSTRACT_NODETYPE_DICT = {}  #: 抽象タイプかどうかの辞書。 (0=No, 1=Abstract, 2=Meta)
_ABS_NO = 0
_ABS_ABS = 1
_ABS_META = 2

# import時にキャッシュを生成。やらなくても良いが、一気にやった方が効率が良いので。
_buildNodeTypeHierarchyInfo()

