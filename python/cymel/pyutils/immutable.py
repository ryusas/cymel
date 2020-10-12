# -*- coding: utf-8 -*-
u"""
簡易的なイミュータブル化ラッパー。
"""
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
def _makeImmutableWrapper(cls, clsname):
    u"""
    immutableラッパークラスを生成し、基本的なメソッドをオーバーライドする。
    """
    attrDict = {}

    # __特殊名__ のミューテーターを封じる。
    for name in _SPECIAL_MUTATOR_NAMES:
        if hasattr(cls, name):
            attrDict[name] = _immutableFunc(name)

    # クラスごとに決められた追加ミューテーターを封じる。
    for basecls in OPTIONAL_MUTATOR_DICT:
        if issubclass(cls, basecls):
            for name in OPTIONAL_MUTATOR_DICT[basecls]:
                attrDict[name] = _immutableFunc(name)

    # 属性の削除を封じる。
    attrDict['__delattr__'] = _immutableFunc('__delattr__')

    # 把握しているシンプルなクラスなら、単に __setattr__ を封じる。
    if cls in _MUTABLE_BUILTIN_TYPES:
        attrDict['__setattr__'] = _immutableFunc('__setattr__')
        attrDict['__slots__'] = tuple()   # 親方向のクラス全てで徹底されていないと意味がないが一応。

    # 把握していないクラスなら、初期化時の属性セットは許容しつつその後の __setattr__ を封じる。
    else:
        def __init__(self, *args, **kwargs):
            cls_init(self, *args, **kwargs)  # この中での __setattr__ は許す。
            self.__dict__['_cymelImmutable'] = True
        cls_init = cls.__init__
        attrDict['__init__'] = __init__

        def __setattr__(self, name, val):
            if self.__dict__.get('_cymelImmutable'):
                raise CymelImmutableError('%s.__setattr__' % repr(self))
            cls_setattr(self, name, val)
        cls_setattr = cls.__setattr__
        attrDict['__setattr__'] = __setattr__

    # ハッシュ関数が実装されていなければ、簡単にサポートして hashable にする。
    h = getattr(cls, '__hash__', None)
    if h is None or h is _OBJECT__HASH__:
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

    # クラスを生成。pickle 用にグローバルスコープにも出す。
    newcls = type(clsname, (cls,), attrDict)
    globals()[clsname] = newcls
    newcls_tuple = (newcls,)
    return newcls


def _immutableFunc(name):
    u"""
    ミューテーターメソッドを封じるオーバーライドを返す。
    """
    def func(self, *args, **kwargs):
        raise CymelImmutableError('%s.%s' % (repr(self), name))
    func.__name__ = name
    return func


_OBJECT__HASH__ = object.__hash__

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

_IS_PYTHON2 = sys.version_info[0] is 2
if _IS_PYTHON2:
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
if not _IS_PYTHON2 or sys.version_info[1] >= 6:
    _MUTABLE_BUILTIN_TYPES |= frozenset([bytearray])


#------------------------------------------------------------------------------
def immutable(type_or_obj, *args, **kwargs):
    u"""
    イミュータブルなオブジェクトを生成する（完璧ではない）。

    `immutableType` を呼び出し、
    デフォルト名のラッパークラスを得て、
    それでラップした新規インスタンスが返される。

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
        cls = type_or_obj
    else:
        if _IS_PYTHON2 and isinstance(type_or_obj, types.ClassType):
            raise TypeError('old style class is not supported.')
        cls = type(type_or_obj)
        args = [type_or_obj]
    return immutableType(cls)(*args, **kwargs)


def immutableType(cls, name=None):
    u"""
    イミュータブル化されたラッパークラスを得る（完璧ではない）。

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
        省略時は ``'_Immutable_元のクラス名'`` となるが、
        最初にその型で生成されたキャッシュがあれば再利用される。
    :rtype: `type`

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
    if name:
        key = (cls, name)
    else:
        newcls = _immutable_class_cache.get(cls)
        if newcls:
            return newcls
        key = (cls, '_Immutable_%s' % cls.__name__)

    newcls = _immutable_class_cache.get(key)
    if newcls:
        return newcls

    newcls = _makeImmutableWrapper(*key)
    _immutable_class_cache[key] = newcls
    if not name or cls not in _immutable_class_cache:
        _immutable_class_cache[cls] = newcls
    return newcls

_immutable_class_cache = {}  #: 生成済みimmutableラッパークラスのキャッシュ。

ImmutableDict = immutableType(dict, 'ImmutableDict')  #: イミュータブル `dict`

