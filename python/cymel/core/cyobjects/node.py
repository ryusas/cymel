# -*- coding: utf-8 -*-
u"""
:mayanode:`node` ノードタイプラッパークラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from uuid import uuid4 as _uuid4, UUID as _UUID
from ...common import *
from ...utils.namespace import _wrapNS, _mayaNS
from ...utils.operation import undoChunk
from ..typeregistry import nodetypes, _FIX_SLOTS
from .node_c import Node_c
from .cyobject import (
    CyObject, UUID_ATTR_NAME,
    IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES,
)

__all__ = ['Node']

_delete = cmds.delete
_lockNode = cmds.lockNode
_ls = cmds.ls
_namespace = cmds.namespace
_namespaceInfo = cmds.namespaceInfo
_rename = cmds.rename
_addAttr = cmds.addAttr
_setAttr = cmds.setAttr
_deleteAttr = cmds.deleteAttr
_connectAttr = cmds.connectAttr
_listAttr = cmds.listAttr
_referenceQuery = cmds.referenceQuery

_RE_NAMESAPACE_match = re.compile(r'(:?.*?):?([^:]+)$').match

_DOT_UUID_ATTR_NAME = '.' + UUID_ATTR_NAME


#------------------------------------------------------------------------------
class Node(Node_c):
    u"""
    :mayanode:`node` ノードタイプラッパークラス。
    """
    if _FIX_SLOTS:
        __slots__ = tuple()

    def delete(self):
        u"""
        ノードを削除する。
        """
        _delete(self.name())

    def setLocked(self, val=True):
        u"""
        ロック、又はアンロックする。

        :param `bool` val: True だとロック、 False だとアンロック。
        """
        _lockNode(self.name(), l=val)

    lock = setLocked  #: `setLocked` の別名。

    def unlock(self):
        u"""
        アンロックする。
        """
        _lockNode(self.name(), l=False)

    if MAYA_VERSION >= (2017,):
        def namespace(self):
            u"""
            ネームスペースを得る。

            :rtype: `.Namespace`
            """
            return _wrapNS(_RE_NAMESAPACE_match(self.mfn().absoluteName()).group(1))

    else:
        def namespace(self):
            u"""
            ネームスペースを得る。

            :rtype: `.Namespace`
            """
            return _mayaNS(self.mfn().namespace)

    def setNamespace(self, ns, ignoreShape=False):
        u"""
        ネームスペースをセットする。

        :param `str` ns: ネームスペース。
        :param `bool` ignoreShape: シェイプの名前は維持する。
        """
        name = self.name()

        # 存在しないネームスペースが指定された場合は、
        # 絶対ネームスペース指定でないとエラーになってしまうため、
        # ここで絶対化する。
        if not ns.startswith(':'):
            if _namespace(q=True, rel=True):
                x = _namespaceInfo(cur=True, an=True)
                ns = (x if x == ':' else (x + ':')) + ns
            else:
                ns = ':' + ns
        if not ns.endswith(':'):
            ns = ns + ':'

        return _rename(
            name,
            ns + _RE_NAMESAPACE_match(name.split('|')[-1]).group(2),
            ignoreShape=ignoreShape)

    def rename(self, name, ignoreShape=False):
        u"""
        リネームする。

        :param `str` name: 新しい名前。
        :param `bool` ignoreShape: シェイプの名前は維持する。
        """
        return _rename(self.name(), name, ignoreShape=ignoreShape)

    def _py_uuid(self, new=False, py=False):
        if not self.hasAttr(UUID_ATTR_NAME):
            self.addAttr(UUID_ATTR_NAME, 'string')
            new = True
        plug = self.plug_(UUID_ATTR_NAME)
        if new:
            val = _uuid4()
            plug.set(str(val))
            return val
        else:
            return _UUID(plug.get())

    def _py_assignUUID(self, val, py=False):
        if val:
            if not self.hasAttr(UUID_ATTR_NAME):
                self.addAttr(UUID_ATTR_NAME, 'string')
            self.plug_(UUID_ATTR_NAME).set(str(val))
        elif self.hasAttr(UUID_ATTR_NAME):
            _deleteAttr(self.name_() + _DOT_UUID_ATTR_NAME)

    if MAYA_VERSION < (2016,):
        uuid = _py_uuid
        assignUUID = _py_assignUUID

    else:
        def uuid(self, new=False, py=False):
            u"""
            UUID を得る。

            :param `bool` new:
                既存の ID 破棄して新しい ID を割り当てる。
            :param `bool` py:
                Maya 標準機能ではなく Python の機能を使って生成する
                UUID は uuid という名前のアトリビュートに保存される。
                2016 未満では常に True 扱いとなる。

                2016 以降では、
                それ以前に作られたファイルをリファレンスしていると
                シーンを開くたびにUUIDが変わってしまう問題を
                回避する目的で利用できる。
            :rtype: `.UUID`

            .. note::
                指定UUIDをアサインするには `assignUUID` 、
                UUIDからノードを得るには `.CyObject.byUUID` を利用する。
            """
            if py:
                return self._py_uuid(new)
            elif new:
                val = _uuid4()
                _rename(self.name(), str(val), uuid=True)
                return val
            else:
                return self._uuid()

        def assignUUID(self, val, py=False):
            u"""
            UUID をアサインする。

            :type val: `.UUID`
            :param val:
                アサインする UUID を指定する。
                py=True の場合は None を指定して消去することもできる。
            :param `bool` py:
                Maya 標準機能ではなく Python の機能を使って生成する
                UUID は uuid という名前のアトリビュートに保存される。
                2016 未満では常に True 扱いとなる。

                2016 以降では、
                それ以前に作られたファイルをリファレンスしていると
                シーンを開くたびにUUIDが変わってしまう問題を
                回避する目的で利用できる。
            """
            if py:
                self._py_assignUUID(val)
            else:
                _rename(self.name(), str(val), uuid=True)

    def referenceNode(self):
        u"""
        ノードがリファレンスの場合、それを管理する :mayanode:`reference` ノードを得る。

        :rtype: `.Reference` or None
        """
        if self.isFromReferencedFile():
            return CyObject(_referenceQuery(self.name_(), rfn=True))

    def addAttr(
        self, longName='', type=None, subType=None,
        channelBox=False,
        childNames=None, childShortNames=None, childSuffixes=None,
        proxy=None,
        getPlug=False,
        **kwargs
    ):
        u"""
        アトリビュートを追加する。

        :mayacmd:`addAttr` コマンドを使いやすくするラッパーである。

        * 型名の指定で -at と -dt を使い分ける煩わしさから解放。

        * コンパウンドの子の自動生成（特に double3 等の数値コンパウンド）。

        * proxy 指定の簡易化。

        * デフォルト値や最大値や最小値の指定を改善。

          - -dt 型でもデフォルト値を指定可能。
          - matrix 型は `.Matrix` でも `.Transformation` でも指定可能。
          - 数値コンパウンドでは `list` 形式での子の値を指定可能。
          - :mayacmd:`addAttr` コマンドの振る舞いの通り、
            内部単位（例えば角度ならラジアン）で指定する。

        * :mayacmd:`addAttr` コマンドのオプションも全て利用可能。

        :param `str` longName|ln:
            アトリビュートのロング名。
            最低限、ロング名のショート名のどちらかの指定が必要。

        :param `str` type:
            アトリビュートのタイプ名。省略時は double となる。

            attibuteType(at)系とdataType(dt)系の違いを気にせずに
            指定することができる。
            中にはどちらにも同じ型名が存在するものがあるが、
            その場合はより一般的な方が採用される
            （例えば matrix は dt となり、double3 は at となる）。

            タイプ名に ``at:`` か ``dt:`` の接頭辞を付加することで
            どちらの型かを明示することができる。
            ちなみに `.Plug.type` は、
            同じ型名が2バージョン存在する場合はこの形式で返す。

            このオプションではなく、本来の
            attibuteType(at) か dataType(dt)
            を使用して明示することもできる。

            proxy を指定した場合は、このオプションは無効となり、
            強制的にそれと同じタイプになる。

            double3 等の数値コンパウンドタイプの場合は、
            子アトリビュートも自動生成される。
            子のタイプや名前も自動決定されるが、
            subType、childNames、childShortNames、childSuffixes
            で明示することもできる。

            一般コンパウンドタイプ(compound)の場合でも、
            subType（デフォルトは double ）が共通の場合に限り、
            childNames、childShortNames、childSuffixes
            のいずれかを指定することで、子を自動生成できる。

        :param `str` subType:
            コンパウンドの子が自動生成される場合の、共通の子タイプを指定する。
            attibuteType(at)系のみを指定可能。

            double3 等の数値コンパウンドの子のタイプ名を明示することを
            主目的とするオプションだが、その場合
            doubleLinear や doubleAngle などの単位付きアトリビュートと
            したい場合だけ明示すれば良い。

        :param `bool` channelBox|cb:
            channelBox フラグを指定する。

        :param `sequence` childNames:
            コンパウンドの子アトリビュートのロング名を指定するリスト。
            省略すると childSuffixes から自動で決まる。

        :param `sequence` childShortNames:
            コンパウンドの子アトリビュートのショート名を指定するリスト。
            省略すると childSuffixes から自動で決まる。

        :param `sequence` childSuffixes:
            コンパウンドの子アトリビュート名を親名に準じた名前に
            自動指定するためのロング名用の接尾辞リスト。
            ショート名用には小文字化されたものになる。
            省略すると usedAsColor かどうかによって
            ``XYZW`` か ``RGBA`` になる。

        :param proxy|pxy:
            プロキシアトリビュートを追加する場合のマスターアトリビュートを指定する。
            これを指定した場合は usedAsProxy(uac) オプションは自動指定されるので
            指定不要である。

        :param `bool` getPlug:
            戻り値として `.Plug` を得るかどうか。
        :param kwargs:
            その他、 :mayacmd:`addAttr` コマンドのオプションを指定可能。
        :rtype: None or `.Plug`
        """
        nodename = self.name()
        nodename_ = nodename + '.'
        kwargs_pop = kwargs.pop
        kwargs_get = kwargs.get

        channelBox = kwargs_pop('cb', False) or channelBox
        proxy = kwargs_pop('pxy', None) or proxy

        # アトリビュートのロング名とショート名の取得。
        shortName = kwargs_pop('shortName', kwargs_pop('sn', None))
        ln = kwargs_pop('ln', None)
        if not longName:
            if ln:
                longName = ln
            elif not shortName:
                raise RuntimeError('addAttr: New attribute needs either a long or short name.')
        name = longName or shortName
        if longName:
            kwargs['ln'] = longName
        if shortName:
            kwargs['sn'] = shortName

        # アトリビュートパス名。
        # NOTE: 2025以降のトップレベルは . を先頭に付加するようにしたが、ノード名との境界が .. になっても問題ないようだ。
        pathname = _pathnameToAddAttr(name, kwargs)

        # proxy オプションはクラッシュしやすいので usedAsProxy を使わなければならないのをカバーする。
        if proxy:
            proxy = CyObject(proxy)
            kwargs_pop('usedAsProxy', None)
            kwargs['uap'] = True

            # type は強制的に同じものにする。
            type = proxy.type()
            kwargs_pop('attributeType', kwargs_pop('at', None))
            kwargs_pop('dataType', kwargs_pop('dt', None))
            if proxy.isUsedAsColor():
                kwargs_pop('usedAsColor', None)
                kwargs['uac'] = True
            else:
                kwargs_pop('usedAsColor', kwargs_pop('uac', False))
            isAttributeType = None

        # type が指定された場合は -at や -dt の指定は無視。
        elif type:
            kwargs_pop('attributeType', kwargs_pop('at', None))
            kwargs_pop('dataType', kwargs_pop('dt', None))
            isAttributeType = None

        # type が指定されない場合は -at や -dt の指定から得る。デフォルトは double 。
        else:
            type = kwargs_pop('dataType', kwargs_pop('dt', None))
            if type:
                if kwargs_pop('attributeType', kwargs_pop('at', None)):
                    raise RuntimeError('addAttr: Cannot specify both an attribute type and a data type.')
                isAttributeType = False
                kwargs['dt'] = type
            else:
                type = kwargs_pop('attributeType', kwargs_pop('at', 'double'))
                isAttributeType = True
                kwargs['at'] = type

        # -at か -dt かの判別。
        if isAttributeType is None:
            isAttributeType = _distinguishAttrType(type, kwargs)
        childArgs = None

        # -at の場合。
        if isAttributeType:
            # addAttr と同時にデフォルト値がセットできないタイプはあとで行う。
            type = kwargs['at']
            if type in _COMPLEX_AT_TYPENAME_SET:
                default = kwargs_pop('defaultValue', kwargs_pop('dv', None))
                nChildren = 0

            # コンパウンドで子の名前や接尾辞が指定された場合は、子を自動生成する。
            elif type == 'compound':
                if childNames or childShortNames or childSuffixes:
                    nChildren = kwargs_pop('numberOfChildren', kwargs_get('nc', 0))
                    if not nChildren:
                        if childNames:
                            nChildren = len(childNames)
                        elif childShortNames:
                            nChildren = len(childShortNames)
                        else:
                            nChildren = len(childSuffixes)
                    elif childSuffixes and nChildren != len(childSuffixes):
                        raise RuntimeError('addAttr: invalid number of childSuffixes')
                    kwargs['nc'] = nChildren
                    if not subType:
                        subType = 'double'
                else:
                    default = None
                    nChildren = 0

            # 特定の型では float3 のカラーと同等となる。
            elif type in _COLOR_AT_TYPENAME_SET:
                subType = 'float'
                childSuffixes = 'RGB'
                nChildren = 3
                kwargs_pop('numberOfChildren', kwargs_pop('nc', None))

            # 末尾が数字のアトリビュート型なら数値コンパウンド型として処理する。
            else:
                m = _RE_NUMERIC_COMPOUND_match(type)
                if m:
                    if proxy:
                        masterChildren = proxy.children()
                        subType = masterChildren[0].type()
                        nChildren = len(masterChildren)
                    else:
                        if not subType:
                            subType = m.group(1)
                        nChildren = int(m.group(2))
                    if not childSuffixes:
                        childSuffixes = ('RGBA' if kwargs_get('usedAsColor', kwargs_get('uac')) else 'XYZW')[:nChildren]
                    elif len(childSuffixes) != nChildren:
                        raise RuntimeError('addAttr: invalid number of childSuffixes')
                    kwargs_pop('numberOfChildren', kwargs_pop('nc', None))
                else:
                    default = None
                    nChildren = 0

            # コンパウンドの子を自動生成するためのオプション辞書の準備。
            if nChildren:
                # 子の名前リストが指定されていなければ、自動的に決定する。
                childLongNames = childNames
                if childLongNames:
                    if len(childLongNames) != nChildren:
                        raise RuntimeError('addAttr: Different number of children for each option')
                elif longName and childSuffixes:
                    childLongNames = [longName + x for x in childSuffixes]

                if childShortNames:
                    if len(childShortNames) != nChildren:
                        raise RuntimeError('addAttr: Different number of children for each option')
                elif shortName and childSuffixes:
                    childShortNames = [shortName + x.lower() for x in childSuffixes]

                childNames = childLongNames or childShortNames

                # 子ごとのオプション辞書を生成し、名前をセットする。
                childrenOpts = [dict() for x in childNames]
                if childLongNames:
                    for opts, x in zip(childrenOpts, childLongNames):
                        opts['ln'] = x
                if childShortNames:
                    for opts, x in zip(childrenOpts, childShortNames):
                        opts['sn'] = x

                # オプション引数から親には不要なもの（min, max や default）を除去し、子に使うようにする。
                default = kwargs_pop('defaultValue', kwargs_pop('dv', None))
                apivals = [(s, kwargs_pop(l, kwargs_pop(s, None))) for l, s in _ATTR_APIVAL_OPTS]
                apivals = [x for x in apivals if x[1] is not None]

                # 親アトリビュートのオプション辞書の複製を子アトリビュート用の共通辞書として、不要なオプションを除去。
                childArgs = dict(kwargs)
                childArgs_pop = childArgs.pop
                childArgs_pop('multi', childArgs_pop('m', None))
                childArgs_pop('indexMatters', childArgs_pop('im', None))
                childArgs_pop('usedAsColor', childArgs_pop('uac', None))
                childArgs_pop('numberOfChildren', childArgs_pop('nc', None))
                childArgs['p'] = pathname
                childArgs.pop('parent', None)

                # 子の型指定。
                # デフォルト値の指定ができない型なら、あとでサポートするようにする。
                if _distinguishAttrType(subType, childArgs) and default and childArgs['at'] != 'time':
                    apivals.append(('dv', default))
                    default = None

                # 親ではなく子に設定する値（min, max や default）。
                for key, val in apivals:
                    if isinstance(val, LIST_OR_TUPLE):
                        for opts, v in zip(childrenOpts, val):
                            if v is not None:
                                opts[key] = v
                    else:
                        childArgs[key] = val

                # 親アトリビュートのオプション辞書から不要なオプションを除去。
                kwargs_pop('usedAsProxy', kwargs_pop('uap', None))
                kwargs_pop('keyable', kwargs_pop('k', None))

        # -dt の場合、デフォルト値はセットできないのでサポートする。
        else:
            default = kwargs_pop('defaultValue', kwargs_pop('dv', None))

        #print(nodename, kwargs)

        # コンパウンドアトリビュート生成。
        if childArgs:
            with undoChunk:
                _addAttr(nodename, **kwargs)

                # 子の生成。
                for opts in childrenOpts:
                    args = dict(childArgs)
                    args.update(opts)
                    #print(nodename, args)
                    _addAttr(nodename, **args)

                # Attribute に対する処理。
                if channelBox or default is not None:
                    plug = self.plug_(pathname)
                    children = plug.children()

                    # デフォルト値は Plug ではなく Attribute に設定するので、undo/redo のときに何もしなくても元に戻る。
                    if isinstance(default, LIST_OR_TUPLE):
                        for p, v in zip(children, default):
                            if v is not None:
                                p.apiSetDefault(v, True, True)
                    elif default is not None:
                        for p in children:
                            p.apiSetDefault(default, True, True)

                    # フラグも Plug ではなく Attribute に設定すれば、undo/redo のときに何もしなくても元に戻る。
                    if isinstance(channelBox, Iterable):
                        for p, v in zip(children, channelBox):
                            if v:
                                p.mfn().channelBox = True
                    elif channelBox:
                        for p in children:
                            p.mfn().channelBox = True
                else:
                    plug = None

                # Plug に対する処理。
                if proxy:
                    pre_ = nodename_ + (pathname[1:] if pathname.startswith('.') else pathname) + '.'
                    for x, src in zip(childNames, masterChildren):
                        _connectAttr(src.name_(), pre_ + x)

        # 単体のアトリビュートの生成。
        elif proxy:
            with undoChunk:
                plug = self.__addOneAttr(nodename, pathname, default, channelBox, **kwargs)
                _connectAttr(proxy.name_(), nodename_ + (pathname[1:] if pathname.startswith('.') else pathname))
        else:
            with undoChunk:
                plug = self.__addOneAttr(nodename, pathname, default, channelBox, **kwargs)

        # Plug オブジェクトを返す。
        if getPlug:
            return plug or self.plug_(pathname)

    def __addOneAttr(self, nodename, pathname, default, channelBox, **kwargs):
        _addAttr(nodename, **kwargs)

        if channelBox or default is not None:
            plug = self.plug_(pathname)
            if default is not None:
                plug.apiSetDefault(default, True, True)
            if channelBox:
                plug.mfn().channelBox = True
            return plug

    def plugs(self, **kwargs):
        u"""
        指定した条件にマッチするプラグのリストを得る。

        :mayacmd:`listAttr` コマンドの単純なラッパーであり、
        オプションで条件を指定しなければ、
        ノードの全アトリビュートが得られる。

        ただし、 m=True を指定しなければマルチ要素は得られない。
        また、 worldSpace アトリビュートの場合は、
        m=True を指定しても要素は得られない
        （worldSpace の場合はインデックスを明示しない方が良いため）。

        :rtype: `list`
        """
        p = self.plug_
        return [p(x) for x in (_listAttr(self.name(), **kwargs) or EMPTY_TUPLE)]

    listAttr = plugs  #: `plugs` の別名。

    def aliases(self):
        u"""
        別名が定義されているアトリビュートのリストを得る。

        別名と `.Plug` のペアのリストが得られる。

        :rtype: `list`
        """
        p = self.plug_
        return [(x, p(y)) for x, y in self.mfn().getAliasList()]

    listAliases = aliases  #: `aliases` の別名。

nodetypes.registerNodeClass(Node, 'node')


#------------------------------------------------------------------------------
if IS_SUPPORTING_NON_UNIQUE_ATTR_NAMES:
    def _pathnameToAddAttr(name, opts):
        return (opts.get('parent') or opts.get('p', '')) + '.' + name
else:
    def _pathnameToAddAttr(name, opts):
        return name


def _distinguishAttrType(typename, _kwargs):
    u"""
    タイプ名が -at か -dt か判別してオプション辞書にセットする。
    """
    if typename.startswith('at:'):
        typename = typename[3:]
        _kwargs['at'] = typename
        return True
    elif typename.startswith('dt:'):
        typename = typename[3:]
        _kwargs['dt'] = typename
        return False
    elif typename in _AT_TYPENAME_SET:
        _kwargs['at'] = typename
        return True
    else:
        _kwargs['dt'] = typename
        return False

_AT_TYPENAME_SET = frozenset([
    'generic',
    'message',
    'bool',
    'byte',
    'char',
    'short',
    'long',
    'float',
    'double',
    'enum',
    'floatAngle',
    'doubleAngle',
    'floatLinear',
    'doubleLinear',
    'time',
    'fltMatrix',
    'short2',
    'short3',
    'long2',
    'long3',
    'float2',
    'float3',
    'double2',
    'double3',
    'double4',
    'reflectance',
    'spectrum',
    'compound',
])  #: -at で作るアトリビュート型名セット。

_COLOR_AT_TYPENAME_SET = frozenset([
    'spectrum',
    'reflectance',
])
#_COLOR_DT_TYPENAME_SET = frozenset([
#    'spectrumRGB',
#    'reflectanceRGB',
#)]

_RE_NUMERIC_COMPOUND_match = re.compile(r'(short|long|float|double)(\d)$').match  #: 数値コンパウンド型名。

_ATTR_APIVAL_OPTS = (
    #('defaultValue', 'dv'),  # 不要なので除外したが、あっても問題はない。
    ('minValue', 'min'),
    ('maxValue', 'max'),
    ('softMinValue', 'smn'),
    ('softMaxValue', 'smx'),
)  #: addAttr で数値コンパウンドを生成する際に子に指定するオプション値。

_COMPLEX_AT_TYPENAME_SET = frozenset([
    'time',
    'matrix',
    'fltMatrix',
])

