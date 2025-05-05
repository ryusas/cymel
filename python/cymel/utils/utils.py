# -*- coding: utf-8 -*-
u"""
Maya用の様々なヘルパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..common import *
from ..compat_nodetype import compat_nodetype_map
import maya.api.OpenMaya as _api2
import maya.OpenMaya as _api1

__all__ = [
    'createNode',

    'correctNodeName',
    'correctNodeNameNS',
    'escapeForMel',
    'makeNiceName',

    'loadPlugin',
    'enablePlugin',

    'affectedAttrNames',
    'affectingAttrNames',

    'listEnum',
]

_createNode = cmds.createNode
_pluginInfo = cmds.pluginInfo
_affects = cmds.affects
_attributeQuery = cmds.attributeQuery
_addAttr = cmds.addAttr

_2_MSelectionList = _api2.MSelectionList
_2_MPlug = _api2.MPlug

_api1_executeCommand = _api1.MGlobal.executeCommand

_cntm_correctName = compat_nodetype_map.correctName
_cntm_futureName = compat_nodetype_map.futureName

_CyObject = None


#------------------------------------------------------------------------------
def createNode(nodetype, **kwargs):
    u"""
    ノードを生成する。

    :mayacmd:`createNode` コマンドの置き換えとして機能する。

    `~.compat_nodetype` による新旧バージョン互換のためのノードタイプ名置換がされつつ、
    `~.CyObject` が返される。
    """
    global _CyObject
    if not _CyObject:
        from ..core import CyObject as _CyObject

    instead = _cntm_futureName(nodetype)
    compat = _cntm_correctName(nodetype)
    if not compat:
        warning('Not compatible node type name between old and new versions: %s (use %s instead)' % (nodetype, instead))
        compat = nodetype

    if 'name' not in kwargs and 'n' not in kwargs:
        kwargs['name'] = instead + '#'
    return _CyObject(_createNode(compat, **kwargs))


#------------------------------------------------------------------------------
def correctNodeName(name):
    u"""
    任意の名前をネームスペースを含まないノード名として問題ない形に修正する。

    :param `str` name: 任意の名前。
    :rtype: `str`
    """
    return _RE_INVALID_CHARACTERS_FOR_NODENAME_sub('_', _RE_HEAD_NUMBER_sub('', name))

_RE_HEAD_NUMBER_sub = re.compile(r'^\d+').sub  #: 先頭の数字。
_RE_INVALID_CHARACTERS_FOR_NODENAME_sub = re.compile(r'\W').sub  #: ノード名に都合の悪い文字。


def correctNodeNameNS(name):
    u"""
    任意の名前をノード名として問題ない形に修正する。ネームスペースを許容。

    :param `str` name: 任意の名前。
    :rtype: `str`
    """
    if name.startswith(':'):
        name = name.rstrip(':') or ':'
    else:
        name = name.rstrip(':')
    return _RE_INVALID_CHARACTERS_FOR_NS_NODENAME_sub(
        '_', _RE_REDUNDANT_NS_SEPARATOR_sub(':', _RE_HEAD_NUMBER_sub('', name))
    )

_RE_INVALID_CHARACTERS_FOR_NS_NODENAME_sub = re.compile(r'[^\w:]').sub  #: ネームスペース付きノード名に都合の悪い文字。
_RE_REDUNDANT_NS_SEPARATOR_sub = re.compile(r':+\d*').sub  #: ネームスペース区切りと続く数字。


def escapeForMel(s):
    u"""
    melの文字列向けのエスケープをする。

    :param `str` s: 文字列。
    :rtype: `str`
    """
    return _RE_ESCAPES_FOR_MEL_sub(r'\\\1', s)

_RE_ESCAPES_FOR_MEL_sub = re.compile(r'(["\\])').sub


def makeNiceName(name):
    u"""
    mixedCase や CamelCase の名前から Maya の Nice Name を得る。

    :param `str` name: 任意の名前。
    :rtype: `str`
    """
    if name:
        return ' '.join([
            (x[0].upper() + x[1:])
            for x in _RE_WORDS_OR_MAYA_NAME_findall(name)
        ])
    return name

_RE_WORDS_OR_MAYA_NAME_findall = re.compile(r'([A-Z]+(?![^A-Z])|[A-Z][a-z]*|\d+|(?<![A-Z])[a-z]+|\|)').findall


#------------------------------------------------------------------------------
def loadPlugin(name):
    u"""
    プラグインがロードされていなければロードする。

    新規にロードされた場合にのみプラグイン名が返される。

    :param `str` name: プラグイン名。
    :rtype: `str` or None
    """
    if not _pluginInfo(name, q=True, loaded=True):
        return str(_loadPlugin(name)[0])

if MAYA_VERSION < (2014,):
    def _loadPlugin(name):
        # 2012 以前では .py を明示してロードすると戻り値が None だった。
        try:
            return _cmds_loadPlugin(name) or ['.'.join(name.split('.')[:-1])]
        except RuntimeError:
            # 2013 以前では .py の明示が必要だった。
            if not name.endswith('.py'):
                return _cmds_loadPlugin(name + '.py') or [name]
            raise
    _cmds_loadPlugin = cmds.loadPlugin
else:
    _loadPlugin = cmds.loadPlugin


def enablePlugin(name, proc=loadPlugin):
    u"""
    プラグインを利用可能にする。

    プラグインが存在しない場合もエラーにはしたくない場合に利用する。

    成功したかどうかの `bool` 値が返される。

    デフォルトでは `loadPlugin` が呼び出されるので、
    プラグインがロードされていなければロードされるが、
    プラグインが存在しない場合はエラーにはならず
    同名プラグインの２度目以降の呼び出し時のリトライは抑制される。

    :param `str` name: プラグイン名。
    :param `callable` proc:
        プラグインのロードするために利用する関数。
        デフォルトでは `loadPlugin` が利用される。
    :rtype: `bool`
    """
    flag = _PLUGIN_ENABLED_DICT.get(name)
    if flag:
        proc(name)
    elif flag is None:
        try:
            proc(name)
            flag = True
        except:
            flag = False
        _PLUGIN_ENABLED_DICT[name] = flag
    return flag

_PLUGIN_ENABLED_DICT = {}


#------------------------------------------------------------------------------
def affectedAttrNames(nodetype, attrname):
    u"""
    ノードタイプ名とアトリビュート名を指定して、それが影響を与える同一ノードのアトリビュート名リストを得る。

    :param `str` nodetype: ノードタイプ名。
    :param `str` attrname: アトリビュート名。
    :rtype: `list`
    """
    return _affects(attrname, t=nodetype, by=True)


def affectingAttrNames(nodetype, attrname):
    u"""
    ノードタイプ名とアトリビュート名を指定して、それが影響を受ける同一ノードのアトリビュート名リストを得る。

    :param `str` nodetype: ノードタイプ名。
    :param `str` attrname: アトリビュート名。
    :rtype: `list`
    """
    return _affects(attrname, t=nodetype)


#------------------------------------------------------------------------------
def listEnum(name, attrname=None, reverse=False):
    u"""
    enum アトリビュートの名前と値のペアのリストを得る。

    スタティックアトリビュートか
    ダイナミックアトリビュートか
    によって指定方法が異なる。

    :param `str` name:
        ダイナミックアトリビュートの場合はプラグ名、
        スタティックアトリビュートの場合はノードタイプ。
    :param `str` attrname:
        スタティックアトリビュートの場合のアトリビュート名。
    :param `bool` reverse:
        ペアの並び順を入れ替え、
        (名前, 値) ではなく (値, 名前) にする。
    :rtype: `list`
    """
    if attrname:
        desc = _attributeQuery(attrname, typ=name, le=True)[0]
    else:
        desc = _addAttr(name, q=True, en=True)
    _idx = [-1]
    proc = _enumItemRev if reverse else _enumItem
    return [proc(x, _idx) for x in desc.split(':')]


def _enumItem(item, _idx):
    m = _RE_ENUM_DESC_match(item)
    v = m.group(3)
    if v:
        _idx[0] = int(v)
    else:
        _idx[0] += 1
    return m.group(1), _idx[0]


def _enumItemRev(item, _idx):
    m = _RE_ENUM_DESC_match(item)
    v = m.group(3)
    if v:
        _idx[0] = int(v)
    else:
        _idx[0] += 1
    return _idx[0], m.group(1)

# 名前に = が含まれている場合を考慮し split ではなく正規表現を使う。
_RE_ENUM_DESC_match = re.compile(r'(.+?)(=(\d+))?$').match

