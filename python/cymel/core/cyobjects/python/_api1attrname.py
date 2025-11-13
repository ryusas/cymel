# -*- coding: utf-8 -*-
# cymel - Copyright(c) Ryusuke Sasaki
u"""
Maya 2025 の Non-Unique Attribute Name の仕様の API 1 用サポート。

2024 以前でもパス表記をサポートし、両者の違いを吸収する。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re
import maya.OpenMaya as _api

_MFnAttribute = _api.MFnAttribute

IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES = hasattr(_MFnAttribute, 'isEnforcingUniqueName')  #: ユニークでないアトリビュート名をサポートしているバージョンかどうか。

_HEAD_DOTS_sub = re.compile('^\.+').sub

#------------------------------------------------------------------------------
# FIX: Maya2026 UnicodeDecodeError Bug
#
# Maya 2026.0-2026.1 の日本語UI時の API2 のエラーが軒並み UnicodeDecodeError になってしまうバグの対策。
# API1 のエラーは日本語になっていても問題ない。
# 特定のメソッドに限らず、日本語のメッセージを出すものは全てそうなっているようなので、根本的に全てを対策するのは難しく、
# API2 を使うプログラム全体に波及する問題で、範囲を絞りきれないため、
# 各所の excet でエラーを明示するのをできるだけやめるか、明示する場合は以下の _MayaAPI2RuntimeError か _MayaAPI2Errors を使う。
#
# - _MayaAPI2RuntimeError ... API2がraiseするRuntimeError相当の型。Maya2026のバグが考慮されて切り替わる。
# - _MayaAPI2Errors ... API2と混在した周辺スクリプトがraiseするRuntimeError相当の型、またはそれらのtuple。
#
# ちなみに findPlug() は API1 と API2 で挙動が同じなので、関数を共有しているため _CommonApiError を使用しているが、
# attribute() は API1 では RuntimeError だが API2 では Null MObject を返す仕様なため共有していないため問題ない。
#
_MayaAPI2RuntimeError = RuntimeError
try:
    if 20260000 <= _api.MGlobal.apiVersion() < 20260200 and not _api.MGlobal.isDefaultLanguage():
        _MayaAPI2RuntimeError = UnicodeDecodeError
except:
    pass
if _MayaAPI2RuntimeError is RuntimeError:
    _CommonApiError = _MayaAPI2RuntimeError
else:
    _CommonApiError = (_MayaAPI2RuntimeError, RuntimeError)
_MayaAPI2Errors = _CommonApiError


#------------------------------------------------------------------------------
def argToFindComplexMPlug(attrPathTkns):
    u"""
    【API 1 2 兼用】プラグ名トークンから findComplexMPlug の為の引数を得る。
    """
    return [_splitAttrIndex(x) for x in attrPathTkns]


def _splitAttrIndex(name):
    ss = name.split('[')
    n = len(ss)
    if n == 1:
        return name, None
    if n == 2:
        return ss[0], int(ss[1][:-1])
    raise RuntimeError()


#------------------------------------------------------------------------------
def findMPlugAsNodeAttr(mfnnode, name):
    u"""
    【API 1 2 兼用】ドットやインデックスを含まない名前だけで MPlug を得る。

      * 2025以降では、そのままで得られない場合に先頭にドットを付けて探し直される。
      * 2024以前では、そのまま取得されるのみ。
    """
    return mfnnode.findPlug(name, False)


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    __findMPlugAsNodeAttr = findMPlugAsNodeAttr

    def findMPlugAsNodeAttr(mfnnode, name):
        try:
            return mfnnode.findPlug(name, False)
        except _CommonApiError:
            return mfnnode.findPlug('.' + name, False)

    findMPlugAsNodeAttr.__doc__ = __findMPlugAsNodeAttr.__doc__


#------------------------------------------------------------------------------
def findMPlug(mfnnode, attrTkns, wantNetworked, strict=False):
    u"""
    【API 1 2 兼用】argToFindComplexMPlug で分解したパスから MPlug を得る。

      * 2025以降では、パス指定に基づいて取得される。
        先頭ドットを省略した場合はトップレベルが優先される（先頭ドット無しで得られない場合は、先頭ドットを付けて再取得が試みられる）。
        strint=False ならば、先頭ドットが指定されてもトップレベル以外のユニーク名のアトリビュートを得られる。

      * 2024以前では、末尾で取得されるだけでパスのチェックはされない。
        パスのチェックは `selectAncestorLogicalIndices` で行うものとする。
        strict フラグもここでは無視される。
    """
    return mfnnode.findPlug(attrTkns[-1][0], wantNetworked)


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    __findMPlug = findMPlug

    def findMPlug(mfnnode, attrTkns, wantNetworked, strict=False):
        name = '.'.join([x[0] for x in attrTkns])
        if not name.startswith('.'):
            try:
                return mfnnode.findPlug(name, wantNetworked)
            except _CommonApiError:
                return mfnnode.findPlug('.' + name, wantNetworked)
        elif strict:
            return mfnnode.findPlug(name, wantNetworked)
        else:
            try:
                return mfnnode.findPlug(name, wantNetworked)
            except _CommonApiError:
                return mfnnode.findPlug(_HEAD_DOTS_sub('', name), wantNetworked)

    findMPlug.__doc__ = __findMPlug.__doc__


#------------------------------------------------------------------------------
def findMAttr(mfnnode, attrTkns, i=-1, strict=False):
    u"""
    argToFindComplexMPlug で分解したパス（インデックス指定で途中までの解釈も可能）からアトリビュート MObject を得る。

      * 2025以降では、パス指定に基づいて取得される。
        先頭ドットを省略した場合はトップレベルが優先される（先頭ドット無しで得られない場合は、先頭ドットを付けて再取得が試みられる）。
        strint=False ならば、先頭ドットが指定されてもトップレベル以外のユニーク名のアトリビュートを得られる。

      * 2024以前では、末尾でのみ取得されるだけでパスのチェックはされない。
        strict フラグもここでは無視される。

    得られない場合は RuntimeError になる（API2と異なる）。
    """
    return mfnnode.attribute(attrTkns[i][0])


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    __findMAttr = findMAttr

    def findMAttr(mfnnode, attrTkns, i=-1, strict=False):
        if i != -1:
            attrTkns = attrTkns[:i + 1]
        name = '.'.join([x[0] for x in attrTkns])
        if not name.startswith('.'):
            try:
                return mfnnode.attribute(name)
            except RuntimeError:
                return mfnnode.attribute('.' + name)
        elif strict:
            return mfnnode.attribute(name)
        else:
            try:
                return mfnnode.attribute(name)
            except RuntimeError:
                return mfnnode.attribute(_HEAD_DOTS_sub('', name))

    findMAttr.__doc__ = __findMAttr.__doc__


#------------------------------------------------------------------------------
def selectAncestorLogicalIndices(mplug, mfnnode, attrTkns, strict=False):
    u"""
    argToFindComplexMPlug で分解したパスの上位のロジカルインデックスを選択する。

      * 2025以降では、findMPlug でパスはチェックされているものとして、ここでは strict フラグは無視される。
      * 2024以前では、strict=True ならば、それにともないパスの整合性もチェックされる。
    """
    inferior = None
    for i, (name, idx) in list(enumerate(attrTkns))[-2::-1]:
        if name:
            try:
                mattr = findMAttr(mfnnode, attrTkns, i, True)
            except RuntimeError:
                if i:
                    raise RuntimeError()
                refPlug = _findAliasMPlug(mfnnode, name, False)
                if refPlug.isElement() and idx is not None:
                    raise RuntimeError()
                _selectAncestorIndicesByMPlug(mplug, refPlug)

            if idx is not None:
                mplug.selectAncestorLogicalIndex(idx, mattr)

            elif not isAncestorAttrOf(mattr, inferior or mplug.attribute()):
                raise RuntimeError()
            inferior = mattr

        elif idx is not None:
            raise RuntimeError()
        elif strict:
            try:
                _MFnAttribute(inferior or mplug.attribute()).parent()
            except:
                pass
            else:
                raise RuntimeError()


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    __selectAncestorLogicalIndices = selectAncestorLogicalIndices

    def selectAncestorLogicalIndices(mplug, mfnnode, attrTkns, strict=False):
        for i, (name, idx) in enumerate(attrTkns[:-1]):
            if name:
                try:
                    mattr = findMAttr(mfnnode, attrTkns, i, True)
                except RuntimeError:
                    if i:
                        raise RuntimeError()
                    refPlug = _findAliasMPlug(mfnnode, name, False)
                    if refPlug.isElement() and idx is not None:
                        raise RuntimeError()
                    _selectAncestorIndicesByMPlug(mplug, refPlug)

                if idx is not None:
                    mplug.selectAncestorLogicalIndex(idx, mattr)

            elif idx is not None:
                raise RuntimeError()

    selectAncestorLogicalIndices.__doc__ = __selectAncestorLogicalIndices.__doc__


def _selectAncestorIndicesByMPlug(mplug, refPlug):
    u"""
    mplug の上位のインデックスを refPlug によって選択する。
    """
    while True:
        if refPlug.isElement():
            mplug.selectAncestorLogicalIndex(refPlug.logicalIndex(), refPlug.attribute())
            refPlug = refPlug.array()
        if not refPlug.isChild():
            return
        refPlug = refPlug.parent()


def _findAliasMPlug(mfnnode, name, wantNetworked):
    u"""
    エイリアス名から MPlug を得る。
    """
    ss = []
    if mfnnode.getAliasList(ss):
        origName = dict(zip(ss[::2], ss[1::2])).get(name)
        if origName:
            return findComplexMPlug(mfnnode, argToFindComplexMPlug(origName.split('.')), wantNetworked, False)
    raise RuntimeError()


#------------------------------------------------------------------------------
def isAncestorAttrOf(mthis, mattr):
    u"""
    アトリビュート mthis が mattr の上位であるかを返す。
    """
    try:
        mattr = _MFnAttribute(mattr).parent()
    except:
        return False
    while mattr != mthis:
        try:
            mattr = _MFnAttribute(mattr).parent()
        except:
            return False
    return True


def findComplexMPlug(mfnnode, attrTkns, wantNetworked=False, alias=True, strict=False):
    u"""
    プラグ階層途中の省略表記や、エイリアスや、-1インデックスなどにも対応して MPlug を得る。

    :param `bool` strict:
        先頭がドットの場合はトップレベルのアトリビュートと解釈する。
    """
    nTkns = len(attrTkns)
    try:
        # 末尾のプラグを得る。2025以降ならこの時点でパスもチェックされる。
        mplug = findMPlug(mfnnode, attrTkns, wantNetworked, strict)

    except RuntimeError:
        # 上位が指定されている場合はエイリアス名ではない。
        if nTkns > 2 or (nTkns == 2 and attrTkns[0][0]):
            raise

        # エイリアスアトリビュートを取得してみる。
        leafName, leafIdx = attrTkns[-1]
        mplug = _findAliasMPlug(mfnnode, leafName, wantNetworked)

    else:
        # 上位のロジカルインデックスを選択する。2024以前ならパスもチェック。
        if nTkns > 1:
            selectAncestorLogicalIndices(mplug, mfnnode, attrTkns, strict)
        leafIdx = attrTkns[-1][1]

    # 末尾のロジカルインデックスを選択する。
    if leafIdx is not None:
        if mplug.isElement():
            raise RuntimeError()
        if wantNetworked:
            mplug = mplug.elementByLogicalIndex(leafIdx)
        else:
            mplug.selectAncestorLogicalIndex(leafIdx)
    return mplug

