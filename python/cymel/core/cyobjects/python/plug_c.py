# -*- coding: utf-8 -*-
u"""
`.Plug` クラスでサポートする機能の中核。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from functools import partial
from ..typeinfo import isDerivedNodeType as _isDerivedNodeType
from ._api2attrname import (
    IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES,
    findMAttrToGetInferiorPlug as _findMAttrToGetInferiorPlug,
    isAncestorAttrOf as _isAncestorAttrOf,
)
from .cyobject import (
    CyObject,
    CY_NODE, CY_PLUG, CY_OBJREF,
    _initAPI1Objects,
    _setPlugCache,
    _newNodeRefPlug,
    _node4ArgsByMPlug,
    _newNodeObjByArgs,
    _newNodeRefByArgs,
)
from .objectref import _getObjectRef
from ._api2mplug import (
    nonNetworkedElemMPlug,
    toNonNetworkedElemMPlug,
    nonNetworkedMPlug,
    toNonNetworkedMPlug,
    getConnWithoutUC,
    fixUnitTypeInfo,
    attrToRawValue, unitAttrToRawValue,
    attrToUnitValue, unitAttrToUnitValue,
    attrFromRawValue, attrFromUnitValue,
    mplugGetRawValue, mplugGetUnitValue,
    mplugCurrentValueSetter, mplugApiValueSetter,
    mplug_get_matrix,
    _RE_NUMERIC_COMPOUND_match,
)
import maya.api.OpenMaya as _api2

__all__ = []

_MFn = _api2.MFn
_2_MPlug = _api2.MPlug
_2_MFnAttribute = _api2.MFnAttribute
_2_MFnCompoundAttribute = _api2.MFnCompoundAttribute
_2_MFnMatrixData = _api2.MFnMatrixData
_2_MFnUnitAttribute = _api2.MFnUnitAttribute
_2_MFnNumericAttribute = _api2.MFnNumericAttribute

_2_MPlug_logicalIndex = _2_MPlug.logicalIndex
_2_MPlug_connectedTo = _2_MPlug.connectedTo

_2_MObject_kNullObj = _api2.MObject.kNullObj

_attributeName = cmds.attributeName

_type = type

#_RE_ATTRNAME_search = re.compile(r'([^.[]+)(?:\[\d+\])?$').search

_apiobject_error = AttributeError('has no attribute: __apiobject__')


#------------------------------------------------------------------------------
class Plug_c(CyObject):
    u"""
    `.Plug` クラスでサポートする機能の中核。
    """
    __slots__ = ('__lenCalled',)

    CLASS_TYPE = CY_PLUG  #: ラッパークラスの種類が `.Plug` であることを表す。

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
        obj = super(Plug_c, cls).newObject(data)
        obj.__lenCalled = False
        return obj

    def __len__(self):
        u"""
        maya.cmds を騙すために常に 1 を返す。

        __getitem__ が実装されているオブジェクトの場合、
        maya はシーケンスと解釈し __len__ を評価し、
        その数だけ __getitem__ が呼ばれることになる。

        そこで __len__ を呼ぶのは maya.cmds のみであるとの前提で
        常に 1 を返すようにして、その直後の __getitem__ では
        self を返すように制御する。
        """
        self.__lenCalled = True
        return 1

    #def __getattribute__(self, name):
    #    print('__getattribute__: ' + name)
    #    return getattr(Plug_c, name).__get__(self)

    def __getitem__(self, idx):
        u"""
        マルチアトリビュートの要素を論理インデックスで得る。
        """
        if self.__lenCalled:
            self.__lenCalled = False
            return self

        self.checkValid()
        mplug = self._CyObject__data['mplug']
        if not mplug.isArray:
            raise TypeError('plug is not an array: ' + self.name_())

        # スライスはサポートしない。
        #if isinstance(idx, slice):
        #    cls = _type(self)
        #    noderef = self._CyObject__data['noderef']
        #    info = self._CyObject__data['typeinfo']
        #    num = mplug.elementByPhysicalIndex(mplug.numElements() - 1).logicalIndex() + 1
        #    return [_newNodeRefPlug(cls, noderef, _2_MPlug(mplug).selectAncestorLogicalIndex(i), info) for i in range(*idx.indices(num))]

        # マルチアトリビュートの要素には、同じ typeinfo を渡せる（同じタイプ名、同じMObject）。
        return _newNodeRefPlug(_type(self), self._CyObject__data['noderef'], _2_MPlug(mplug).selectAncestorLogicalIndex(idx), self._CyObject__data['typeinfo'])

    def __getattr__(self, name):
        u"""
        下位のプラグを得る。
        """
        if name == '__apiobject__':
            raise _apiobject_error
        self.checkValid()
        return self.__getInferiorPlug(name)

    def node(self):
        u"""
        ノードを得る。

        :rtype: `.Node` 派生クラス
        """
        node = self._CyObject__data['noderef'].object()
        if not node:
            node = self._CyObject__data['noderef']._newobject()
            _setPlugCache(node, self)
        return node

    def noderef(self):
        u"""
        ノードの弱参照ラッパーを得る。

        :rtype: `.ObjectRef`
        """
        return self._CyObject__data['noderef']

    def nodeName(self):
        u"""
        ノード名を得る。

        :rtype: `str`
        """
        self.checkValid()
        return self._CyObject__data['noderef']._CyObject__data['getname']()

    def nodeType(self):
        u"""
        ノードタイプ名を得る。

        :rtype: `str`
        """
        return self._CyObject__data['noderef']._CyObject__data['nodetype']

    def isNodeType(self, typename):
        u"""
        ノードが指定タイプの派生型かどうか。

        :param `str` typename: ノードタイプ名。
        :rtype: `bool`
        """
        dt = self._CyObject__data['noderef']._CyObject__data
        return _isDerivedNodeType(dt['nodetype'], typename, dt['getname']())

    def hasNodeFn(self, fn):
        u"""
        ノードが指定ファンクションタイプと互換性があるかどうか。

        :param `int` fn: :mayaapi2:`MFn` タイプ。
        :rtype: `bool`
        """
        dt = self._CyObject__data['noderef']._CyObject__data
        dt['isValid']()
        return dt['mnode'].hasFn(fn)

    def mplug(self):
        u"""
        Python API 2 の :mayaapi2:`MPlug` を得る。

        :rtype: :mayaapi2:`MPlug`
        """
        self.checkValid()
        return self._CyObject__data['mplug']

    def mplug_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 2 の :mayaapi2:`MPlug` を得る。

        :rtype: :mayaapi2:`MPlug`
        """
        return self._CyObject__data['mplug']

    def mplug1(self):
        u"""
        Python API 1 の :mayaapi1:`MPlug` を得る。

        :rtype: :mayaapi1:`MPlug`
        """
        self.checkValid()
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mplug1']

    def mplug1_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 1 の :mayaapi1:`MPlug` を得る。

        :rtype: :mayaapi1:`MPlug`
        """
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mplug1']

    def mfn(self):
        u"""
        Python API 2 のファンクションセットを得る。

        :rtype: :mayaapi2:`MFnAttribute` の派生
        """
        self.checkValid()
        return self._CyObject__data['typeinfo']['mfn']

    def mfn_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 2 のファンクションセットを得る。

        :rtype: :mayaapi2:`MFnAttribute` の派生
        """
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['typeinfo']['mfn']

    def mfn1(self):
        u"""
        Python API 1 のファンクションセットを得る。

        :rtype: :mayaapi1:`MFnAttribute` の派生
        """
        self.checkValid()
        _initAPI1Objects(self._CyObject__data)
        return self._CyObject__data['mfn1']

    def mfn1_(self):
        u"""
        `~.CyObject.checkValid` を省略して、 Python API 1 のファンクションセットを得る。

        :rtype: :mayaapi1:`MFnAttribute` の派生
        """
        return self._CyObject__data['mfn1']

    def type(self):
        u"""
        アトリビュートタイプ名を得る。判別できないタイプは '' になる。

        :rtype: `str`
        """
        return self._CyObject__data['typeinfo']['typename']

    def subType(self):
        u"""
        数値コンパウンド（ double3 等）アトリビュートの要素のタイプ名を得る。

        一般コンパウンドでも数値コンパウンドと同等に扱うべきタイプの場合もそのタイプが返される。
        たとえば、quatNodes プラグインのクォータニオンアトリビュートは一般コンパウンドだが double となる。

        :rtype: `str` or `None`
        """
        self.checkValid()
        fixUnitTypeInfo(self._CyObject__data['typeinfo'])
        return self._CyObject__data['typeinfo'].get('subtype')

    def _unittype(self):
        u"""
        内部的に使用される単位情報を含んだ型名を得る。

        通常は `type` と同じだが、
        数値コンパウンドかそれと同等の一般コンパウンドの場合に、以下の規則で型名と異なる名前になる。

        * `subType` が単位付き数値型の場合、数値コンパウンド名に単位型名を連結した名前になる（例: double3doubleAngle など）。
        * `subType` が単位無し数値型の場合、数値コンパウンド名になる（例: double3 など）。

        :rtype: `str`
        """
        self.checkValid()
        fixUnitTypeInfo(self._CyObject__data['typeinfo'])
        return self._CyObject__data['typeinfo'].get('unittype')

    if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
        def isEnforcingUniqueName(self):
            u"""
            これが固有のアトリビュート名であることをノードに強制しているかどうか。

            Maya 2025 以降はアトリビュートごとの設定値（デフォルトは True）が返され、
            それより前のバージョンだと常に True が返される。

            :rtype: `bool`
            """
            return self.mfn().enforcingUniqueName

        def pathName(self, useLongName=True, useCompression=True):
            u"""
            アトリビュートのユニークなパス名を返す。インデックスは含まない。

            Maya 2025 以降で非ユニーク名なら . (ドット) で区切られたパスが返される。
            ユニーク名で且つ useCompression=True (デフォルト) か、
            2024 以前なら常に単一のアトリビュート名が返される。

            :param `bool` useLongName:
                デフォルトの True だとロング名が使用される。
                False を指定するとショート名が使用される。
            :param `bool` useCompression:
                デフォルトの True だと可能な限り短いパス名が返される
                （DAGパスでいうところの partial path name ）。
                False を指定するとトップレベルからのパス名が返されるが、
                ユニークである限り先頭のドットは付加されない（APIの挙動）。
            :rtype: `str`
            """
            return self.mfn().pathName(useLongName, useCompression)

    else:
        def isEnforcingUniqueName(self):
            u"""
            これが固有のアトリビュート名であることをノードに強制しているかどうか。

            Maya 2025 以降はアトリビュートごとの設定値（デフォルトは True）が返され、
            それより前のバージョンだと常に True が返される。

            :rtype: `bool`
            """
            return True

        def pathName(self, useLongName=True, useCompression=True):
            u"""
            アトリビュートのユニークなパス名を返す。インデックスは含まない。

            Maya 2025 以降で非ユニーク名なら . (ドット) で区切られたパスが返される。
            ユニーク名で且つ useCompression=True (デフォルト) か、
            2024 以前なら常に単一のアトリビュート名が返される。

            :param `bool` useLongName:
                デフォルトの True だとロング名が使用される。
                False を指定するとショート名が使用される。
            :param `bool` useCompression:
                デフォルトの True だと可能な限り短いパス名が返される
                （DAGパスでいうところの partial path name ）。
                False を指定するとトップレベルからのパス名が返されるが、
                ユニークである限り先頭のドットは付加されない（APIの挙動）。
            :rtype: `str`
            """
            return '.'.join([
                x.split('[')[0]
                for x in self._CyObject__data['mplug'].partialName(useFullAttributePath=not useCompression, useLongNames=useLongName).split('.')
            ])

    def isAffectsAppearance(self):
        u"""
        ビューポートに影響を与えるかどうか。

        :rtype: `bool`
        """
        return self.mfn().affectsAppearance

    def isAffectsWorldSpace(self):
        u"""
        ワールドスペースに影響を与えるかどうか。

        :rtype: `bool`
        """
        return self.mfn().affectsWorldSpace

    def isArray(self):
        u"""
        マルチアトリビュートかどうか。

        :rtype: `bool`
        """
        return self.mplug().isArray
        # MFnAttribute だとエレメント場合も True になってしまうのでダメ。

    isMulti = isArray  #: `isArray` の別名。

    def isCaching(self, static=False):
        u"""
        値がデータブロックにキャッシュされるかどうか。

        :param `bool` static: 静的な設定をチェックする。
        :rtype: `bool`
        """
        # Should attr value be cached in the datablock?
        if static:
            return self.mfn().cached
        else:
            return self.mplug().isCaching

    isCached = isCaching  # `isCaching` の別名。

    def isChannelBox(self, static=False):
        u"""
        Keyable でなくてもチャンネルボックスに出すかどうか。

        :rtype: `bool`
        """
        # Should attr appear in Channel Box?
        if static:
            return self.mfn().channelBox
        else:
            return self.mplug().isChannelBox

    def isChild(self):
        u"""
        コンパウンドの子アトリビュートかどうか。

        :rtype: `bool`
        """
        return self.mplug().isChild

    def isCompound(self):
        u"""
        コンパウンドアトリビュートかどうか。

        :rtype: `bool`
        """
        return self.mplug().isCompound

    def isConnectable(self):
        u"""
        コネクト可能かどうか。

        :rtype: `bool`
        """
        return self.mfn().connectable

    def disconnectBehavior(self):
        u"""
        マルチアトリビュートの要素の削除時の振る舞いを得る。

        :rtype: `int`
        """
        return self.mfn().disconnectBehavior

    def isDynamic(self):
        u"""
        ダイナミックアトリビュートかどうか。

        :rtype: `bool`
        """
        return self.mfn().dynamic

    def isElement(self):
        u"""
        マルチアトリビュートの要素かどうか。

        :rtype: `bool`
        """
        return self.mplug().isElement

    def isExtension(self):
        u"""
        拡張アトリビュートかどうか。

        :rtype: `bool`

        .. note::
            拡張アトリビュートとは 2011 で追加された
            既存ノードタイプにスタティックアトリビュートを追加する機能。
        """
        return self.mfn().extension

    def isHidden(self):
        u"""
        隠しアトリビュートかどうか。

        :rtype: `bool`
        """
        return self.mfn().hidden

    def isIgnoredWhenRendering(self):
        u"""
        レンダリング中にはコネクションが無視されるかどうか。

        :rtype: `bool`
        """
        return self.mplug().isIgnoredWhenRendering

    def isIndeterminant(self):
        u"""
        Hint to DG that this attr may not always be used when computing the attrs which are dependent upon it.

        :rtype: `bool`
        """
        return self.mfn().indeterminant

    def indexMatters(self):
        u"""
        マルチ要素のインデックスが意味を持つかどうか。

        この値と `isReadable` が False の場合に :mayacmd:`connectAttr` -na が使える。

        :rtype: `bool`
        """
        return self.mfn().indexMatters

    isIndexMatters = indexMatters  #: `indexMatters` の別名。

    def isInternal(self):
        u"""
        インターナルアトリビュートかどうか。

        :rtype: `bool`
        """
        return self.mfn().internal

    def isKeyable(self):
        u"""
        Keyable かどうか。

        :rtype: `bool`
        """
        return self.mplug().isKeyable

    def isProcedural(self):
        u"""
        Maya が内部的に使用する手続き型プラグかどうか。

        :rtype: `bool`
        """
        return self.mplug().isProcedural

    def isReadable(self):
        u"""
        読めるか（値をゲットしたりコネクションの入力元と成り得るか）どうか。

        :rtype: `bool`
        """
        return self.mfn().readable

    def isRenderSource(self):
        u"""
        レンダーソースかどうか。

        :rtype: `bool`
        """
        return self.mfn().renderSource

    def isStorable(self):
        u"""
        ファイルに保存されるかどうか。

        :rtype: `bool`
        """
        return self.mfn().storable

    def isUsedAsColor(self):
        u"""
        カラーとして使われるものかどうか。

        :rtype: `bool`
        """
        return self.mfn().usedAsColor

    def isUsedAsFilename(self):
        u"""
        ファイル名として使われるものかどうか。

        :rtype: `bool`
        """
        return self.mfn().usedAsFilename

    def isUsedArrayDataBuilder(self):
        u"""
        API の MArrayDataBuilder が使われるかどうか。

        :rtype: `bool`
        """
        return self.mfn().usesArrayDataBuilder

    def isWorldSpace(self):
        u"""
        DAGノードインスタンスに結びついたマルチアトリビュートかどうか。

        :rtype: `bool`
        """
        return self.mfn().worldSpace

    def isWritable(self):
        u"""
        書き込めるか（値をセットしたりコネクションの出力先と成り得るか）どうか。

        :rtype: `bool`
        """
        return self.mfn().writable

    def isNewAttribute(self):
        u"""
        リファレンスではないアトリビュートかどうか。

        そもそもノードがリファレンスファイルのものでないか、
        ファイルリファレンスした後に追加されたアトリビュートの場合に
        True となる。

        `isAttrFromReferencedFile` の逆の結果が得られる。

        :rtype: `bool`
        """
        self.checkValid()
        return self._CyObject__data['noderef']._CyObject__data['mfn'].isNewAttribute(
            self._CyObject__data['mplug'].attribute())

    isNewAttr = isNewAttribute  #: `isNewAttribute` の別名。

    def isWritableNow(self, ancestors=True, children=True):
        u"""
        プラグの値が変更可能な状態にあるか。

        :param `bool` ancestors: 上位プラグもチェックするかどうか。
        :param `bool` children: 下位プラグもチェックするかどうか。
        :rtype: `bool`
        """
        return (
            self.mfn().writable and
            not self._CyObject__data['mplug'].isFreeToChange(
                checkAncestors=ancestors, checkChildren=children)
        )

    isSettable = isWritableNow  #: `isWritableNow` の別名。

    def isFreeToChange(self, ancestors=True, children=True):
        u"""
        プラグの値が変更可能な状態にあるかどうか検査する。

        戻り値の意味は以下の通り。

        - 0 ... 変更可能。
        - 1 ... そのプラグが変更不可。
        - 2 ... 下位プラグが変更不可（children=True 指定時のみチェック）。

        children=True を指定した場合にのみ

        :param `bool` ancestors: 上位プラグもチェックするかどうか。
        :param `bool` children: 下位プラグもチェックするかどうか。
        :rtype: `int`

        .. warning::
          戻り値 `bool` として評価しないこと。
          戻り値は `enum` であり、 0 は変更可能である。

          静的な writable フラグはチェックされないため、
          そもそもこのアトリビュートが変更不可であっても 0 が返される点も注意。

          静的な状態も考慮する場合は `isWritableNow` メソッドが利用できる。
        """
        return self.mplug().isFreeToChange(checkAncestors=ancestors, checkChildren=children)

    def isNodeFromReferencedFile(self):
        u"""
        ノードがリファレンスファイルのものかどうか。

        :rtype: `bool`
        """
        self.checkValid()
        return self._CyObject__data['noderef']._CyObject__data['mfn'].isFromReferencedFile

    def isAttrFromReferencedFile(self):
        u"""
        アトリビュートがリファレンスファイルのものかどうか。

        ノードがリファレンスファイルのものであっても、
        その上に追加されたアトリビュートなら False となる。

        `isNewAttribute` の逆の結果が得られる。

        :rtype: `bool`
        """
        self.checkValid()
        # isNodeFromReferencedFile をチェックする必要はない。
        return not self._CyObject__data['noderef']._CyObject__data['mfn'].isNewAttribute(
            self._CyObject__data['mplug'].attribute())

    def isFromReferencedFile(self, ancestors=False, children=False):
        u"""
        リファレンスファイルで作られた入力コネクションを持つかどうか。

        :param `bool` ancestors: 上位プラグもチェックするかどうか。
        :param `bool` children: 下位プラグもチェックするかどうか。
        :rtype: `bool`

        .. note::
            アトリビュートそのものがリファレンスファイル由来のものかどうかを
            チェックするには `isAttrFromReferencedFile` が利用できる。
        """
        return _mplugHierCheck(self.mplug(), 'isFromReferencedFile', ancestors, children)

    def isConnected(self, ancestors=False, children=False):
        u"""
        入力か出力のコネクションを持つかどうか。

        :param `bool` ancestors: 上位プラグもチェックするかどうか。
        :param `bool` children: 下位プラグもチェックするかどうか。
        :rtype: `bool`
        """
        return _mplugHierCheck(self.mplug(), 'isConnected', ancestors, children)

    def isDestination(self, ancestors=False, children=False):
        u"""
        入力コネクションを持つかどうか。

        :param `bool` ancestors: 上位プラグもチェックするかどうか。
        :param `bool` children: 下位プラグもチェックするかどうか。
        :rtype: `bool`
        """
        return _mplugHierCheck(self.mplug(), 'isDestination', ancestors, children)

    def isSource(self, ancestors=False, children=False):
        u"""
        出力コネクションを持つかどうか。

        :param `bool` ancestors: 上位プラグもチェックするかどうか。
        :param `bool` children: 下位プラグもチェックするかどうか。
        :rtype: `bool`
        """
        return _mplugHierCheck(self.mplug(), 'isSource', ancestors, children)

    def isLocked(self, ancestors=True, children=False):
        u"""
        ロックされているかどうか。

        :param `bool` ancestors: 上位プラグもチェックするかどうか。
        :param `bool` children: 下位プラグもチェックするかどうか。
        :rtype: `bool` or `int`

        .. warning::
            デフォルトは ancestors=True であるため、
            上位プラグがロックされていればロック扱いとなる。

            また、仮に False を指定したとしても、
            Maya の API の制限により、
            厳密なチェックはできない場合が多くある。
            そのため、上位でロックされているものの、
            そのプラグそのものがロックされているかどうか不明な場合は
            True ではなく 1 が返される。
        """
        # getAttr や MPlug.isLocked では親の影響を除外出来ない為、まず、自身＋子以下を調べる。
        # 親もチェックするモードであったか、結果が False であれば、結果そのままを返すだけ。
        mplug = self.mplug()
        res = _mplugHierCheck(mplug, 'isLocked', False, children)
        if ancestors or not res:
            return bool(res)  # 念の為 bool 型を保証。

        # そのプラグ以下が変更可能であるならば、少なくともそれ以下はロックされていない。
        if not mplug.isFreeToChange(checkAncestors=False, checkChildren=children):  # kFreeToChange
            return False

        # そのプラグが変更不可な場合、どの階層でロックされたものか判別が必要。
        if mplug.isChild:
            # 直接の親が False なら True で間違いない。
            if not mplug.parent().isLocked:
                return True
        elif mplug.isElement:
            # 直接の親が False なら True で間違いない。
            if not mplug.array().isLocked:
                return True
        else:
            # トップレベルのプラグであるなら True で間違いない。
            return True
        # そのプラグで直接ロックされているかどうかは定かではないが、これが限界。
        return 1

    def shortName(self):
        u"""
        アトリビュートのショート名を得る。

        :rtype: `str`
        """
        return self._CyObject__data['typeinfo']['shortname']

    def longName(self):
        u"""
        アトリビュートのロング名を得る。

        :rtype: `str`
        """
        return self.mfn().name

    def attrName(self):
        u"""
        ノード名を含まずに、ドットから始まるプラグ名を得る。

        プラグを特定する最短の名前からノード名を除去したものである。

        `shortName` との違いは、
        マルチ要素のインデックスが含まれることと、
        それによるコンパウンド階層が含まれる場合もあることである。

        :rtype: `str`
        """
        return self._CyObject__data['attrname']

    def plugName(self, short=False, fullAttrPath=False):
        u"""
        プラグ名を得る。

        :param `bool` short:
            アトリビュート名をショート名で得るかどうか。
        :param `bool` fullAttrPath:
            コンパウンドアトリビュート階層をフルパスで得るかどうか。
        :rtype: `str`
        """
        return self._CyObject__data['noderef'].name() + '.' + self._CyObject__data['mplug'].partialName(
            includeNonMandatoryIndices=True,  # isIndexMatters=False の場合にもインデックスを含ませる。
            includeInstancedIndices=True,  # worldSpace=True の場合にもインデックスを含ませる。
            useFullAttributePath=fullAttrPath, useLongNames=not short)

    def niceName(self, noWorldIndex=False):
        u"""
        ナイス名を得る。

        :rtype: `str`
        """
        if self.mplug().isArray:
            return _attributeName(self._CyObject__data['getname'](), n=True).split('[')[0]
        return _attributeName(self._CyObject__data['getname'](), n=True)

    def alias(self):
        u"""
        別名を得る。

        :rtype: `str`
        """
        self.checkValid()
        return self._CyObject__data['noderef']._CyObject__data['mfn'].plugsAlias(self._CyObject__data['mplug'])

    def plug(self, name):
        u"""
        下位のプラグを得る。

        Python属性としても同じように取得できるが、
        Pythonの名前と衝突する場合のためにこのメソッドがある。

        :param `str` name: アトリビュート名。
        :rtype: `.Plug`
        """
        self.checkValid()
        return self.__getInferiorPlug(name)

    def plug_(self, name):
        u"""
        `~.CyObject.checkValid` を省略して、下位のプラグを得る。

        Python属性としても同じように取得できるが、
        Pythonの名前と衝突する場合のためにこのメソッドがある。

        :param `str` name: アトリビュート名。
        :rtype: `.Plug`
        """
        return self.__getInferiorPlug(name)

    def __getInferiorPlug(self, name):
        u"""
        下位のプラグを得る共通ルーチン。
        """
        thisMPlug = self._CyObject__data['mplug']
        if not thisMPlug.isCompound:
            raise TypeError('plug is not a compound: ' + self.name_())

        noderef = self._CyObject__data['noderef']
        mfnnode = noderef._CyObject__data['mfn']
        mattr = _findMAttrToGetInferiorPlug(mfnnode, name, self)  # Maya2025以降でないと下位とは限らない。
        if mattr.isNull():
            raise AttributeError('no inferior attribute exists: %s.%s' % (self.name_(), name))

        # これ自身がマルチでなければ、子を直接得てみる。
        # マルチ（インデックスが未解決）の場合は、そのまま子に下ると不具合が生じる。
        if not thisMPlug.isArray:
            try:
                mplug = thisMPlug.child(mattr)
            except RuntimeError:
                pass
            else:
                # 子が得られない場合、エラーではなく同じ MPlug になるようだ。
                if mplug != thisMPlug:
                    return _newNodeRefPlug(_type(self), noderef, mplug, typename=self._CyObject__data['typeinfo'].get('subtype'))

        # ノードから得る。
        mplug = mfnnode.findPlug(mattr, False)

        # 上位にマルチ要素が在る場合、このプラグにインデックスを合わせる。これで階層チェックも兼ねる。
        idxAttrs = self.__elementIndexAttrs()
        if idxAttrs:
            try:
                for ia in self.__elementIndexAttrs():
                    mplug.selectAncestorLogicalIndex(*ia)
            except:
                raise AttributeError('no inferior attribute exists: %s.%s' % (self.name_(), name))

        # 上位にマルチ要素が無い場合、Maya2025以降でないなら、アトリビュートが下位のものかチェックする。
        elif not IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES and not _isAncestorAttrOf(thisMPlug.attribute(), mattr):
            raise AttributeError('no inferior attribute exists: %s.%s' % (self.name_(), name))

        return _newNodeRefPlug(_type(self), noderef, mplug)

    def __elementIndexAttrs(self):
        u"""
        上位のインデックス情報を得る。一度得たものはキャッシュされる。

        :rtype: `list`
        """
        info = self._CyObject__data['elemIdxAttrs']
        if info is None:
            mplug = self._CyObject__data['mplug']
            if mplug.isElement:
                info = [(mplug.logicalIndex(), mplug.attribute())]
                mplug = mplug.array()
            else:
                info = []
            while mplug.isChild:
                mplug = mplug.parent()
                if mplug.isElement:
                    info.append((mplug.logicalIndex(), mplug.attribute()))
                    mplug = mplug.array()
            self._CyObject__data['elemIdxAttrs'] = info
        return info

    def root(self, completely=False):
        u"""
        コンパウンドのルートプラグを得る。

        :param `bool` completely:
            ルートがマルチ要素プラグの場合は、そこからさらにマルチプラグを得る。
        :rtype: `.Plug`
        """
        mplug = self.mplug()
        mp = mplug
        typeinfo = None

        if completely:
            if mp.isElement:
                mp = mp.array()
            while mp.isChild:
                mp = mp.parent()
                if mp.isElement:
                    mp = mp.array()
            if mp is mplug:
                return self

            if mp == mplug:
                typeinfo = self._CyObject__data['typeinfo']

        else:
            c = mp.array() if mp.isElement else mp
            while c.isChild:
                mp = c.parent()
                c = mp.array() if mp.isElement else mp
            if mp is mplug:
                return self

        return _newNodeRefPlug(_type(self), self._CyObject__data['noderef'], mp, typeinfo)

    def parent(self):
        u"""
        親のコンパウンドアトリビュートを得る。

        :rtype: `.Plug`
        """
        self.checkValid()
        try:
            return _newNodeRefPlug(_type(self), self._CyObject__data['noderef'], self._CyObject__data['mplug'].parent())
        except:
            raise TypeError('plug is not a child: ' + self.name_())

    def numChildren(self):
        u"""
        コンパウンドアトリビュートの子の数を得る。

        :rtype: `int`
        """
        self.checkValid()
        try:
            return self._CyObject__data['mplug'].numChildren()
        except:
            raise TypeError('plug is not a compound: ' + self.name_())

    def child(self, idx):
        u"""
        コンパウンドアトリビュートの idx 番目の子を得る。

        :param `int` idx: 得たい子のインデックス
        :rtype: `.Plug`
        """
        # コンパウンドでなければエラー。
        self.checkValid()
        mplug = self._CyObject__data['mplug']
        if not mplug.isCompound:
            raise TypeError('plug is not a compound: ' + self.name_())

        # 下手するとクラッシュするので、インデックスをチェックする。
        if idx < 0 or mplug.numChildren() <= idx:
            raise IndexError('no child attribute exists: %s (%d)' % (self.name_(), idx))

        noderef = self._CyObject__data['noderef']

        # マルチアトリビュートのインデックスが未解決な場合は、そのまま子に下ると不具合が生じるためノードから得る。
        if mplug.isArray:
            mattr = self._CyObject__data['typeinfo']['mfn'].child(idx)
            mp = noderef._CyObject__data['mfn'].findPlug(mattr, False)
            # 上位にマルチ要素が在る場合、このプラグにインデックスを合わせる。
            for ia in self.__elementIndexAttrs():
                mp.selectAncestorLogicalIndex(*ia)

        # マルチアトリビュートでなければ子を直接得られる。
        else:
            mp = mplug.child(idx)

        return _newNodeRefPlug(_type(self), noderef, mp, typename=self._CyObject__data['typeinfo'].get('subtype'))

    def children(self):
        u"""
        コンパウンドアトリビュートの子のリストを得る。

        :rtype: `list`
        """
        # コンパウンドでなければエラー。
        mplug = self._CyObject__data['mplug']
        if not mplug.isCompound:
            raise TypeError('plug is not a compound: ' + self.name_())

        noderef = self._CyObject__data['noderef']

        # 子の MPlug を得るプロシージャを作成。
        if mplug.isArray:
            # マルチアトリビュートのインデックスが未解決な場合は、そのまま子に下ると不具合が生じるためノードから得る。
            childAttr = self._CyObject__data['typeinfo']['mfn'].child
            findPlug = noderef._CyObject__data['mfn'].findPlug
            idxAttrs = self.__elementIndexAttrs()

            def getChild(i):
                mattr = childAttr(i)
                mp = findPlug(mattr, False)
                # 上位にマルチ要素が在る場合、このプラグにインデックスを合わせる。
                for ia in idxAttrs:
                    mp.selectAncestorLogicalIndex(*ia)
                return mp

        else:
            # マルチアトリビュートでなければ子を直接得られる。
            getChild = mplug.child

        # 子プラグリストを得る。
        cls = _type(self)
        subtype = self._CyObject__data['typeinfo'].get('subtype')
        res = [
            _newNodeRefPlug(cls, noderef, getChild(i), typename=subtype)
            for i in range(mplug.numChildren())
        ]
        getChild = None
        return res

    def childNames(self, long=False):
        u"""
        コンパウンドアトリビュートの子アトリビュート名リストを得る。

        :param `bool` long: ロング名で得るかどうか。
        :rtype: `list`
        """
        self.checkValid()
        try:
            # mfn.numChildren() だと double3 などの場合に得られない。
            n = self._CyObject__data['mplug'].numChildren()
        except:
            raise TypeError('plug is not a compound: ' + self.name_())

        c_ = self._CyObject__data['typeinfo']['mfn'].child
        if long:
            return [_2_MFnAttribute(c_(i)).name for i in range(n)]
        else:
            return [_2_MFnAttribute(c_(i)).shortName for i in range(n)]

    def leaves(self, evaluate=False):
        u"""
        マルチやコンパウンドの階層を下って、リーフのプラグのリストを得る。

        :param `bool` evaluate:
            未評価のマルチ要素プラグを取りこぼさないように、
            マルチプラグを評価する。
        :rtype: `list`
        """
        self.checkValid()

        def finder(mplug):
            if mplug.isArray:
                for i in range(getattr(mplug, numElemName)()):
                    finder(nonNetworkedElemMPlug(mplug, mplug.elementByPhysicalIndex(i)))
            elif mplug.isCompound:
                for i in range(mplug.numChildren()):
                    finder(mplug.child(i))
            else:
                append(mplug)

        leaves = []
        append = leaves.append
        numElemName = 'evaluateNumElements' if evaluate else 'numElements'
        finder(self._CyObject__data['mplug'])

        if len(leaves) == 1:
            return [self]

        cls = _type(self)
        noderef = self._CyObject__data['noderef']
        leaves = [_newNodeRefPlug(cls, noderef, x) for x in leaves]
        return leaves

    def array(self):
        u"""
        要素からマルチアトリビュートを得る。

        :rtype: `.Plug`
        """
        self.checkValid()
        try:
            return _newNodeRefPlug(_type(self), self._CyObject__data['noderef'], self._CyObject__data['mplug'].array(), self._CyObject__data['typeinfo'])
        except:
            raise TypeError('plug is not an element: ' + self.name_())

    multi = array  #: `array` の別名。

    def isNotInstanced(self):
        u"""
        解決されていないマルチアトリビュート要素が含まれているかどうか。

        要素化されていなかったり -1 の要素が含まれている場合に True となる。

        :rtype: `bool`
        """
        if self.mplug().isArray:
            return True
        for x in self.__elementIndexAttrs():
            if x[0] < 0:
                return True
        return False

    def isValidWorldElement(self):
        u"""
        `isWorldSpace` な要素プラグの場合にインデックスがDAGノードのインスタンス番号と矛盾が無いかどうか。

        そもそも `isWorldSpace` でなかったり、要素プラグでない場合や
        未解決なインデックス要素(-1)の場合にも True が返される。

        :rtype: `bool`
        """
        if not self.mfn().worldSpace:
            return True

        mp = self._CyObject__data['mplug']
        c = mp.array() if mp.isElement else mp
        while c.isChild:
            mp = c.parent()
            c = mp.array() if mp.isElement else mp

        if not mp.isElement:
            return True
        i = mp.logicalIndex()
        return i < 0 or i == self._CyObject__data['noderef']._CyObject__data['mpath'].instanceNumber()

    def worldElement(self):
        u"""
        `isWorldSpace` なプラグの適切な要素を得る。

        自身がマルチでなく、その要素プラグやコンパウンドの子プラグの場合は
        補正されたものが得られる。

        `isWorldSpace` でない場合や、既に適切な要素な場合は、自身が得られる。

        :rtype: `.Plug`
        """
        if not self.mfn().worldSpace:
            return self

        mplug = self._CyObject__data['mplug']
        root = mplug

        isElem = root.isElement
        c = root.array() if isElem else root
        while c.isChild:
            root = c.parent()
            isElem = root.isElement
            c = root.array() if isElem else root

        idx = self._CyObject__data['noderef']._CyObject__data['mpath'].instanceNumber()
        if isElem and root.logicalIndex() == idx:
            # インデックスが正しいなら、自身をそのまま返す。
            return self

        if mplug is root:
            mplug = _2_MPlug(mplug)
            mplug.selectAncestorLogicalIndex(idx)
        else:
            mplug = _2_MPlug(mplug)
            mplug.selectAncestorLogicalIndex(idx, root.attribute())

        return _newNodeRefPlug(_type(self), self._CyObject__data['noderef'], mplug, self._CyObject__data['typeinfo'])

    def numElements(self):
        u"""
        マルチアトリビュートの評価済みの要素数を得る。

        この数に基づいて要素を得るには `element` を利用できる。

        :rtype: `int`

        .. warning::
            コネクトされていても未評価のプラグはカウントされない点に注意。

            評価を保証したい場合は `evaluateNumElements` を使用すること。
            `evaluateNumElements` を呼び出した後は、このメソッドも同じ値を
            返すようになり、これに依存した操作も期待通り動作する。
        """
        self.checkValid()
        return self._CyObject__data['mplug'].numElements()

    def numConnectedElements(self):
        u"""
        マルチアトリビュートの接続を持つ要素数を得る。

        この数に基づいて要素を得るには `connectedElement` を利用できる。

        :rtype: `int`

        .. note::
            接続数を得たい場合に最も確実なメソッドである。
            `numElements` や `evaluateNumElements` ではアクセス出来ない
            場合がある出力のみのプラグもカウントされる。
        """
        self.checkValid()
        return self._CyObject__data['mplug'].numConnectedElements()

    def evaluateNumElements(self):
        u"""
        マルチアトリビュートを評価した上で要素数を得る。

        :rtype: `int`

        .. warning::
            このメソッドは `numElements` より効率が悪いと思われるが、
            `numElements` よりも信頼性がある。
            なお、このメソッドを呼び出した後は `numElements` も同じ値を
            返すようになる。

            ただし、出力コネクションのプラグはこれでもカウントされない場合がある。
            コネクトされた要素数を知りたい場合は `numConnectedElements`
            を利用すること。
        """
        self.checkValid()
        return self._CyObject__data['mplug'].evaluateNumElements()

    def element(self, idx):
        u"""
        マルチアトリビュートの要素を物理インデックスで得る。

        論理インデックスの並びは昇順となる。

        :param `int` idx: 得たい要素の物理インデックス
        :rtype: `.Plug`
        """
        self.checkValid()
        mplug = self._CyObject__data['mplug']
        if not mplug.isArray:
            raise TypeError('plug is not an array: ' + self.name_())
        return _newNodeRefPlug(
            _type(self),
            self._CyObject__data['noderef'],
            nonNetworkedElemMPlug(mplug, mplug.elementByPhysicalIndex(idx)),
            self._CyObject__data['typeinfo'])

    def elements(self):
        u"""
        マルチアトリビュートの要素のリストを得る。

        論理インデックスの並びは昇順となる。

        :rtype: `list`
        """
        self.checkValid()
        mplug = self._CyObject__data['mplug']
        if not mplug.isArray:
            raise TypeError('plug is not an array: ' + self.name_())
        cls = _type(self)
        noderef = self._CyObject__data['noderef']
        info = self._CyObject__data['typeinfo']
        getElem = mplug.elementByPhysicalIndex
        return [
            _newNodeRefPlug(cls, noderef, nonNetworkedElemMPlug(mplug, getElem(i)), info)
            for i in range(mplug.numElements())
        ]

    def connectedElement(self, idx):
        u"""
        マルチアトリビュートのコネクトされている要素を物理インデックスで得る。

        論理インデックスの並びは必ずしも昇順とはならない。
        （接続操作の後は乱れており、シーンを開き直すと整列される）

        :param `int` idx:
            0 ～ `numConnectedElements` ()-1 の範囲の物理インデックス。
        :rtype: `.Plug`
        """
        self.checkValid()
        mplug = self._CyObject__data['mplug']
        if not mplug.isArray:
            raise TypeError('plug is not an array: ' + self.name_())
        return _newNodeRefPlug(
            _type(self),
            self._CyObject__data['noderef'],
            toNonNetworkedElemMPlug(mplug, mplug.connectionByPhysicalIndex(idx)),
            self._CyObject__data['typeinfo'])

    def connectedElements(self):
        u"""
        マルチアトリビュートのコネクトされている要素のリストを得る。

        論理インデックスの並びは必ずしも昇順とはならない。
        （接続操作の後は乱れており、シーンを開き直すと整列される）

        :rtype: `list`
        """
        self.checkValid()
        mplug = self._CyObject__data['mplug']
        if not mplug.isArray:
            raise TypeError('plug is not an array: ' + self.name_())
        cls = _type(self)
        noderef = self._CyObject__data['noderef']
        info = self._CyObject__data['typeinfo']
        getConElem = mplug.connectionByPhysicalIndex
        return [
            _newNodeRefPlug(cls, noderef, toNonNetworkedElemMPlug(mplug, getConElem(i)), info)
            for i in range(mplug.numElements())
        ]

    def index(self):
        u"""
        マルチアトリビュートの要素の論理インデックスを得る。

        :rtype: `int`
        """
        self.checkValid()
        try:
            return self._CyObject__data['mplug'].logicalIndex()
        except:
            raise TypeError('plug is not an element: ' + self.name_())

    def indices(self):
        u"""
        マルチアトリビュートの論理インデックスのリストを得る。

        論理インデックスの並びは昇順となる。

        :rtype: `list`
        """
        self.checkValid()
        try:
            return list(self._CyObject__data['mplug'].getExistingArrayAttributeIndices())
        except:
            raise TypeError('plug is not an array: ' + self.name_())

    def elementExists(self, idx=None):
        u"""
        マルチアトリビュートの要素が存在しているかどうか。

        :param `int` idx:
            自身がマルチのとき、調べるインデックスを指定する。
            自身が要素（実在は不明）のときは省略する。
        :rtype: `bool`
        """
        mplug = self.mplug()
        if idx is None:
            if mplug.isElement:
                return mplug.logicalIndex() in mplug.array().getExistingArrayAttributeIndices()
            raise TypeError('plug is not an element: ' + self.name_())
        else:
            if mplug.isArray: 
                return idx in mplug.getExistingArrayAttributeIndices()
            raise TypeError('plug is not an array: ' + self.name_())

    def affectedAttrs(self, worldSpace=False, pcls=None):
        u"""
        このプラグが同一ノード内で影響を与えるプラグのリストを得る。

        逆に、影響元を得る場合は `affectingAttrs` が利用できる。

        また、このメソッドは実際のプラグからプラグを得られるが、
        実際のノードやプラグではなくノードタイプとアトリビュート名から調べるには
        ユーティリティ関数 `.affectedAttrNames` が利用できる。

        :param `bool` worldSpace:
            ワールドスペースアトリビュートの依存関係も確実に得るかどうか。

            デフォルトの False だと、
            例えば :mayanode:`transform` ノードの
            translate が影響を与えるアトリビュートとして
            matrix は得られるが worldMatrix は得ることができない。
        :rtype: `list`
        """
        self.checkValid()
        noderef = self._CyObject__data['noderef']
        mfnnode = self._CyObject__data['noderef']._CyObject__data['mfn']
        mattr = self._CyObject__data['mplug'].attribute()
        mattrs = [x for x in mfnnode.getAffectedAttributes(mattr) if x != mattr]

        if worldSpace and self.mfn_().affectsWorldSpace:
            mfn_attr = mfnnode.attribute
            allAttrs = [mfn_attr(i) for i in range(mfnnode.attributeCount())]
            mattrs.extend([
                x for x in allAttrs
                if _2_MFnAttribute(x).worldSpace and x not in mattrs
            ])

        pcls = pcls or _type(self)
        findPlug = mfnnode.findPlug
        return [_newNodeRefPlug(pcls, noderef, findPlug(x, False)) for x in mattrs]

    def affectingAttrs(self, worldSpace=False, pcls=None):
        u"""
        このプラグが同一ノード内で影響を受けるプラグのリストを得る。

        逆に、影響先を得る場合は `affectedAttrs` が利用できる。

        また、このメソッドは実際のプラグからプラグを得られるが、
        実際のノードやプラグではなくノードタイプとアトリビュート名から調べるには
        ユーティリティ関数 `.affectingAttrNames` が利用できる。

        :param `bool` worldSpace:
            ワールドスペースアトリビュートの依存関係も確実に得るかどうか。

            デフォルトの False だと、
            例えば :mayanode:`transform` ノードの
            worldMatrix が影響を受けるアトリビュートとして
            translate 等を得ることはできない。
        :rtype: `list`
        """
        self.checkValid()
        noderef = self._CyObject__data['noderef']
        mfnnode = self._CyObject__data['noderef']._CyObject__data['mfn']
        mattr = self._CyObject__data['mplug'].attribute()
        mattrs = [x for x in mfnnode.getAffectingAttributes(mattr) if x != mattr]

        if worldSpace and self.mfn_().worldSpace:
            mfn_attr = mfnnode.attribute
            allAttrs = [mfn_attr(i) for i in range(mfnnode.attributeCount())]
            mattrs.extend([
                x for x in allAttrs
                if _2_MFnAttribute(x).affectsWorldSpace and x not in mattrs
            ])

        pcls = pcls or _type(self)
        findPlug = mfnnode.findPlug
        return [_newNodeRefPlug(pcls, noderef, findPlug(x, False)) for x in mattrs]

    def hasMin(self):
        u"""
        最小値を持っているかどうか。

        :rtype: `bool`
        """
        return (
            self._CyObject__data['typeinfo']['typename'] == 'enum' or 
            self.__getFromMFn('hasMin') or False
        )

    def hasMax(self):
        u"""
        最大値を持っているかどうか。

        :rtype: `bool`
        """
        return (
            self._CyObject__data['typeinfo']['typename'] == 'enum' or 
            self.__getFromMFn('hasMax') or False
        )

    def hasSoftMin(self):
        u"""
        ソフト最小値を持っているかどうか。

        :rtype: `bool`
        """
        return self.__getFromMFn('hasSoftMin') or False

    def hasSoftMax(self):
        u"""
        ソフト最大値を持っているかどうか。

        :rtype: `bool`
        """
        return self.__getFromMFn('hasSoftMax') or False

    def min(self):
        u"""
        アトリビュートに設定されている最小値を内部単位で得る。
        """
        v = self.__getFromMFn('getMin', 'hasMin')
        if v is not None:
            return unitAttrToRawValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def max(self):
        u"""
        アトリビュートに設定されている最大値を内部単位で得る。
        """
        v = self.__getFromMFn('getMax', 'hasMax')
        if v is not None:
            return unitAttrToRawValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def softMin(self):
        u"""
        アトリビュートに設定されているソフト最小値を内部単位で得る。
        """
        v = self.__getFromMFn('getSoftMin', 'hasSoftMin')
        if v is not None:
            return unitAttrToRawValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def softMax(self):
        u"""
        アトリビュートに設定されているソフト最大値を内部単位で得る。
        """
        v = self.__getFromMFn('getSoftMax', 'hasSoftMax')
        if v is not None:
            return unitAttrToRawValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def minu(self):
        u"""
        アトリビュートに設定されている最小値をUI設定単位で得る。
        """
        v = self.__getFromMFn('getMin', 'hasMin')
        if v is not None:
            return unitAttrToUnitValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def maxu(self):
        u"""
        アトリビュートに設定されている最大値をUI設定単位で得る。
        """
        v = self.__getFromMFn('getMax', 'hasMax')
        if v is not None:
            return unitAttrToUnitValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def softMinu(self):
        u"""
        アトリビュートに設定されているソフト最小値をUI設定単位で得る。
        """
        v = self.__getFromMFn('getSoftMin', 'hasSoftMin')
        if v is not None:
            return unitAttrToUnitValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def softMaxu(self):
        u"""
        アトリビュートに設定されているソフト最大値をUI設定単位で得る。
        """
        v = self.__getFromMFn('getSoftMax', 'hasSoftMax')
        if v is not None:
            return unitAttrToUnitValue(v, self._CyObject__data['typeinfo']['unittype'], True)

    def __getFromMFn(self, method, checker=None):
        subType = self.subType()  # これで fixUnitTypeInfo もされる。
        mfn = self._CyObject__data['typeinfo']['mfn']
        if subType:
            cls = _2_MFnUnitAttribute if subType in _UNIT_ATTRTYPE_SET else _2_MFnNumericAttribute
            mfn_child = mfn.child
            return [
                _getFrom(cls(mfn_child(i)), method, checker)
                for i in range(self._CyObject__data['mplug'].numChildren())
            ]
        else:
            return _getFrom(mfn, method, checker)

    def default(self):
        u"""
        デフォルト値を内部単位で得る。
        """
        try:
            v = self.mfn().default
        except:
            return
        if v is not None:
            return attrToRawValue(v, self._CyObject__data['typeinfo']['typename'])

    def defaultu(self):
        u"""
        デフォルト値をUI設定単位で得る。
        """
        try:
            v = self.mfn().default
        except:
            return
        if v is not None:
            fixUnitTypeInfo(self._CyObject__data['typeinfo'])
            return attrToUnitValue(v, self._CyObject__data['typeinfo']['unittype'])

    def evaluate(self):
        u"""
        このプラグを評価する。

        .. note::
            これによって、起こる変化の undo はできないことに注意。
            たとえば、マルチアトリビュートの要素を評価することで
            要素が追加されても undo できない。
            それをやりたい場合は `.Plug.addElement` が利用できる。
        """
        self.checkValid()
        try:
            self._CyObject__data['mplug'].asMObject()
        except:
            pass

    def evaluator(self):
        u"""
        呼び出すとプラグを評価できる関数を得る。

        `evaluate` そのものが得られるとも言えるが、
        自身への参照を保持していない点で異なる。

        :rtype: `callable`
        """
        self.checkValid()
        mplug = self._CyObject__data['mplug']

        def proc():
            try:
                #print('eval: ' + mplug.info)
                mplug.asMObject()
            except:
                pass
        return proc

    def __fixedMPlug(self):
        u"""
        worldSpaceでインデックスが未確定の場合にインスタンスに合わせた MPlug を得る。

        DAGノードのインスタンス番号は動的に変わるので、キャッシュはされない。
        `~.CyObject.checkValid` は呼び出し側で保証すること。
        """
        if not self._CyObject__data['typeinfo']['mfn'].worldSpace:
            return self._CyObject__data['mplug']

        mplug = self._CyObject__data['mplug']
        if mplug.isArray:
            if not mplug.isChild:
                # 最上位のプラグで isArray なら、現在のインスタンス番号の要素を得る。
                mplug = _2_MPlug(mplug)
                mplug.selectAncestorLogicalIndex(self._CyObject__data['noderef']._CyObject__data['mpath'].instanceNumber())
                return mplug
            root = mplug.parent()
        else:
            root = mplug

        c = root.array() if root.isElement else root
        while c.isChild:
            root = c.parent()
            c = root.array() if root.isElement else root

        if root.logicalIndex() < 0:
            # 最上位のインデックスが未確定なら、現在のインスタンス番号に合わせた要素を得る。
            if mplug is root:
                mplug = _2_MPlug(mplug)
                mplug.selectAncestorLogicalIndex(self._CyObject__data['noderef']._CyObject__data['mpath'].instanceNumber())
            else:
                mplug = _2_MPlug(mplug)
                mplug.selectAncestorLogicalIndex(self._CyObject__data['noderef']._CyObject__data['mpath'].instanceNumber(), root.attribute())
        return mplug

    def get(self):
        u"""
        アトリビュート値を内部単位で得る。

        MEL の場合と同様に、 `isWorldSpace` なアトリビュートで
        要素を指定していない場合は自動的に補完される。

        :returns: アトリビュート値。
        """
        self.checkValid()
        # どのみち一般 compound の数値型は通常手段では得られないので unittype ではなく typename としている。
        return mplugGetRawValue(self.__fixedMPlug(), self._CyObject__data['typeinfo']['typename'])

    def getu(self):
        u"""
        アトリビュート値をUI設定単位で得る。

        MEL の場合と同様に、 `isWorldSpace` なアトリビュートで
        要素を指定していない場合は自動的に補完される。

        :returns: アトリビュート値。
        """
        self.checkValid()
        fixUnitTypeInfo(self._CyObject__data['typeinfo'])
        return mplugGetUnitValue(self.__fixedMPlug(), self._CyObject__data['typeinfo']['unittype'])

    def getM(self):
        u"""
        matrix 型アトリビュートから matrix 値を得る。

        データ型 matrix アトリビュートは、
        マトリックスだけでなく
        トランスフォーメーション情報形式での値の保存が可能で、
        `get` メソッドでは、保持されている値の形式に応じて
        `.Matrix` か `.Transformation` が得られる。

        一方、こちらのメソッドを使用すると、
        保持されている値の形式にかかわらず、常に
        `.Matrix` で得ることができる。

        :rtype: `.Matrix` or None
        """
        self.checkValid()
        return mplug_get_matrix(self.__fixedMPlug())

    def getEnumName(self):
        u"""
        enum 型アトリビュートから現在の値の名前を得る。
        """
        return self.mfn().fieldName(self._CyObject__data['mplug'].asShort())

    def enumName(self, val):
        u"""
        enum アトリビュートの値から名前を得る。

        :param `int` val: enum値。
        :rtype: `str`
        """
        return self.mfn().fieldName(val)

    def enumValue(self, key):
        u"""
        enum アトリビュートの名前から値を得る。

        :param `str` key: enum名。
        :rtype: `int`
        """
        return self.mfn().fieldValue(key)

    def hasTransformation(self):
        u"""
        matrix 型アトリビュートが `.Transformation` 値を持つかどうか。

        :rtype: `bool`
        """
        if self._CyObject__data['typeinfo']['typename'] == 'matrix':
            self.checkValid()
            try:
                return _2_MFnMatrixData(self.__fixedMPlug().asMObject()).isTransformation()
            except:
                return False
        return False

    def connections(
        self,
        s=True, d=True, c=False, t=None, et=False, scn=False,
        source=True, destination=True, connections=False,
        type=None, exactType=False, skipConversionNodes=False,
        asPair=False, asNode=False, checkChildren=True,
        checkElements=True, index=None, pcls=None,
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
            :mayanode:`unitConversion` 系ノードをスキップするかどうか。
        :param `bool` asNode:
            コネクト先をプラグではなくノードで得る。
        :param `bool` checkChildren:
            コンパウンドの下層もチェックする。
            デフォルトで True なので False を明示すると無効化できる。
        :param `bool` checkElements:
            マルチプラグの要素もチェックする。
            デフォルトで True なので False を明示すると無効化できる。
        :param `int` index:
            結果を1つだけ得る場合にインデックスを指定する。
            負数も指定可能。
            結果は `list` ではなく単一となる（得られない場合は None ）。
            範囲外を指定してもエラーにはならず None となる。
        :param pcls:
            得たいプラグオブジェクトのクラス。
            省略時はこのオブジェクト自身と同じクラスになる。
        :rtype: `list`
        """
        # worldSpaceでインデックスが未確定の場合はインスタンスに合わせた MPlug を得る。
        self.checkValid()
        mplug = self.__fixedMPlug()
        if mplug is self._CyObject__data['mplug']:
            # 上位に未解決なインデックスがある場合は、コネクションは得られないものとする。
            if '[-1]' in self._CyObject__data['attrname']:
                return [] if index is None else None
            fromPlug = self
        else:
            fromPlug = None

        source &= s
        destination &= d
        asPair |= c
        asPair |= connections
        type = type or t
        exactType |= et
        getConn = getConnWithoutUC if skipConversionNodes or scn else _2_MPlug_connectedTo

        # 再帰的にコネクションを探す処理。
        def search(mplug, fromPlug=None):
            isCompound = checkChildren and mplug.isCompound

            # このプラグのコネクションを得る。
            marr = getConn(mplug, source, destination)
            if marr:
                addMPlugs0(marr, fromPlug, mplug)

            # マルチプラグなら要素プラグのコネクションを得る。
            if checkElements and mplug.isArray:
                # コネクションでは必ずしも論理インデックスの昇順とは限らないので、ここではソートする。
                getConElem = mplug.connectionByPhysicalIndex
                mps = [getConElem(i) for i in range(mplug.numConnectedElements())]
                mps.sort(key=_2_MPlug_logicalIndex)
                for mp in mps:
                    marr = getConn(mp, source, destination)
                    if marr:
                        addMPlugs1(marr, mplug, mp)

                    # コンパウンドの子もチェックする場合、子プラグを再帰呼び出しする。
                    if isCompound:
                        getChild = mp.child
                        for i in range(mp.numChildren()):
                            search(getChild(i))

            # コンパウンドの子もチェックする場合、子プラグを再帰呼び出しする。
            elif isCompound:
                getChild = mplug.child
                for i in range(mplug.numChildren()):
                    search(getChild(i))

        # 得られたコネクト先を一旦保持するための処理。
        # このメソッドの途中であっても Networked のまま保持するのは危険であるため、
        # 即 Non-Networked 化するか Node を得るための情報に変換しておく。
        if asNode:
            toKeep = _node4ArgsByMPlug
        else:
            toKeep = toNonNetworkedMPlug

        # 得られたコネクションを results に追加する処理。
        if asPair:
            def addMPlugs0(marr, fromPlug, fromMPlug):
                base = fromPlug or nonNetworkedMPlug(fromMPlug)  # Networked とは限らないので判定付き。
                results.extend([(base, toKeep(x)) for x in marr])

            def addMPlugs1(marr, multi, elem):
                base = toNonNetworkedElemMPlug(multi, elem)
                results.extend([(base, toKeep(x)) for x in marr])
        else:
            def addMPlugs0(marr, *args):
                results.extend([toKeep(x) for x in marr])
            addMPlugs1 = addMPlugs0

        # コネクションを収集。
        results = []
        search(mplug, fromPlug)

        search = None
        addMPlugs0 = None
        addMPlugs1 = None

        # 得た結果を共通ルーチンで加工して返す。
        if not pcls:
            pcls = (asPair or not asNode) and _type(self)
        return _evalConnList(self, results, not asNode and pcls, asPair and pcls, index, type, exactType)

    def inputs(self, **kwargs):
        u"""
        上流のコネクションを得る。

        `connections` に s=True, d=False を指定することと同等であり、
        その他のオプションは全て指定可能。
        """
        return self.connections(True, False, **kwargs)

    def outputs(self, **kwargs):
        u"""
        下流のコネクションを得る。

        `connections` に s=False, d=True を指定することと同等であり、
        その他のオプションは全て指定可能。
        """
        return self.connections(False, True, **kwargs)

    def source(self, **kwargs):
        u"""
        unitConversionノードをスキップしつつ、入力しているプラグかノードを得る。

        `inputs` に以下のオプションを指定することと同等であり、
        その他のオプションは全て指定可能。

        - skipConversionNodes=True
        - checkChildren=False
        - checkElements=False
        - index=0

        :rtype: `.Plug`, `.Node`, or None
        """
        kwargs['skipConversionNodes'] = True
        kwargs['checkChildren'] = False
        kwargs['checkElements'] = False
        kwargs['index'] = 0
        return self.connections(True, False, **kwargs)

    def sourceWithConversion(self, **kwargs):
        u"""
        unitConversionノードをスキップせずに、入力しているプラグかノードを得る。

        `inputs` に以下のオプションを指定することと同等であり、
        その他のオプションは全て指定可能。

        - checkChildren=False
        - checkElements=False
        - index=0

        :rtype: `.Plug`, `.Node`, or None
        """
        kwargs['checkChildren'] = False
        kwargs['checkElements'] = False
        kwargs['index'] = 0
        return self.connections(True, False, **kwargs)

    def destinations(self, **kwargs):
        u"""
        unitConversionノードをスキップしつつ、出力先のプラグかノードのリストを得る。

        `outputs` に以下のオプションを指定することと同等であり、
        その他のオプションは全て指定可能。

        - skipConversionNodes=True
        - checkChildren=False
        - checkElements=False

        :rtype: `list`
        """
        kwargs['skipConversionNodes'] = True
        kwargs['checkChildren'] = False
        kwargs['checkElements'] = False
        return self.connections(False, True, **kwargs)

    def destinationsWithConversions(self, **kwargs):
        u"""
        unitConversionノードをスキップせずに、出力先のプラグかノードのリストを得る。

        `outputs` に以下のオプションを指定することと同等であり、
        その他のオプションは全て指定可能。

        - checkChildren=False
        - checkElements=False

        :rtype: `list`
        """
        kwargs['checkChildren'] = False
        kwargs['checkElements'] = False
        return self.connections(False, True, **kwargs)

    def isConnectedTo(self, dst):
        u"""
        このプラグから指定プラグへ向かう接続が在るかどうか検査する。

        :type dst: `.Plug`
        :param dst:
            接続を検査する下流プラグ。

            `isIndexMatters` が False のマルチプラグが指定された場合、
            各要素とのコネクションの有無もチェックされる。
        :rtype: `bool`
        """
        src = self.mplug()
        dst = dst.mplug()
        if dst.isArray:
            mfn = dst.mfn_()
            if not(mfn.indexMatters or mfn.readable):
                for i in range(dst.numConnectedElements()):
                    if _mplugInList(src, dst.connectionByPhysicalIndex(i).connectedTo(True, False)):
                        return True
                return False
        return _mplugInList(src, dst.connectedTo(True, False))

    def nextAvailable(self, start=-1, asPlug=False, checkLocked=True, checkChildren=True):
        u"""
        マルチプラグの入力の次の空きインデックスを得る。

        `isIndexMatters` 設定に限らず利用できる。

        :param `int` start:
            検索を開始するインデックス。
            デフォルトだと、最後のコネクションの次のインデックスからとなる。
            途中のインデックスも見つけるなら 0 などを指定する。
        :param `bool` asPlug: 結果を `Plug` で得る。
        :param `bool` checkLocked: ロックされたプラグをスキップする。
        :param `bool` checkChildren:
            コンパウンドの子やその中のマルチもチェックする。
        :rtype: `int` or `.Plug`
        """
        mplug = self.mplug()

        # start が指定されなかった場合、最後のコネクションの次のインデックスからチェックする。
        # ロックをチェックする必要がなければ、それで決定。
        if start < 0:
            n = mplug.numConnectedElements()
            idx = (mplug.connectionByPhysicalIndex(n - 1).logicalIndex() + 1) if n else 0
        else:
            idx = start

        # 空きプラグを探す。
        if start >= 0 or checkLocked:
            nPlugs = mplug.evaluateNumElements() if checkLocked else mplug.numConnectedElements()
            if nPlugs:
                # 条件に応じて、コネクションチェック関数を作成。
                if checkLocked:
                    getAt = mplug.elementByPhysicalIndex
                    checkOne = lambda mp: mp.isLocked or mp.isDestination
                else:
                    getAt = mplug.connectionByPhysicalIndex
                    checkOne = lambda mp: mp.isDestination
                if checkChildren:
                    def checker(mp):
                        if checkOne(mp):
                            return True
                        if mp.isArray:
                            mp_elem = elementByPhysicalIndex
                            for i in range(mp.evaluateNumElements()):
                                if checker(mp_elem(i)):
                                    return True
                        elif mp.isCompound:
                            mp_child = mp.child
                            for i in range(mp.numChildren()):
                                if checker(mp_child(i)):
                                    return True
                else:
                    checker = checkOne

                # プラグを順にチェック。
                for i in range(nPlugs):
                    mp = getAt(i)
                    if idx != mp.logicalIndex() or not checker(mp):
                        break
                    idx += 1

        # インデックスかプラグを返す。
        return _newNodeRefPlug(
            _type(self),
            self._CyObject__data['noderef'],
            _2_MPlug(mplug).selectAncestorLogicalIndex(idx),
            self._CyObject__data['typeinfo']
        ) if asPlug else idx

    if MAYA_VERSION >= (2016, 5):
        def isProxy(self):
            u"""
            プロキシアトリビュートかどうか。

            :rtype: `bool`
            """
            return self.mfn().isProxyAttribute

        def proxyMaster(self):
            u"""
            プロキシアトリビュートのマスタープラグを得る。

            プロキシでなければ自身が返され、
            マスターがコネクトされていないプロキシなら None が返される。

            :rtype: `.Plug`
            """
            if self.mfn().isProxyAttribute:
                src = self.connections(True, False)
                if src:
                    return src[0].proxyMaster()
            else:
                return self

        def hasProxy(self):
            u"""
            関連付けられたプロキシアトリビュートを持つかどうか。

            :rtype: `bool`
            """
            for mp in self.mplug().connectedTo(False, True):
                if _2_MFnAttribute(mp.attribute()).isProxyAttribute:
                    return True
            return False

        def getProxies(self):
            u"""
            関連付けられたプロキシアトリビュートを全て得る。

            :rtype: `list`
            """
            return [
                y for x in self.connections(False, True)
                if x.isProxy() for y in ([x] + x.getProxies())]

        def addProxy(self, name, node=None, **kwargs):
            u"""
            このプラグに対するプロキシアトリビュートを生成する。

            :param `str` name: アトリビュートのロング名。
            :type node: `.Node`
            :param node:
                アトリビュートを追加するノード。
                省略すると、このプラグのノードになる。
            :param kwargs:
                その他に `.Node.addAttr` のオプション引数を指定可能。
            :rtype: None or `.Plug`
            """
            return (node or self.node()).addAttr(name, proxy=self, **kwargs)

    else:
        def isProxy(self):
            u"""
            プロキシアトリビュートかどうか。

            :rtype: `bool`
            """
            return False

        def proxyMaster(self):
            u"""
            プロキシアトリビュートのマスタープラグを得る。

            プロキシでなければ自身が返され、
            マスターがコネクトされていないプロキシなら None が返される。

            :rtype: `.Plug`
            """
            return self

        def hasProxy(self):
            u"""
            関連付けられたプロキシアトリビュートを持つかどうか。

            :rtype: `bool`
            """
            return False

        def getProxies(self):
            u"""
            関連付けられたプロキシアトリビュートを全て得る。

            :rtype: `list`
            """
            return []

        def addProxy(self, name, node=None, **kwargs):
            u"""
            このプラグに対するプロキシアトリビュートを生成する。

            :param `str` name: アトリビュートのロング名。
            :type node: `.Node`
            :param node:
                アトリビュートを追加するノード。
                省略すると、このプラグのノードになる。
            :param kwargs:
                その他に `.Node.addAttr` のオプション引数を指定可能。
            :rtype: None or `.Plug`
            """
            raise RuntimeError('Proxy attributes is supported in Maya 2016.5 and later.')

    def apiSetLocked(self, val):
        u"""
        undoに対応せずにプラグのロック状態をセットする。

        :param `bool` val: セットする値。
        """
        self.mplug().isLocked = val

    def apiSetDefault(self, val, reset=False, force=False):
        u"""
        undoに対応せずにアトリビュートのデフォルト値を内部単位でセットする。

        :param val: セットする値。
        :param `bool` reset: 現在の値もリセットする。
        :param `bool` force:
            ダイナミックアトリビュートでなくても許容する。
            つまり、このプラグ以外にも影響する操作を許容するかどうか。
        """
        if not(force or self.mfn().dynamic):
            raise RuntimeError('not dynamic attribute: ' + self.name_())

        typ = self.subType()
        if typ:
            if reset:
                setApiVal = mplugApiValueSetter(typ)
                for p, v in zip(self.children(), val):
                    v = attrFromRawValue(v, typ)
                    p.mfn_().default = v
                    setApiVal(p._CyObject__data['mplug'], v)
            else:
                for p, v in zip(self.children(), val):
                    p.mfn_().default = attrFromRawValue(v, typ)
        else:
            if reset:
                typ = self._CyObject__data['typeinfo']['typename']
                val = attrFromRawValue(val, typ)
                self.mfn().default = val
                mplugApiValueSetter(typ)(self._CyObject__data['mplug'], val)
            else:
                self.mfn().default = attrFromRawValue(val, self._CyObject__data['typeinfo']['typename'])

    def apiSetDefaultu(self, val, reset=False, force=False):
        u"""
        undoに対応せずにアトリビュートのデフォルト値をUI設定単位でセットする。

        :param val: セットする値。
        :param `bool` reset: 現在の値もリセットする。
        :param `bool` force:
            ダイナミックアトリビュートでなくても許容する。
            つまり、このプラグ以外にも影響する操作を許容するかどうか。
        """
        if not(force or self.mfn().dynamic):
            raise RuntimeError('not dynamic attribute: ' + self.name_())

        typ = self.subType()
        if typ:
            if reset:
                setApiVal = mplugApiValueSetter(typ)
                for p, v in zip(self.children(), val):
                    v = attrFromUnitValue(v, typ)
                    p.mfn_().default = v
                    setApiVal(p._CyObject__data['mplug'], v)
            else:
                for p, v in zip(self.children(), val):
                    p.mfn_().default = attrFromUnitValue(v, typ)
        else:
            if reset:
                typ = self._CyObject__data['typeinfo']['typename']
                val = attrFromUnitValue(val, typ)
                self.mfn().default = val
                mplugApiValueSetter(typ)(self._CyObject__data['mplug'], val)
            else:
                self.mfn().default = attrFromUnitValue(val, self._CyObject__data['typeinfo']['typename'])

    def apiGetSetNullProc(self):
        u"""
        undoに対応せずに Null をセットするための関数を得る。

        得られる関数はこのオブジェクトの参照を保持しない。

        :rtype: `callable`
        """
        return partial(self.mplug().setMObject, _2_MObject_kNullObj)

    def apiGetUndoSetProc(self):
        u"""
        undoに対応せずに現在の値をセットするための関数を得る。

        得られる関数はこのオブジェクトの参照を保持しない。

        :rtype: `callable`
        """
        return mplugCurrentValueSetter(self.mplug(), self._CyObject__data['typeinfo']['typename'])


#------------------------------------------------------------------------------
def _cmpbase(base, val):
    return base if val == base else val


def _mplugInList(mplug, mplugs):
    u"""
    MPlug がシーケンスに含まれるか厳密にチェックする。

    MPlug の比較は MObject の比較と同じなので、
    マルチアトリビュートの場合は個々の MPlug を別とみなすようにする。
    """
    for mp in mplugs:
        if mp == mplug and mp.info == mplug.info:
            return True
    return False


def _evalConnList(baseobj, results, pcls=None, basepcls=None, index=None, nodetype=None, exactType=False):
    u"""
    `Node.connections` や `Plug.connections` で得た結果を最後に加工する。
    """
    # ノードタイプが指定されたら、その派生タイプに限定する。
    if nodetype:
        # プラグの場合は、ノードの情報を取得しておく。
        if pcls:
            if basepcls:
                results = [(x[0], x[1], _node4ArgsByMPlug(x[1])) for x in results]
            else:
                results = [(x, _node4ArgsByMPlug(x)) for x in results]

        # ノードタイプでフィルタする。
        if exactType:
            if pcls or basepcls:
                results = [x for x in results if x[-1][-2].typeName == nodetype]
            else:
                results = [x for x in results if x[-2].typeName == nodetype]
        else:
            if pcls or basepcls:
                results = [x for x in results if _isDerivedNodeType(x[-1][-2].typeName, nodetype, x[-1][-1])]
            else:
                results = [x for x in results if _isDerivedNodeType(x[-2].typeName, nodetype, x[-1])]

    # インデックスが指定されたらスライスしてその要素だけにする。範囲外でもエラーにはならない。
    if index is not None:
        j = index + 1
        if j:
            results = results[index:j]
        else:
            results = results[index:]

    # ノードタイプが指定されていない場合、プラグのノード情報をここで取得する。
    if not nodetype and pcls:
        if basepcls:
            results = [(x[0], x[1], _node4ArgsByMPlug(x[1])) for x in results]
        else:
            results = [(x, _node4ArgsByMPlug(x)) for x in results]

    # 得た MPlug から戻り値となる Plug や Node オブジェクトを得る。
    # objMap によって、なるべく同じインスタンスがシェアされるようにする。
    if results:
        isNode = baseobj.CLASS_TYPE is CY_NODE
        noderef = _getObjectRef(baseobj) if isNode else baseobj._CyObject__data['noderef']
        nodename = noderef._CyObject__data['getname']()
        objMap = {nodename: noderef}

        # asPair=True の場合 basepcls が渡される。
        if basepcls:
            # 元プラグ情報から Plug を得る処理。
            if isNode:
                def toBase(base):
                    return _baseMPlugToPlug(basepcls, base, nodename_, noderef, objMap)
            else:
                def toBase(base):
                    if base is baseobj:
                        return base
                    return _baseMPlugToPlug(basepcls, base, nodename_, noderef, objMap)
            nodename_ = nodename + '.'

            # 得られた MPlug を Node や Plug オブジェクトにする処理。
            if pcls:
                toResult = lambda x: (toBase(x[0]), _mplugToPlug(pcls, x[1], x[2], objMap))
            else:
                toResult = lambda x: (toBase(x[0]), _argsToNode(x[1], objMap))

        else:
            # 得られた MPlug を Node や Plug オブジェクトにする処理。
            if pcls:
                toResult = lambda x: _mplugToPlug(pcls, x[0], x[1], objMap)
            else:
                toResult = lambda x: _argsToNode(x, objMap)

        results = [toResult(x) for x in results]

        toBase = None
        toResult = None

    if index is None:
        return results
    if results:
        return results[0]


def _argsToNode(args, objMap):
    u"""
    名前をキーとする辞書で結果を共有しつつ MPlug から得た引数リストから Node オブジェクトを得る。

    objMap には Node がキャッシュされる。
    """
    node = objMap.get(args[-1])
    if not node:
        node = _newNodeObjByArgs(args)
        objMap[args[-1]] = node
    elif node.CLASS_TYPE is CY_OBJREF:
        node = node()
        objMap[args[-1]] = node
    return node


def _mplugToPlug(pcls, mplug, nodeargs, objMap):
    u"""
    名前をキーとする辞書で結果を共有しつつ MPlug から Plug オブジェクトを得る。

    objMap には Plug とノードの ObjectRef がキャッシュされる。
    """
    name = nodeargs[-1] + '.' + mplug.partialName(includeNonMandatoryIndices=True, includeInstancedIndices=True)
    plug = objMap.get(name)
    if not plug:
        noderef = objMap.get(nodeargs[-1])
        if not noderef:
            noderef = _newNodeRefByArgs(nodeargs)
            objMap[nodeargs[-1]] = noderef
        plug = _newNodeRefPlug(pcls, noderef, mplug)
        objMap[name] = plug
    return plug


def _baseMPlugToPlug(pcls, mplug, nodename_, noderef, objMap):
    u"""
    名前をキーとする辞書で結果を共有しつつ MPlug とノードの ObjectRef から Plug オブジェクトを得る。

    objMap には Plug がキャッシュされる。
    """
    name = nodename_ + mplug.partialName(includeNonMandatoryIndices=True, includeInstancedIndices=True)
    plug = objMap.get(name)
    if not plug:
        plug = _newNodeRefPlug(pcls, noderef, mplug)
        objMap[name] = plug
    return plug


def _mplugHierCheck(mplug, name, above, below, evaluate=False):
    u"""
    階層をサポートした MPlug の属性チェックの汎用メソッド。

    :type mplug: :mayaapi2:`MPlug`
    :param mplug: 処理するプラグ。
    :param `str` name: チェックする属性名。
    :param `bool` above:
        上位アトリビュートの状態をチェックするかどうか。
    :param `bool` below:
        子アトリビュートの状態をチェックするかどうか。
    :rtype: `bool`
    """
    if getattr(mplug, name):
        return True

    if above:
        mp = mplug
        if mp.isElement:
            mp = mp.array()
            if getattr(mp, name):
                return True
        while mp.isChild:
            mp = mp.parent()
            if getattr(mp, name):
                return True
            if mp.isElement:
                mp = mp.array()
                if getattr(mp, name):
                    return True

    if below:
        def proc(mplug):
            if mplug.isArray:
                get = mplug.elementByPhysicalIndex
                for i in range(getattr(mplug, numElems)()):
                    mp = get(i)
                    if getattr(mp, name) or proc(mp):
                        return True
            elif mplug.isCompound:
                get = mplug.child
                for i in range(mplug.numChildren()):
                    mp = get(i)
                    if getattr(mp, name) or proc(mp):
                        return True
            return False
        numElems = 'evaluateNumElements' if evaluate  else 'numElements'
        return proc(mplug)
    return False


def _getFrom(mfn, method=None, checker=None):
    u"""
    任意のオブジェクトの任意のメソッドから値を得る。
    """
    if checker:
        checker = getattr(mfn, checker, None)
        if checker and not checker():
            return
    method = getattr(mfn, method, None)
    if method:
        return method()

_UNIT_ATTRTYPE_SET = frozenset([
    'doubleAngle',
    'doubleLinear',
    'floatAngle',
    'floatLinear',
    'time',
])

