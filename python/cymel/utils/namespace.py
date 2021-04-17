# -*- coding: utf-8 -*-
u"""
Mayaネームスペース。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..common import *
from .utils import correctNodeNameNS
from ..pyutils import iterTreeBreadthFirst, iterTreeDepthFirst

__all__ = ['Namespace', 'NS', 'RelativeNamespace', 'RelativeNS']

_str_new = UNICODE.__new__
_str_add = UNICODE.__add__
_str_eq = UNICODE.__eq__
_str_ne = UNICODE.__ne__
_str_le = UNICODE.__le__
_str_lt = UNICODE.__lt__
_str_ge = UNICODE.__ge__
_str_gt = UNICODE.__gt__

_namespace = cmds.namespace
_namespaceInfo = cmds.namespaceInfo
_ls = cmds.ls

_INTERNAL_NS_SET = frozenset([':UI', ':shared',])


#------------------------------------------------------------------------------
class Namespace(UNICODE):
    u"""
    Mayaネームスペースクラス。

    カレントネームスペースを制御するコンテキストとしても使用できる。

    文字列の派生クラスなので、通常の文字列のように振る舞う。

    それがMayaに実際に存在するかどうかにかかわらず、
    インスタンスは生成できる。
    そして、カレントにする際などに存在しなければ生成される。

    イミュータブルである文字列としては、
    Mayaの相対ネームスペースモード如何にかかわらず、
    常に : で始まる絶対名で扱われる。

    .. warning::
        カレントネームスペース設定時、
        Mayaの相対ネームスペースモードの設定による挙動の違いには注意が必要。

        - ノード生成は、相対ネームスペースモード設定にかかわらず、
          カレントネームスペースでの命名となる。

        - ノード名の評価や指定は、相対ネームスペースモード設定が有効でないと、
          カレントネームスペース指定の影響はない。

        本クラスにおけるネームスペースのハンドリングは、ノード生成ではないため、
        相対名が有効に機能するのは相対ネームスペースモードが有効な場合のみである。
    """
    __slots__ = ('_lastcur',)

    def __new__(cls, ns=''):
        return _str_new(cls, _correctNS(ns))

    def __enter__(self):
        self._lastcur = _namespaceInfo(cur=True, an=True)
        _setCurrentNS(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _setCurrentNS(self._lastcur)

    def __repr__(self):
        return "%s('%s')" % (type(self).__name__, self)

    def __add__(self, s):
        return _str_add(self, ':' + s.strip(':'))

    def __eq__(self, ns):
        return _str_eq(self, _correctNS(ns))

    def __ne__(self, ns):
        return _str_ne(self, _correctNS(ns))

    def __le__(self, ns):
        return _str_le(self, _correctNS(ns))

    def __lt__(self, ns):
        return _str_lt(self, _correctNS(ns))

    def __ge__(self, ns):
        return _str_ge(self, _correctNS(ns))

    def __gt__(self, ns):
        return _str_gt(self, _correctNS(ns))

    __hash__ = UNICODE.__hash__

    @staticmethod
    def relativeMode():
        u"""
        相対ネームスペースモードが有効かどうか。

        :rtype: `bool`
        """
        return _namespace(q=True, rel=True)

    @staticmethod
    def setRelativeMode(state):
        u"""
        相対ネームスペースモードをセットする。

        :param `bool` state: 有効か無効か。
        """
        _namespace(rel=state)

    @classmethod
    def current(cls):
        u"""
        カレントネームスペースを得る。

        :rtype: `Namespace`
        """
        return _str_new(cls, _namespaceInfo(cur=True, an=True))

    def isCurrent(self):
        u"""
        ネームスペースがカレントかどうか。
        """
        return _str_eq(self, _namespaceInfo(cur=True, an=True))

    def setCurrent(self):
        u"""
        ネームスペースをカレントにする。存在しない場合は追加される。
        """
        _setCurrentNS(self)

    def name(self):
        u"""
        Maya の相対ネームスペースモードの影響のもと、相対名を得る。

        相対ネームスペースモードが ON の場合はカレントネームスペースから、
        OFF の場合はルートネームスペースからの相対名となる。

        :rtype: `str`
        """
        if _namespace(q=True, rel=True):
            return self.relative()
        return self[1:]

    def absolute(self):
        u"""
        カレント設定に依存しない絶対名であり、このネームスペースの文字列そのもの。

        :rtype: `str`
        """
        return UNICODE(self)

    def relative(self):
        u"""
        カレントネームスペースからの相対名を得る。

        Mayaの相対ネームスペースモードの状態にかかわらず、
        常に、カレントネームスペースからの相対名が得られる。

        :rtype: `str`
        """
        cur = _namespaceInfo(cur=True, an=True)
        if _str_eq(self, cur):
            return ''
        if cur != ':':
            cur += ':'
        if self.startswith(cur):
            return self[len(cur):]
        return UNICODE(self)

    def exists(self):
        u"""
        ネームスペースが実際に存在するかどうか。

        :rtype: `bool`
        """
        return _namespace(ex=self)

    def create(self):
        u"""
        ネームスペースを生成する。
        """
        _namespace(add=self)

    def parent(self):
        u"""
        親ネームスペースを得る。

        :rtype: `Namespace` or None
        """
        if _str_ne(self, ':'):
            return _str_new(self.__class__, ':'.join(self.split(':')[:-1]) or ':')

    def children(self, internal=False):
        u"""
        子ネームスペースのリストを得る。

        :param `bool` internal: 
            Mayaのシステムネームスペースを除外しない。
        :rtype: `list`
        """
        res = _namespaceInfo(self, lon=True, an=True)
        if res:
            cls = self.__class__
            if internal or _str_ne(self, ':'):
                return [cls(x) for x in res]
            else:
                return [cls(x) for x in res if x not in _INTERNAL_NS_SET]
        return []

    def iterBreadthFirst(self):
        u"""
        ネームスペース階層を幅優先反復する。

        :rtype: yield `Namespace`
        """
        return iterTreeBreadthFirst([self], 'children')

    def iterDepthFirst(self):
        u"""
        ネームスペース階層を深さ優先反復する。

        :rtype: yield `Namespace`
        """
        return iterTreeDepthFirst([self], 'children')

    def ls(self, pattern='*', **kwargs):
        u"""
        このネームスペース直下のノードのリストを得る。

        :param `str` pattern:
            名前のパターン。
        :param kwargs:
            :mayacmd:`ls` コマンドのオプションを指定可能。
        :rtype: `list`
        """
        global _CyObject
        from ..core import CyObject as _CyObject
        Namespace.ls = _Namespace_ls
        return self.ls(pattern, **kwargs)

NS = Namespace  #: `Namespace` の別名。


#------------------------------------------------------------------------------
class RelativeNamespace(object):
    u"""
    相対ネームスペースモードを切り替えるコンテキスト。
    """
    __slots__ = ('namespace', '_lastcur', '_notrel')

    def __init__(self, namespace=None):
        if namespace:
            if isinstance(namespace, Namespace):
                self.namespace = namespace
            else:
                self.namespace = Namespace(namespace)
        else:
            self.namespace = None

    def __enter__(self):
        ns = self.namespace and _namespaceInfo(cur=True, an=True)
        if self.namespace == ns:
            self._lastcur = None
        else:
            self._lastcur = ns
            _setCurrentNS(self.namespace)

        if _namespace(q=True, rel=True):
            self._notrel = False
        else:
            self._notrel = True
            _namespace(rel=True)

    def __exit__(self, exc_type, exc_value, traceback):
        if self._notrel:
            _namespace(rel=False)
        if self._lastcur:
            _setCurrentNS(self._lastcur)

RelativeNS = RelativeNamespace  #: `RelativeNamespace` の別名。


#------------------------------------------------------------------------------
def _Namespace_ls(self, pattern='*', **kwargs):
    return [_CyObject(x) for x in _ls(self + pattern, **kwargs)]


def _correctNS(ns):
    u"""
    ネームスペース文字列を補正する。

    - 使用できない文字を修正、末尾の : を除去。
    - Mayaの相対モード設定に従い : で始まる絶対名に補正。
    """
    ns = correctNodeNameNS(ns)
    if ns.startswith(':'):
        return ns
    c = _namespaceInfo(cur=True, an=True) if _namespace(q=True, rel=True) else ':'
    if ns:
        return (c if c == ':' else (c + ':')) + ns
    return c


def _setCurrentNS(ns):
    u"""
    カレントネームスペースをセットする。
    """
    if not _namespace(ex=ns):
        _namespace(add=ns)
    _namespace(set=ns)


def _mayaNS(ns):
    u"""
    Maya API の返すネームスペース文字列から `Namespace` を得る。
    """
    # - ルートネームスペースは常に空文字列（ノード名を得た場合は : となる）。
    # - カレントネームスペースは絶対名（ノード名を得た場合は無しになる）。
    # - カレントの下位にない場合は絶対名（ノード名でも同じ）。
    # - カレントの下位の場合は相対名（ノード名でも同じ）。
    if not ns:
        return _wrapNS(':')
    elif ns.startswith(':'):
        return _wrapNS(ns)
    elif _namespace(q=True, rel=True):
        x = _namespaceInfo(cur=True, an=True)
        return _wrapNS((x if x == ':' else (x + ':')) + ns)
    else:
        return _wrapNS(':' + ns)

_wrapNS = partial(_str_new, Namespace)  #: `str` をそのまま `Namespace` にする。

