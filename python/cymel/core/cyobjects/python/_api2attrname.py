# -*- coding: utf-8 -*-
# cymel - Copyright(c) Ryusuke Sasaki
u"""
Maya 2025 の Non-Unique Attribute Name の仕様の API 2 用サポート。

2024 以前でもパス表記をサポートし、両者の違いを吸収する。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ._api1attrname import (
    IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES,
    findMPlugAsNodeAttr,
    findMPlug,
    argToFindComplexMPlug,
    _HEAD_DOTS_sub,
    _MayaAPI2RuntimeError, _MayaAPI2Errors,
)
import maya.api.OpenMaya as _api

_MFnAttribute = _api.MFnAttribute


# NOTE: mfn.attribute(name) は失敗すると Null MObject を返すが、2012以前では RuntimeError になる。
# しかし、cymel python 実装は 2015 以降のサポートのため考慮しない。


#------------------------------------------------------------------------------
def findMAttrToGetInferiorPlug(mfnnode, name, plug):
    u"""
    Plug の下位の MPlug を得るためのアトリビュート MObject を得る。
    2025以降はPlugのパスから下層のものとして取得されるが、2024以前は名前から取得されるだけで下層のものである保証はされない。

    得られない場合もエラーにはならず Null の MObject が返される。
    """
    return mfnnode.attribute(name)  # NOTE: Maya2012以前は要注意。

__findMAttrToGetInferiorPlug = findMAttrToGetInferiorPlug


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    def findMAttrToGetInferiorPlug(mfnnode, name, plug):
        return mfnnode.attribute(plug.mfn_().pathName() + '.' + name)  # 直接の子でなくても下位にあれば通る。

    findMAttrToGetInferiorPlug.__doc__ = __findMAttrToGetInferiorPlug.__doc__


#------------------------------------------------------------------------------
def findMAttr(mfnnode, attrTkns, i=-1, strict=False):
    u"""
    argToFindComplexMPlug で分解したパス（インデックス指定で途中までの解釈も可能）からアトリビュート MObject を得る。

      * 2025以降では、パス指定に基づいて取得される。
        先頭ドットを省略した場合はトップレベルが優先される（先頭ドット無しで得られない場合は、先頭ドットを付けて再取得が試みられる）。
        strint=False ならば、先頭ドットが指定されてもトップレベル以外のユニーク名のアトリビュートを得られる。

      * 2024以前では、末尾でのみ取得されるだけでパスのチェックはされない。
        strict フラグもここでは無視される。

    得られない場合もエラーにはならず Null の MObject が返される（API1と異なる）。
    """
    return mfnnode.attribute(attrTkns[i][0])  # NOTE: Maya2012以前は要注意。

__findMAttr = findMAttr


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    def findMAttr(mfnnode, attrTkns, i=-1, strict=False):
        if i != -1:
            attrTkns = attrTkns[:i + 1]
        name = '.'.join([x[0] for x in attrTkns])
        if not name.startswith('.'):
            o = mfnnode.attribute(name)
            return mfnnode.attribute('.' + name) if o.isNull() else o
        elif strict:
            return mfnnode.attribute(name)
        else:
            o = mfnnode.attribute(name)
            return mfnnode.attribute(_HEAD_DOTS_sub('', name)) if o.isNull() else o

    findMAttr.__doc__ = __findMAttr.__doc__


#------------------------------------------------------------------------------
def hasNodeAttribute(mfnnode, name, alias=False, strict=False):
    u"""
    ノードがアトリビュートを持つかどうか。

    MFnAttribute.hasAttribute より判定基準はゆるく、ドットから始まるフルパス指定が必要な場合でも省略を許容する。

    先頭ドットを省略した場合はトップレベルが優先される（先頭ドット無しで得られない場合は、先頭ドットを付けて再検査が試みられる）。
    この点は 2025 以降の MFnAttribute.hasAttribute より判定基準がゆるい。

    strint=False ならば、先頭ドットが指定されてもトップレベル以外のユニーク名のアトリビュートなら許容される。
    """
    # 末尾のアトリビュートのチェック。
    if not strict:
        name = _HEAD_DOTS_sub('', name)
    tkns = name.split('.')
    name = tkns.pop()
    if not tkns:
        return mfnnode.hasAttribute(name) or (alias and not mfnnode.findAlias(name).isNull())

    # 上位のパスのチェック。
    mattr = mfnnode.attribute(name)  # NOTE: Maya2012以前は要注意。
    if mattr.isNull():
        return False
    while tkns:
        name = tkns.pop()
        mattr = _MFnAttribute(mattr).parent
        if mattr.isNull():
            return not name and not tkns

        parent = mfnnode.attribute(name)  # NOTE: Maya2012以前は要注意。
        if parent.isNull():
            if not alias or (tkns and (tkns[-1] or len(tkns) > 1)):
                return False
            parent = mfnnode.findAlias(name)
            if parent.isNull():
                return False
        if mattr != parent:
            return False
    return True


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    __hasNodeAttribute = hasNodeAttribute

    def hasNodeAttribute(mfnnode, name, alias=False, strict=False):
        # APIがパス名を受け付けるのでそのまま指定。
        if mfnnode.hasAttribute(name):
            return True

        # 先頭ドット有りで見つからなかった場合、strict=False ならドット無しで再探索。
        if name.startswith('.'):
            name = _HEAD_DOTS_sub('', name)
            if not strict and mfnnode.hasAttribute(name):
                return True
        # 先頭ドット無しで見つからなかった場合、ドットを付けて再探索。
        elif mfnnode.hasAttribute('.' + name):
            return True

        # 先頭をエイリアスとして再探索。
        if not alias:
            return False
        tkns = name.split('.')
        mattr = mfnnode.findAlias(tkns[0])
        if mattr.isNull():
            return False
        if len(tkns) == 1:
            return True
        tkns[0] = _MFnAttribute(mattr).pathName()
        return mfnnode.hasAttribute('.'.join(tkns))

    hasNodeAttribute.__doc__ = __hasNodeAttribute.__doc__


#------------------------------------------------------------------------------
def findNodeMAttr(mfnnode, name, alias=False, strict=False):
    u"""
    hasNodeAttribute と同じ要領で MObject を得る。

    MFnAttribute.hasAttribute より判定基準はゆるく、ドットから始まるフルパス指定が必要な場合でも省略を許容する。

    先頭ドットを省略した場合はトップレベルが優先される（先頭ドット無しで得られない場合は、先頭ドットを付けて再検査が試みられる）。
    この点は 2025 以降の MFnAttribute.attribute より判定基準がゆるい。

    strint=False ならば、先頭ドットが指定されてもトップレベル以外のユニーク名のアトリビュートなら許容される。
    """
    # 末尾のアトリビュートの取得。
    if not strict:
        name = _HEAD_DOTS_sub('', name)
    tkns = name.split('.')
    name = tkns.pop()
    mattr = mfnnode.attribute(name)  # NOTE: Maya2012以前は要注意。
    if not tkns:
        if not mattr.isNull():
            return mattr
        if alias:
            mattr = mfnnode.findAlias(name)
            if not mattr.isNull():
                return mattr
        return

    # 上位のパスのチェック。
    if mattr.isNull():
        return
    while tkns:
        name = tkns.pop()
        mattr = _MFnAttribute(mattr).parent
        if mattr.isNull():
            if not name and not tkns:
                return mattr
            return

        parent = mfnnode.attribute(name)  # NOTE: Maya2012以前は要注意。
        if parent.isNull():
            if not alias or (tkns and (tkns[-1] or len(tkns) > 1)):
                return
            parent = mfnnode.findAlias(name)
            if parent.isNull():
                return
        if mattr != parent:
            return
    return mattr


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    __findNodeMAttr = findNodeMAttr

    def findNodeMAttr(mfnnode, name, alias=False, strict=False):
        # APIがパス名を受け付けるのでそのまま指定。
        mattr = mfnnode.attribute(name)
        if not mattr.isNull():
            return mattr

        # 先頭ドット有りで見つからなかった場合、strict=False ならドット無しで再探索。
        if name.startswith('.'):
            name = _HEAD_DOTS_sub('', name)
            if not strict:
                mattr = mfnnode.attribute(name)
                if not mattr.isNull():
                    return mattr
        # 先頭ドット無しで見つからなかった場合、ドットを付けて再探索。
        else:
            mattr = mfnnode.attribute('.' + name)
            if not mattr.isNull():
                return mattr

        # 先頭をエイリアスとして再探索。
        if not alias:
            return
        tkns = name.split('.')
        mattr = mfnnode.findAlias(tkns[0])
        if mattr.isNull():
            return
        if len(tkns) == 1:
            return mattr
        tkns[0] = _MFnAttribute(mattr).pathName()
        mattr = mfnnode.attribute('.'.join(tkns))
        if not mattr.isNull():
            return mattr

    findNodeMAttr.__doc__ = __findNodeMAttr.__doc__


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
            mattr = findMAttr(mfnnode, attrTkns, i, True)
            if mattr.isNull():
                if i:
                    raise RuntimeError()
                mattr = mfnnode.findAlias(name)
                if mattr.isNull():
                    raise RuntimeError()
                _selectAliasAttrAncestorIndices(mplug, mfnnode, name, idx, mattr)
            if idx is not None:
                mplug.selectAncestorLogicalIndex(idx, mattr)
            elif not isAncestorAttrOf(mattr, inferior or mplug.attribute()):
                raise RuntimeError()
            inferior = mattr
        elif idx is not None or (strict and not _MFnAttribute(inferior or mplug.attribute()).parent.isNull()):
            raise RuntimeError()


if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    __selectAncestorLogicalIndices = selectAncestorLogicalIndices

    def selectAncestorLogicalIndices(mplug, mfnnode, attrTkns, strict=False):
        for i, (name, idx) in enumerate(attrTkns[:-1]):
            if name:
                mattr = findMAttr(mfnnode, attrTkns, i, True)
                if mattr.isNull():
                    if i:
                        raise RuntimeError()
                    mattr = mfnnode.findAlias(name)
                    if mattr.isNull():
                        raise RuntimeError()
                    _selectAliasAttrAncestorIndices(mplug, mfnnode, name, idx, mattr)
                if idx is not None:
                    mplug.selectAncestorLogicalIndex(idx, mattr)
            elif idx is not None:
                raise RuntimeError()

    selectAncestorLogicalIndices.__doc__ = __selectAncestorLogicalIndices.__doc__


def _selectAliasAttrAncestorIndices(mplug, mfnnode, aliasName, leafIdx=None, leafMObj=None):
    u"""
    エイリアスアトリビュートの上位のインデックスを選択する。

    :param mplug: 操作対象のMPlug。エイリアスの参照先よりさらに深い場合も許容。
    :param mfnnode: ノードのファンクションセット。
    :param aliasName: エイリアス名。
    :param leafIdx:
        さらに外側で指定されたインデックス。
        エイリアス参照先とのインデックス二重指定をエラーにするための判別用。
    :param leafMObj:
        エイリアス名から findAlias で得られたアトリビュート MObject 。
        mplug のアトリビュートそのものの場合は None を指定する。
    """
    attrTkns = argToFindComplexMPlug(dict(mfnnode.getAliasList())[aliasName].split('.'))
    for i, (name, idx) in enumerate(attrTkns[:-1]):
        if name and idx is not None:
            mplug.selectAncestorLogicalIndex(idx, __findMAttr(mfnnode, attrTkns, i, True))
    idx = attrTkns[-1][1]
    if idx is not None:
        if leafIdx is not None:
            raise RuntimeError()
        if leafMObj:
            mplug.selectAncestorLogicalIndex(idx, leafMObj)
        else:
            mplug.selectAncestorLogicalIndex(idx)


#------------------------------------------------------------------------------
def isAncestorAttrOf(mthis, mattr):
    u"""
    アトリビュート mthis が mattr の上位であるかを返す。
    """
    mattr = _MFnAttribute(mattr).parent
    while mattr != mthis:
        if mattr.isNull():
            return False
        mattr = _MFnAttribute(mattr).parent
    return True


def findSimpleMPlug(mfnnode, name):
    u"""
    ドットやインデックスを含まない名前だけで MPlug を得る。エイリアス名も許容。
    """
    try:
        return findMPlugAsNodeAttr(mfnnode, name)
    except _MayaAPI2RuntimeError:
        mattr = mfnnode.findAlias(name)
        if not mattr.isNull():
            mplug = mfnnode.findPlug(mattr, False)
            _selectAliasAttrAncestorIndices(mplug, mfnnode, name)
            return mplug


def findComplexMPlug(mfnnode, attrTkns, wantNetworked=False, strict=False):
    u"""
    プラグ階層途中の省略表記や、エイリアスや、-1インデックスなどにも対応して MPlug を得る。

    :param `bool` strict:
        先頭がドットの場合はトップレベルのアトリビュートと解釈する。
    """
    nTkns = len(attrTkns)
    try:
        # 末尾のプラグを得る。2025以降ならこの時点でパスもチェックされる。
        mplug = findMPlug(mfnnode, attrTkns, wantNetworked, strict)

    except _MayaAPI2RuntimeError:
        # 上位が指定されている場合はエイリアス名ではない。
        if nTkns > 2 or (nTkns == 2 and attrTkns[0][0]):
            raise

        # エイリアスアトリビュートを取得してみる。
        leafName, leafIdx = attrTkns[-1]
        mattr = mfnnode.findAlias(leafName)
        if mattr.isNull():
            raise
        mplug = mfnnode.findPlug(mattr, wantNetworked)
        _selectAliasAttrAncestorIndices(mplug, mfnnode, leafName, leafIdx)

    else:
        # 上位のロジカルインデックスを選択する。2024以前ならパスもチェック。
        if nTkns > 1:
            selectAncestorLogicalIndices(mplug, mfnnode, attrTkns, strict)
        leafIdx = attrTkns[-1][1]

    # 末尾のロジカルインデックスを選択する。
    if leafIdx is not None:
        if mplug.isElement:
            raise RuntimeError()
        if wantNetworked:
            mplug = mplug.elementByLogicalIndex(leafIdx)
        else:
            mplug.selectAncestorLogicalIndex(leafIdx)
    return mplug

