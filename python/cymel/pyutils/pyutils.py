# -*- coding: utf-8 -*-
u"""
Mayaに依存しない諸機能。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys as _sys
if _sys.hexversion < 0x2060000:
    raise EnvironmentError('unsupported python version')

import os as _os
import os.path as _os_path
import types as _types
import re as _re
from weakref import ref as _wref
from tempfile import gettempdir as _gettempdir
from random import choice as _choice
from .immutables import ImmutableDict as _ImmutableDict
from ..constants import AVOID_ZERO_DIV_PRECISION, PI

#------------------------------------------------------------------------------
try:
    from future.utils import with_metaclass
except ImportError:
    #try:
    #    from six import with_metaclass
    #except ImportError:
    def with_metaclass(meta, *bases):
        u"""
        Function from jinja2/_compat.py. License: BSD.
        """
        class metaclass(meta):
            __call__ = type.__call__
            __init__ = type.__init__

            def __new__(cls, name, this_bases, d):
                if this_bases is None:
                    return type.__new__(cls, name, (), d)
                return meta(name, bases, d)
        return metaclass('temporary_class', None, {})


#------------------------------------------------------------------------------
_os_path_exists = _os_path.exists
_os_path_join = _os_path.join
_os_path_normpath = _os_path.normpath
_os_path_normcase = _os_path.normcase
#_os_path_split = _os_path.split
#_os_path_splitext = _os_path.splitext
#_os_path_relpath = _os_path.relpath
#_os_path_dirname = _os_path.dirname

_wref_dict = {}

#------------------------------------------------------------------------------
EMPTY_TUPLE = tuple()  # 空 `tuple`
EMPTY_SET = frozenset()  # 空 `frozenset`
EMPTY_DICT = _ImmutableDict()  # 空 `.ImmutableDict`

LIST_OR_TUPLE = (list, tuple)

#------------------------------------------------------------------------------
MAXINT32 = int(2**31 - 1)  #: 32bit符号付き整数の最大値。Maya の sys.maxint はこれ（py3 で廃止）。
MAXINT64 = int(2**63 - 1)  #: 64bit符号付き整数の最大値。Maya の sys.maxsize はこれ。

#------------------------------------------------------------------------------
IS_WINDOWS = _sys.platform == 'win32'  #: OS が Windows かどうか。
if IS_WINDOWS:
    USER_DOC_PATH = _os_path_join(_os.environ['USERPROFILE'], 'Documents')  #: ユーザードキュメントディレクトリ。Unix系ではホーム、Windowsではマイドキュメントとしている。
else:
    USER_DOC_PATH = _os.environ['HOME']  #: ユーザードキュメントディレクトリ。Unix 系ではホーム、Windows ではマイドキュメントとしている。

#------------------------------------------------------------------------------
IS_PYTHON2 = _sys.version_info[0] == 2
IS_PYTHON3 = _sys.version_info[0] == 3

if IS_PYTHON2:
    BYTES = str
    UNICODE = unicode
    BASESTR = basestring  #: Python 2 と 3 の差を吸収する文字列型チェック用。
    LONG = long  #: Python 2 と 3 の差を吸収する長整数型チェック用。

    RePattern = _re._pattern_type  #: 正規表現パターン型。

    lrange = range  #: list を返す range (Python 2 の標準)
    xrange = xrange  #: イテレータによる range

    lzip = zip  #: list を返す zip (Python 2 の標準)
    lmap = map  #: list を返す map (Python 2 の標準)
    lfilter = filter  #: list を返す filter (Python 2 の標準)
    from itertools import izip, imap, ifilter
    if _sys.hexversion >= 0x2060000:
        from itertools import izip_longest

    # 辞書から list を取得。
    dict_get_keys = lambda d: d.keys()  #: `dict` から keys リストを得る。
    dict_get_values = lambda d: d.values()  #: `dict` から values リストを得る。
    dict_get_items = lambda d: d.items()  #: `dict` から items リストを得る。

    # 辞書イテレータ。next() が使え、一度しかイテレーションできない。インデックスアクセスはできない。
    dict_iterkeys = lambda d: d.iterkeys()  #: `dict` から keys イテレータを得る。
    dict_itervalues = lambda d: d.itervalues()  #: `dict` から values イテレータを得る。
    dict_iteritems = lambda d: d.iteritems()  #: `dict` から items イテレータを得る。

    # py2.7 以降は辞書ビューを使える。繰り返しイテレーションできる。next() やインデックスアクセスはできない。
    if hasattr(dict, 'viewkeys'):
        dict_keys = lambda d: d.viewkeys()  #: `dict` から dict_keys を得る。
        dict_values = lambda d: d.viewvalues()  #: `dict` から dict_values を得る。
        dict_items = lambda d: d.viewitems()  #: `dict` から dict_items を得る。
    else:
        dict_keys = None
        dict_values = None
        dict_items = None

    reduce = reduce
    execfile = execfile

    fround = round  #: 常にfloat型を返すround。ただし、py2は四捨五入、py3は偶数への丸め(bankers' rounding)という違いはある。

    def round(f, ndigits=None):
        u"""
        py3 標準の round 。ndigits がデフォルト(None)だと `int` 型を返す。ただし、py2は四捨五入、py3は偶数への丸め(bankers' rounding)という違いはある。
        """
        return int(fround(f)) if ndigits is None else fround(f, ndigits)

    def ucToStrList(xx):
        u"""
        `unicode` の可能性のある `list` をすべて `str` にする。
        """
        return [str(x) for x in xx]

else:
    BYTES = bytes
    UNICODE = str
    BASESTR = str  #: Python 2 と 3 の差を吸収する文字列型チェック用。
    LONG = int  #: Python 2 と 3 の差を吸収する長整数型チェック用。

    RePattern = _re.Pattern  #: 正規表現パターン型。

    lrange = lambda *a: list(range(*a))  # list を返す range (Python 3 には無い)
    xrange = range  #: イテレータによる range (Python 3 の標準)

    lzip = lambda *a: list(zip(*a))  #: list を返す zip (Python 3 には無い)
    izip = zip
    lmap = lambda *a: list(map(*a))  #: list を返す map (Python 3 には無い)
    imap = map
    lfilter = lambda *a: list(filter(*a))  #: list を返す filter (Python 3 には無い)
    ifilter = filter
    from itertools import zip_longest as izip_longest

    # 辞書から list を取得。
    dict_get_keys = lambda d: list(d)  #: `dict` から keys リストを得る。
    dict_get_values = lambda d: list(d.values())  #: `dict` から values リストを得る。
    dict_get_items = lambda d: list(d.items())  #: `dict` から items リストを得る。

    # 辞書イテレータ。next() が使え、一度しかイテレーションできない。インデックスアクセスはできない。
    dict_iterkeys = lambda d: d.keys().__iter__()  #: `dict` から keys イテレータを得る。
    dict_itervalues = lambda d: d.values().__iter__()  #: `dict` から values イテレータを得る。
    dict_iteritems = lambda d: d.items().__iter__()  #: `dict` から items イテレータを得る。

    # py3 では通常操作が辞書ビューになった。繰り返しイテレーションできる。next() やインデックスアクセスはできない。
    dict_keys = lambda d: d.keys()  #: `dict` から dict_keys を得る。
    dict_values = lambda d: d.values()  #: `dict` から dict_values を得る。
    dict_items = lambda d: d.items()  #: `dict` から dict_items を得る。

    from functools import reduce

    def execfile(fname, globals=None, locals=None):
        if globals is None:
            globals = {'__name__': '__main__'}
        exec(compile(open(fname, 'rb').read(), fname, 'exec'), globals, locals)

    def fround(f, ndigits=0):
        u"""
        常に `float` 型を返す `round` 。ただし、py2は四捨五入、py3は偶数への丸め(bankers' rounding)という違いはある。
        """
        return round(f, ndigits or 0)

    round = round  #: py3 標準の round 。ndigits がデフォルト(None)だと `int` 型を返す。ただし、py2は四捨五入、py3は偶数への丸め(bankers' rounding)という違いはある。

    def ucToStrList(xx):
        u"""
        何もしない。
        """
        return xx


#------------------------------------------------------------------------------
def donothing(*a):
    u"""
    何もしない。
    """


def gettrue(*a):
    u"""
    常に真。
    """
    return True


#------------------------------------------------------------------------------
class Singleton(type):
    u"""
    シングルトンクラスを作る為のメタクラス。

    その型のインスタンスは1つしか生成されなくなる。

    インスタンスが生成されようとする時、同じ型のインスタンスが
    既に存在していればそれが返されるだけである。
    生成時の引数内容の違いも考慮されずに流用される点には注意が必要。

    >>> import cymel.main as cm
    >>> class Foo(cm.with_metaclass(cm.Singleton, object)):
    ...     def __init__(self, v):
    ...         self._v = v
    ...     def __repr__(self):
    ...         return '%s(%s)' % (self.__class__.__name__, repr(self._v))
    ...
    >>> class Bar(Foo):
    ...     pass
    ...
    >>> a,b,c,d = Foo(1), Foo(2), Bar(3), Bar(4)
    >>> a,b,c,d
    (Foo(1), Foo(1), Bar(3), Bar(3))
    >>> a is b
    True
    >>> a is c
    False
    >>> c is d
    True
    >>> del a,b,c,d
    >>> b = Foo(2)
    >>> b
    Foo(2)
    >>> del b
    """
    def __new__(metacls, clsname, bases, attrs):
        cls = type.__new__(metacls, clsname, bases, attrs)
        cls._singleton_ref = None
        return cls

    def __call__(cls, *args, **kwargs):
        ref = cls._singleton_ref
        if ref:
            ref = ref()
            if ref is not None:
                return ref
        ref = type.__call__(cls, *args, **kwargs)

        def _finalize(ref):
            cls._singleton_ref = None
            if _wref_dict:  # モジュール削除時に None になる場合があるので。
                del _wref_dict[key]

        # 弱参照に簡単にアクセス出来るようにする為に参照を保持。
        key = id(cls)
        cls._singleton_ref = _wref(ref, _finalize)
        _wref_dict[key] = cls._singleton_ref  # 弱参照をクラス外で保持しないとファイナライザが呼ばれない場合がある。
        return ref


#------------------------------------------------------------------------------
def parentClasses(cls):
    u"""
    親クラスのリストを得る。

    :type cls: `type`
    :param cls: クラス。
    :rtype: `list`
    """
    mro = cls.mro()
    supSet = set(mro[1].mro())
    n = len(mro)
    i = 2
    while i < n:
        c = mro[i]
        if c in supSet:
            break
        supSet.update(c.mro())
        i += 1
    return mro[1:i]


#------------------------------------------------------------------------------
def avoidZeroDiv(v, pre=AVOID_ZERO_DIV_PRECISION):
    u"""
    Maya を模倣したゼロ割を防ぐ為の分母を得る。

    Maya では scale=0 を設定しても matrix が特異値とならないように
    0.0 は 1.e-12 くらいでリミットして保持するようなので、それを意識
    したリミットを掛けた値を返す。

    :param v: チェックする値。
    :param pre: 最小値。デフォルトは `AVOID_ZERO_DIV_PRECISION` 。
    :rtype: リミットを適用した値。
    """

    #if v < 0.:
    #    pre = -pre
    #    return pre if v > pre else v
    #else:
    #    return pre if v < pre else v

    # fix for Python 2.4
    if v < 0.:
        pre = -pre
        if v > pre:
            return pre
        else:
            return v
    else:
        if v < pre:
            return pre
        else:
            return v


def boundAngle(a):
    u"""
    角度を±πの範囲におさめる。
    """
    a %= _2PI
    if a < _nPI:
        a += _2PI
    elif a > PI:
        a -= _2PI
    return a

_nPI = -PI
_2PI = 2. * PI


#------------------------------------------------------------------------------
def _normPath(path):
    return _os_path_normpath(_os_path_normcase(path))


def insertEnvPath(path, name, index=-1, noCheck=False, noUpdate=False):
    u"""
    様々なパス環境変数にパスを追加する。

    パスが存在せず追加されなかったら 0 、
    既にリストに含まれていたら 1 、
    新規に追加されたなら 2 が返される。

    :param `str` path: 追加するパス。
    :param `str` name: 環境変数名。
    :param `int` index:
        追加する位置。負数であれば末尾に追加、
        そうでなければこの位置の手前に挿入される。
    :param `bool` noCheck:
        パスの存在の有無をチェックしない。
        デフォルトでは、実際に存在しないパスは追加されない。
    :param `bool` noUpdate:
        パスが既に含まれていたら更新しない。
        デフォルトでは、既にリストに含まれているパスなら、
        一旦それを削除してから追加し直される。
    :rtype: `int`
    """
    result = 0
    if noCheck or _os_path_exists(path):
        npath = _normPath(path)
        if name in _os.environ:
            paths = _os.environ[name].split(_os.pathsep)
        else:
            paths = []
        normPaths = [_normPath(s) for s in paths]
        try:
            i = normPaths.index(npath)
            if noUpdate:
                return 1
            paths.pop(i)
            result = 1
        except:
            result = 2
        if index < 0:
            paths.append(path)
        else:
            paths.insert(index, path)
        _os.environ[name] = _os.pathsep.join(paths)
    return result


def insertSysPath(path, index=-1, noCheck=False):
    u"""
    `sys.path` にパスを追加する。

    パスが存在せず追加されなかったら 0 、
    既にリストに含まれていて追加し直されたら 1 、
    新規に追加されたなら 2 が返される。

    :param `str` path: 追加するパス。
    :param `int` index:
        追加する位置。負数であれば末尾に追加、
        そうでなければこの位置の手前に挿入される。
    :param `bool` noCheck:
        パスの存在の有無をチェックしない。
        デフォルトでは、実際に存在しないパスは追加されない。
    :param `bool` noUpdate:
        パスが既に含まれていたら更新しない。
        デフォルトでは、既にリストに含まれているパスなら、
        一旦それを削除してから追加し直される。
    :rtype: `int`
    """
    result = 0
    if noCheck or _os_path_exists(path):
        npath = _normPath(path)
        normPaths = [_normPath(s) for s in _sys.path]
        try:
            i = normPaths.index(npath)
            if noUpdate:
                return 1
            _sys.path.pop(i)
            result = 1
        except:
            result = 2
        if index < 0:
            _sys.path.append(path)
        else:
            _sys.path.insert(index, path)
    return result


#------------------------------------------------------------------------------
def incrementName(name):
    u"""
    名前の末尾の数字をインクリメントする。

    >>> import cymel.main as cm
    >>> cm.incrementName('hoge')
    'hoge1'
    >>> cm.incrementName('hoge1')
    'hoge2'
    """
    m = _RE_TAIL_NUMBER_search(name)
    if m:
        i = m.group(0)
        return name[:-len(i)] + str(int(i) + 1)
    return name + '1'

_RE_TAIL_NUMBER_search = _re.compile(r'\d+$').search


def convIntToBaseN(i, chars='0123456789abcdef'):
    u"""
    整数を N 進数表記の文字列に変換する。

    :param `str` chars:
        桁の文字を 0～N-1 まで並べた文字列。
        デフォルトは小文字の16進数。
    :rtype: `str`

    >>> import cymel.main as cm
    >>> convIntToBaseN(255)
    'ff'
    >>> convIntToBaseN(4096)
    '1000'
    """
    num = len(chars)
    r = i % num
    i //= num
    s = chars[r]
    while i:
        r = i % num
        i //= num
        s = chars[r] + s
    return s


def assembleCodeToCallFunction(name, *args, **kwargs):
    u"""
    関数呼び出し用のコード文字列を生成する。

    :param `str` name: 関数名。
    :param iterable args: 引数リスト。
    :param `dict` kwargs: キーワード引数辞書。
    :rtype: `str`
    """
    if args:
        args = repr(args)
        if args[-2] == ',':
            args = [args[1:-2]]
        else:
            args = [args[1:-1]]
        args.extend([(str(k) + '=' + repr(v)) for k, v in kwargs.items()])
    else:
        args = [(str(k) + '=' + repr(v)) for k, v in kwargs.items()]
    return name + '(' + ', '.join(args) + ')'


#------------------------------------------------------------------------------
def getTempFilename(
    suffix='', prefix='tmp', dir=None, n=5,
    chars='abcdefghijklmnopqrstuvwxyz0123456789'
):
    u"""
    任意に使えるテンポラリファイル名をフルパスで得る。

    :param `str` prefix: ファイル名に付ける任意の接頭辞を指定する。
    :param `str` suffix: ファイル名に付ける任意の接尾辞を指定する。
    :param `str` dir: ファイルを生成するディレクトリパスを指定する。
    :param `int` n: ランダムに決まる部分の文字数を指定する。
    :param `str` chars: ランダムに決まる部分に使用される文字。
    :rtype: `str`
    """
    if dir is None:
        dir = _gettempdir()

    namer = lambda: ''.join([_choice(chars) for i in range(n)])

    name = _os_path_join(dir, prefix + namer() + suffix)
    while _os_path_exists(name):
        name = _os_path_join(dir, prefix + namer() + suffix)
    return name


#------------------------------------------------------------------------------
def iterTreeBreadthFirst(nodes, proc):
    u"""
    木を幅優先反復する。

    :param `iterable` nodes: 基点ノードリスト。
    :param `callable` proc: 子ノード群を得るプロシージャ。

    .. warning::
        循環していると無限ループになる。
    """
    while nodes:
        queue = nodes
        nodes = []
        for node in queue:
            yield node
            nodes.extend(proc(node))


def iterTreeDepthFirst(nodes, proc):
    u"""
    木を深さ優先反復する。

    :param `iterable` nodes: 基点ノードリスト。
    :param `callable` proc: 子ノード群を得るプロシージャ。

    .. warning::
        循環していると無限ループになる。
    """
    for node in nodes:
        yield node
        for node in iterTreeDepthFirst(proc(node), proc):
            yield node

