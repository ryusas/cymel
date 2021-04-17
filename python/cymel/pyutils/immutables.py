# -*- coding: utf-8 -*-
u"""
簡易的なイミュータブル化ラッパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import types

__all__ = [
    'OPTIONAL_MUTATOR_DICT',
    'CymelImmutableError',
    'immutable',
    'immutableType',
    'ImmutableDict',
]

#------------------------------------------------------------------------------
OPTIONAL_MUTATOR_DICT = {
    list: (
        'append',
        'extend',
        'insert',
    ),
    dict: (
        'clear',
        'pop',
        'popitem',
        'setdefault',
        'update',
    ),
    set: (
        'update',
        'intersection_update',
        'difference_update',
        'symmetric_difference_update',
        'add',
        'remove',
        'discard',
        'pop',
        'clear',
    ),
}  #: クラスごとの追加ミューテーターを把握するための辞書。適切なメンテナンスが必要。


#------------------------------------------------------------------------------
class CymelImmutableError(TypeError):
    u"""
    `immutable` ラップされたオブジェクトが書き換えられた。 
    """


#------------------------------------------------------------------------------
def _makeImmutableWrapper(cls, clsname, modulename):
    u"""
    immutableラッパークラスを生成し、基本的なメソッドをオーバーライドする。
    """
    attrDict = {}

    # クラスごとに決められた追加ミューテーターを封じる。
    nameSet = set()
    for base in cls.mro()[:-1]:
        names = OPTIONAL_MUTATOR_DICT.get(base)
        if names:
            nameSet.update(names)
    for name in nameSet:
        attrDict[name] = _immutableFunc(name)

    # __特殊名__ のミューテーターを封じる。
    for name in _SPECIAL_MUTATOR_NAMES:
        if hasattr(cls, name):
            attrDict[name] = _immutableFunc(name)

    # 属性の削除を封じる。
    attrDict['__delattr__'] = _immutableFunc('__delattr__')

    # 把握しているシンプルなクラスや __init__ が無いなら、単に __setattr__ を封じる。
    if cls in _MUTABLE_BUILTIN_TYPES or cls.__init__ is _object_init:
        attrDict['__setattr__'] = _immutableFunc('__setattr__')
        attrDict['__slots__'] = tuple()   # 親方向のクラス全てで徹底されていないと意味がないが一応。

    # 把握していないクラスなら、__init__ での属性セットは許容しつつその後の __setattr__ を封じる。
    else:
        initSet = set()
        init_add = initSet.add
        init_remove = initSet.remove

        cls_init = cls.__init__
        cls_setattr = cls.__setattr__

        def __init__(self, *args, **kwargs):
            init_add(self)
            try:
                cls_init(self, *args, **kwargs)
            finally:
                init_remove(self)
        attrDict['__init__'] = __init__

        def __setattr__(self, name, val):
            if self in initSet:
                cls_setattr(self, name, val)
            else:
                raise CymelImmutableError('%s.__setattr__' % repr(self))
        attrDict['__setattr__'] = __setattr__

    # ハッシュ関数が実装されていなければ、簡単にサポートして hashable にする。
    h = getattr(cls, '__hash__', None)
    if h is None or h is _object_hash:
        # ラップするクラスインスタンス全てに一致させる。
        h = hash(cls)
        attrDict['__hash__'] = lambda s: h

    # pickle 用の __reduce__ サポート。
    # 元々 pickle 不可なら TypeError になる。
    def __reduce_ex__(self, protocol):
        res = cls.__reduce_ex__(self, protocol)
        if res[0] is cls:
            return newcls_tuple + res[1:]
        return res
    attrDict['__reduce_ex__'] = __reduce_ex__

    # クラスを生成。
    # pickle 用に __module__ 属性をセットし、モジュールにもクラスをセットする。
    attrDict['__module__'] = modulename
    newcls = type(clsname, (cls,), attrDict)
    setattr(sys.modules[modulename], clsname, newcls)
    newcls_tuple = (newcls,)
    return newcls

_object_init = object.__init__
_object_hash = object.__hash__


def _immutableFunc(name):
    u"""
    ミューテーターメソッドを封じるオーバーライドを返す。
    """
    def func(self, *args, **kwargs):
        raise CymelImmutableError('%s.%s' % (repr(self), name))
    func.__name__ = name
    return func


_SPECIAL_MUTATOR_NAMES = (
    '__set__',
    '__delete__',
    '__setitem__',
    '__delitem__',
    '__setslice__',
    '__delslice__',
    '__iadd__',
    '__isub__',
    '__imul__',
    '__idiv__',
    '__itruediv__',
    '__ifloordiv__',
    '__imod__',
    '__ipow__',
    '__ilshift__',
    '__irshift__',
    '__iand__',
    '__ixor__',
    '__ior__',
)  #: 既存クラスに存在する場合のみオーバーライドするミューテーター。

if sys.hexversion < 0x3000000:
    _LONG = long
    _BYTES = str
    _UNICODE = unicode
else:
    _LONG = int
    _BYTES = bytes
    _UNICODE = str

_MUTABLE_BUILTIN_TYPES = frozenset([
    bool, int, float, _LONG, complex,
    _BYTES, _UNICODE, list, tuple, dict,
])  #: イミュータブル化の処理を簡易化する組み込み型。
if sys.hexversion >= 0x2060000:
    _MUTABLE_BUILTIN_TYPES |= frozenset([bytearray])


#------------------------------------------------------------------------------
def immutable(type_or_obj, *args, **kwargs):
    u"""
    オブジェクトが変更不可になるラッパーを生成する。

    `immutableType` を呼び出し、
    デフォルト設定でラッパークラスを得て、
    それでラップした新規インスタンスが返される。

    .. warning:
        本機能は、変更してはならないものを
        うっかり変更してしまうミスを防ぐことを目的としており、
        絶対に変更不可能なオブジェクトを作れるわけではない。
        やろうと思えば、いくらでも抜け道を作れるだろう。

    :param type_or_obj:
        ラップするオブジェクトのクラス、又はインスタンス。
        旧スタイルのクラスは非サポート。
        インスタンスが指定された場合のラッパーの初期化引数は
        インスタンス自身となる為、コピーコンストラクタが実装
        されている場合にのみ動作する。
    :param list args:
        type_or_obj にクラスが指定された場合の初期化引数。
    :param dict kwargs:
        type_or_obj にクラスが指定された場合の初期化引数。
    :returns:
        ラッパーオブジェクト。

    >>> import cymel.main as cm
    >>> d = cm.immutable(dict, woo=1, foo=2, boo=3)  # construct a immutable dict.
    >>> d = cm.immutable({'woo':1, 'foo':2, 'boo':3})  # same result via copying.
    >>> d['foo']
    2
    >>> # d['foo'] = 9   # CymelImmutableError
    >>> isinstance(d, dict)
    True
    >>> d.__class__ is dict
    False
    >>> cm.immutable({}).__class__ is d.__class__
    True
    """
    if isinstance(type_or_obj, type):
        return immutableType(type_or_obj)(*args, **kwargs)
    else:
        return immutableType(type(type_or_obj))(type_or_obj, **kwargs)


def immutableType(cls, name=None, module=None):
    u"""
    オブジェクトが変更不可になるラッパークラスを生成する。

    .. warning:
        本機能は、変更してはならないものを
        うっかり変更してしまうミスを防ぐことを目的としており、
        絶対に変更不可能なオブジェクトを作れるわけではない。
        やろうと思えば、いくらでも抜け道を作れるだろう。

    ラッパークラスはそのクラス名とともにキャッシュされ再利用される。

    型ごとに初めて生成されたラッパークラスは、型のみをキーとしてもキャッシュされ、
    クラス名が省略された場合には任意の名前としても再利用される。

    ラッパークラスでは、オブジェクトの属性値を書き換える
    メソッドがオーバーライドされ、それらがコールされた際に
    `CymelImmutableError` が送出されるようになる。

    どのメソッドをオーバーライドすべきかは、特殊メソッドの
    有無を検査する事で自動決定されるが、
    それだけでは補い切れないクラスに関しては
    `OPTIONAL_MUTATOR_DICT` 辞書で管理している為、
    必要に応じて拡張しなければならない。

    :param `type` cls:
        イミュータブル化する元のクラス。
    :param `str` name:
        ラッパークラスの名前。
        省略時は ``'Immutable元のクラス名'`` となる。
    :param `str` module:
        ラッパークラスを提供するモジュール名。
        __module__ 属性にセットされる。
        省略時は、元のクラスの __module__ 属性を引き継ぐ。
    :rtype: `type`

    .. warning::
        name も module も省略した場合は、
        指定したクラスで最初に生成された immutable ラッパークラスが
        再利用されるため、結果的にどちらも不定となる。

    .. note::
        `OPTIONAL_MUTATOR_DICT` には、インスタンスを変更する
        メソッド名をクラスごとに列挙する必要がある。
        これは、対応させたいクラスごとに拡張する必要がある事を
        意味する。ただし、全てのメソッドについて列挙する必要が
        あるわけではない。
        `OPTIONAL_MUTATOR_DICT` をあえて拡張せずとも、
        属性の設定、削除、代入演算子などはデフォルトで封じられる。
        あえてメソッド名を列挙する必要があるのは以下のケースである。

        * 属性のメソッドを呼び出すメソッド。
        * 組み込みやバイナリモジュールで提供される型のメソッド。
    """
    # immutableラップの多重化を防ぐ。
    base = cls.mro()[1]
    existing = _immutableClsCache_get(base)
    if existing:
        if not name and not module:
            return existing
        cls = base

    else:
        existing = _immutableClsCache_get(cls)
        if existing and not name and not module:
            return existing

    key = (
        cls,
        name or 'Immutable%s' % cls.__name__,
        module or cls.__module__,
    )
    if existing:
        icls = _immutableClsCache_get(key)
        if icls:
            return icls

    icls = _makeImmutableWrapper(*key)
    _immutableClsCache[key] = icls

    if not existing:
        _immutableClsCache[cls] = icls
    return icls

_immutableClsCache = {}  #: 生成済みimmutableラッパークラスのキャッシュ。
_immutableClsCache_get = _immutableClsCache.get

ImmutableDict = immutableType(dict, 'ImmutableDict', __name__)  #: イミュータブル `dict`

