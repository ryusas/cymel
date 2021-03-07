# -*- coding: utf-8 -*-
u"""
ノードタイプのラッパークラスのマネージャー。
"""
from ..common import *
from ..pyutils import Singleton, parentClasses
from .typeinfo import isDerivedNodeType, getInheritedNodeTypes

__all__ = ['nodetypes']

_FIX_SLOTS = True  #: 標準 CyObject クラスのスロットを固定する。


#------------------------------------------------------------------------------
class NodeTypes(with_metaclass(Singleton, object)):
    u"""
    ノードタイプのラッパークラスのマネージャー。

    唯一のインスタンスである `nodetypes` が生成済み。

    全てのノードクラスはこの属性としてアクセスできる。

    cymel では、プラグインも含む全てのノードタイプの
    ラッパークラスが提供されるが、機能実装のために
    あらかじめ用意されている主要なノードタイプ以外は、
    最初にアクセスしたときなどの必要なときに自動生成される。

    システムが提供する標準的なクラス名は、
    ノードタイプ名の先頭を大文字にした名前となる。

    既存のノードクラスを継承してカスタムクラスを作ることもできる。
    カスタムクラスはノードタイプのみから純粋に決まるものでも、
    その他の任意の条件によって決まるものでも良い。

    カスタムクラスは、
    システムに登録するなどせずにそのまま利用可能だが、
    `registerNodeClass` によって登録することもできる。
    インスタンスを得る場合、
    そのクラスを直接指定すればインスタンスを得られるが、
    クラスが登録してあれば
    `.CyObject` からインスタンスを得ることで
    自動的にクラスを決定させることができる。
    """
    def __getattr__(self, name):
        u"""
        ベーシッククラスを得る。

        登録されたクラスは __dict__ に追加されていくので、
        その場合はこの特殊メソッドは呼ばれない。

        同名のベーシッククラスと検査メソッド付きクラスは、
        ベーシッククラスが優先される。

        未登録のクラス名を指定した場合、
        クラス名の先頭を小文字にしたノードタイプ名の
        ベーシッククラスとして自動生成、登録される。

        :param `str` name: クラス名。
        :rtype: `type`
        """
        if _RE_STARTS_WITH_CAPITAL_match(name):
            try:
                return self.basicNodeClass(name[0].lower() + name[1:])
            except ValueError:
                return self.basicNodeClass(name)
        raise ValueError('unknown class name: ' + name)

    def registerNodeClass(self, cls, nodetype):
        u"""
        ノードクラスを登録する。

        ノードクラスは、適合検査のためのスタティックメソッド
        ``_verifyNode`` を持つ **検査メソッド付きクラス** と、
        それを持たない **ベーシッククラス** に分けられる。

        適合検査のためのスタティックメソッドの仕様は以下の通り。

        * _verifyNode(mfn, name)

          引数に、
          Python API 2 の :mayaapi2:`MFnDependencyNode`
          派生クラスのインスタンス（例えば dagNode なら
          :mayaapi2:`MFnDagNode` など）と、
          ノードのパーシャルパスなどのユニーク名が渡され、
          適合の可否を表すブール値を返すものとする。

        ``_verifyNode`` を実装した場合、さらに
        `Node.createNode <.Node_c.createNode>`
        もオーバーライドして、
        ノード生成時に条件を満たすようにすることを推奨する。

        ベーシッククラスは、ノードタイプへの紐付けが厳格で、
        抽象タイプも含む全てのノードタイプごとに1つずつ存在するか
        自動生成される。
        カスタムクラスをベーシッククラスとして登録する場合も、
        ノードタイプと矛盾しない親クラスを継承しなければならない。
        クラス実装で、継承すべき親クラスを取得するには
        `parentBasicNodeClass` が便利である。
        1つのノードタイプへの競合する登録は上書き登録となり、
        警告が出力された上で古いクラスの登録はサブクラスも含めて
        全て抹消される（システムが先んじて行った自動登録を上書き
        してもさして害は無い）。

        一方、適合検査メソッド付きクラスは、
        ノードタイプへの紐付けが厳格でなくても問題ない。
        クラスの継承と登録するノードタイプに矛盾さえ無ければ、
        抽象タイプも含むどのノードタイプに登録するのも自由である。
        複数の検査メソッド付きクラスが、1つのノードタイプに競合して
        登録されることは問題なく、
        また、同じクラスを複数のノードタイプに登録しても構わない。
        登録時は、ノードタイプごとに管理されているリストの最初に挿入
        されるため、後から登録したものほど優先される。

        :type cls: `type`
        :param cls: 登録するクラス。
        :param `str` nodetype: 紐付けるノードタイプ名。
        """
        # 検査メソッド付きクラスの場合。
        if hasattr(cls, '_verifyNode'):
            # 親クラスの一致をチェック。
            invalid = True
            for sc in parentClasses(cls):
                typs = _clsNodeTypeDict_get(sc)
                if typs:
                    # 親クラスが紐付けられたノードタイプのいずれかの派生でなければエラー。
                    invalid = True
                    for typ in typs:
                        if isDerivedNodeType(nodetype, typ):
                            invalid = False
                            break
                    if invalid:
                        break
            if invalid:
                raise ValueError("registerNoeClass: class inheritance does not match node type: " + repr(cls))

            # 評価リストの先頭に追加。
            #print('# RegisterConditionalNodeClass: %s %r %r' % (nodetype, exact, cls))
            clss = _evalAbstrClsDict_get(nodetype)
            if clss:
                try:
                    clss.remove(cls)
                except ValueError:
                    pass
                else:
                    warning('registerNoeClass: updated the same class registration for: ' + nodetype + ' ' + repr(cls))
                clss.insert(0, cls)
            else:
                _evalAbstrClsDict[nodetype] = [cls]

            # 登録。
            typs = _clsNodeTypeDict_get(cls)
            if typs:
                _clsNodeTypeDict[cls] = (nodetype,) + typs
            else:
                _clsNodeTypeDict[cls] = (nodetype,)
            name = cls.__name__
            old = self.__dict__.get(name)
            if not old or hasattr(old, '_verifyNode'):
                # 同名のベーシッククラスが在る場合、属性ではそちらが優先される。
                setattr(self, name, cls)

        # ベーシッククラスの場合。
        else:
            # 親クラスの一致をチェック。
            if nodetype != 'node':
                # 親タイプに完全に一致するベーシッククラスを継承していなければならない。
                invalid = True
                for sc in cls.mro()[1:-3]:  # 最後の2個は [Node_c, CyObject, object] なので省いている。
                    typ = _clsNodeTypeDict_get(sc)
                    if typ:
                        # 親に _verifyNode 属性が無いことは必然なので、ノードタイプのみをチェックする。
                        if typ[0] == getInheritedNodeTypes(nodetype)[1]:
                            invalid = False
                        break
                if invalid:
                    raise ValueError("class inheritance missmatch for maya nodetype hierarchy: %s(%s)" % (cls.__name__, base.__name__))

            # ノードタイプの登録が既にあれば、警告を出力しつつ削除する。
            oldcls = _basicClsDict_get(nodetype)
            if oldcls:
                self.deregisterNodeClass(oldcls, warn=True)

            # 登録。
            self.__registerBasicNodeCls(nodetype, cls)

    def deregisterNodeClass(self, cls, warn=False):
        u"""
        ノードクラスとそのサブクラスの登録を削除する。

        :type cls: `type`
        :param cls: 登録を削除するクラス。
        :param `bool` warn: 削除しながら警告メッセージを出力するかどうか。
        """
        cnt = _deregisterNodeClass(_evalAbstrClsDict, cls, warn)
        cnt += _deregisterNodeClass(_basicClsDict, cls, warn)
        if not cnt:
            raise ValueError('unknown class: ' + repr(cls))

    def relatedNodeTypes(self, cls):
        u"""
        クラスに結び付けられているノードタイプのタプルを得る。

        ベーシッククラスのノードタイプは1つだが、
        検査メソッド付きカスタムクラスの場合は
        複数タイプへの紐付けも有り得る。

        :type cls: `type`
        :param cls: クラス。
        :rtype: `tuple`
        """
        typs = _clsNodeTypeDict_get(cls)
        if typs:
            return typs
        for sc in cls.mro()[1:-3]:  # 最後の3個は [Node_c, CyObject, object] なので省いている。
            typs = _clsNodeTypeDict_get(sc)
            if typs:
                return typs
        return EMPTY_TUPLE

    def basicNodeClass(self, nodetype, nodename=None):
        u"""
        ノードタイプ名のみを条件として決まるベーシッククラスを得る。

        :param `str` nodetype: ノードタイプ名。
        :param `str` nodename:
            実際のノードを特定する名前。
            必須ではないが、指定すると未知のタイプの処理がやや高速。
        :rtype: `type`
        """
        return _basicClsDict_get(nodetype) or self.__newBasicNodeClass(getInheritedNodeTypes(nodetype, nodename))

    def parentBasicNodeClass(self, nodetype, nodename=None):
        u"""
        指定ノードタイプの親タイプ名のみを条件として決まるベーシッククラスを得る。

        :param `str` nodetype: ノードタイプ名。
        :param `str` nodename:
            実際のノードを特定する名前。
            必須ではないが、指定すると未知のタイプの処理がやや高速。
        :rtype: `type` ('node' を指定した場合のみ `None` となる)
        """
        inherited = getInheritedNodeTypes(nodetype, nodename)[1:]
        if inherited:
            return _basicClsDict_get(inherited[0]) or self.__newBasicNodeClass(inherited)

    def __newBasicNodeClass(self, inherited):
        u"""
        ノードタイプ名のみを条件として決まるベーシッククラスを新規に登録して得る。

        指定タイプは未登録である前提。
        少なくとも、最上位のタイプ node だけは登録されている前提。
        継承タイプ（それらも必要なら登録）を順次得て、指定タイプを登録する。

        :param `list` inherited: 先頭を指定タイプとする継承リスト。
        :rtype: `type`
        """
        i = 1
        typ = inherited[i]
        cls = _basicClsDict_get(typ)
        while not cls:
            i += 1
            typ = inherited[i]
            cls = _basicClsDict_get(typ)
        i -= 1
        while i >= 0:
            typ = inherited[i]
            cls = type(typ[0].upper() + typ[1:], (cls,), _CLS_DEFAULT_ATTRS)
            self.__registerBasicNodeCls(typ, cls)
            i -= 1
        return cls

    def __registerBasicNodeCls(self, nodetype, cls):
        u"""
        ノードタイプ名のみを条件として決まるシンプルなラッパークラスを属性にセットする。

        同名の検査メソッド付きクラスがあったとしても属性では優先される。
        """
        #print('# RegisterBasicNodeClass: %s %r' % (nodetype, cls))
        _basicClsDict[nodetype] = cls
        _clsNodeTypeDict[cls] = (nodetype,)
        setattr(self, cls.__name__, cls)

    def __decideClass(self, nodename, nodetype, getMFn, basecls=None):
        u"""
        登録されたクラスの中からノードに最適なものを決定する。

        :param `str` nodename: ノードを特定する名前。
        :param `str` nodetype: ノードタイプ名。
        :param mfn:
            効率的に API 2 ファンクションセットを得るための
            呼び出し可能オブジェクト。
        :param basecls:
            検査メソッド付きクラスを指定することで、
            テストするクラスをその派生クラスに限定する。
            マッチするものが無ければ None が返される。
        :rtype: `type` or None
        """
        if basecls:
            # 検査メソッド付きノードクラス辞書の中から basecls 派生クラスを調べる。
            if _evalAbstrClsDict and basecls in _clsNodeTypeDict:
                mfn = None
                for typ in getInheritedNodeTypes(nodetype, nodename):
                    for cls in _evalAbstrClsDict_get(typ, EMPTY_TUPLE):
                        if issubclass(cls, basecls):  # <-- この判定が加わるだけ。
                            if mfn is None:
                                mfn = getMFn()
                            if cls._verifyNode(mfn, nodename):
                                return cls
            # basecls が未登録なら、それだけを適合検査する。
            elif basecls._verifyNode(getMFn(), nodename):
                return basecls

            # ベーシッククラスは認めない。

        else:
            # 検査メソッド付きノードクラス辞書を調べる。
            if _evalAbstrClsDict:
                mfn = None
                for typ in getInheritedNodeTypes(nodetype, nodename):
                    for cls in _evalAbstrClsDict_get(typ, EMPTY_TUPLE):
                        if mfn is None:
                            mfn = getMFn()
                        if cls._verifyNode(mfn, nodename):
                            return cls

            # ベーシックノードクラスを得る。
            return self.basicNodeClass(nodetype, nodename)


#------------------------------------------------------------------------------
def _deregisterNodeClass(dic, cls, warn):
    u"""
    クラスの種類ごとの `NodeTypes.deregisterNodeClass` サブルーチン。

    :param `dict` dic: クラスの種類に応じた登録辞書。
    :param `type` cls: クラス。
    :param `callable` proc: クラス登録削除用プロシージャ。
    :rtype: `int`
    """
    cnt = 0
    for typ in list(dic):
        subc = dic[typ]
        if issubclass(subc, cls):
            del dic[typ]
            del _clsNodeTypeDict[subc]
            if warn:
                warning('node class deregistered: ' + repr(subc))
            cnt += 1
    return cnt

_evalAbstrClsDict = {}  #: 検査メソッド付きクラス辞書。
_basicClsDict = {}  #: ベーシッククラス辞書。
_clsNodeTypeDict = {}  #: クラスに紐付けられたノードタイプの辞書。

_evalAbstrClsDict_get = _evalAbstrClsDict.get
_basicClsDict_get = _basicClsDict.get
_clsNodeTypeDict_get = _clsNodeTypeDict.get

_RE_STARTS_WITH_CAPITAL_match = re.compile(r'[A-Z]').match

nodetypes = NodeTypes()  #: `NodeTypes` の唯一のインスタンス。

_CLS_DEFAULT_ATTRS = {'__slots__': tuple()} if _FIX_SLOTS else {}

