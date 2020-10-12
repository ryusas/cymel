# -*- coding: utf-8 -*-
u"""
Mayaネームスペース。
"""
from ..common import *
from .utils import correctNodeNameNS
from ..pyutils import iterTreeBreadthFirst, iterTreeDepthFirst

__all__ = ['Namespace']

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

    def setCurrent(self):
        u"""
        ネームスペースをカレントにする。存在しない場合は追加される。
        """
        _setCurrentNS(self)

    def isCurrent(self):
        u"""
        ネームスペースがカレントかどうか。
        """
        return _str_eq(self, _namespaceInfo(cur=True, an=True))

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

    @classmethod
    def current(cls):
        u"""
        カレントネームスペースを得る。

        :rtype: `Namespace`
        """
        return _str_new(cls, _namespaceInfo(cur=True, an=True))


#------------------------------------------------------------------------------
def _Namespace_ls(self, pattern='*', **kwargs):
    return [_CyObject(x) for x in _ls(self + pattern, **kwargs)]


def _correctNS(ns):
    ns = correctNodeNameNS(ns)
    if ns.startswith(':'):
        return ns
    elif ns:
        c = _namespaceInfo(cur=True, an=True)
        return (c if c == ':' else (c + ':')) + ns
    else:
        return _namespaceInfo(cur=True, an=True)


def _setCurrentNS(ns):
    if not _namespace(ex=ns):
        _namespace(add=ns)
    _namespace(set=ns)

