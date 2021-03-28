# -*- coding: utf-8 -*-
u"""
Mayaに依存しない諸機能。
"""
import sys as _sys
import os as _os
import os.path as _os_path
import types as _types
import re as _re
from weakref import ref as _wref
from tempfile import gettempdir as _gettempdir
from random import Random as _Random
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
MAXINT32 = int(2**31 - 1)  #: 32bit符号付き整数の最大値。Maya の python 2.x の sys.maxint はこれ。
MAXINT64 = int(2**63 - 1)  #: 64bit符号付き整数の最大値。Maya の python 3.x の sys.maxsize はこれ。

#------------------------------------------------------------------------------
IS_WINDOWS = _sys.platform == 'win32'  #: OS が Windows かどうか。
if IS_WINDOWS:
    #IS_X64 = _os.environ['PROCESSOR_ARCHITECTURE'] == 'AMD64'  #: 64bit OS かどうか。
    ENV_SEPARATOR = ';'  #: 環境変数などで使用する設定値の区切り文字。Unix 系ではコロン、Windows ではセミコロンとしている。
    #LD_PATH_VARNAME = 'PATH'  #: ダイナミックライブラリの検索パスを定義する環境変数名。Unix 系では LD_LIBRARY_PATH、Windows では PATH としている。
    USER_DOC_PATH = _os_path_join(_os.environ['USERPROFILE'], 'Documents')  #: ユーザードキュメントディレクトリ。Unix系ではホーム、Windowsではマイドキュメントとしている。
    #RE_PATH_DELIMITTER = re.compile(r'[\\/]')  #: パス区切り文字の正規表現。
else:
    # NOTE: Windows Python の場合は x64 でも int サイズが変わらない為、この手段は使えない。
    #IS_X64 = hash('a') == 12416037344  #: 64bit OS かどうか。
    ENV_SEPARATOR = ':'  #: 環境変数などで使用する設定値の区切り文字。Unix 系ではコロン、Windows ではセミコロンとしている。
    #LD_PATH_VARNAME = 'LD_LIBRARY_PATH'  #: ダイナミックライブラリの検索パスを定義する環境変数名。Unix 系では LD_LIBRARY_PATH、Windows では PATH としている。
    USER_DOC_PATH = _os.environ['HOME']  #: ユーザードキュメントディレクトリ。Unix 系ではホーム、Windows ではマイドキュメントとしている。
    #RE_PATH_DELIMITTER = re.compile(r'/')  #: パス区切り文字の正規表現。

#------------------------------------------------------------------------------
IS_PYTHON2 = _sys.version_info[0] is 2
IS_PYTHON3 = _sys.version_info[0] is 3
if (not IS_PYTHON2 and not IS_PYTHON3) or (IS_PYTHON2 and _sys.version_info[1] < 6):
    raise EnvironmentError('unsupported python version')

if IS_PYTHON2:
    BASESTR = basestring  #: Python 2 と 3 の差を吸収する文字列型チェック用。
    BYTES = str
    UNICODE = unicode
    LONG = long  #: Python 2 と 3 の差を吸収する長整数型チェック用。

    RePattern = _re._pattern_type  #: 正規表現パターン型。

    lrange = range  #: list を返す range (Python 2 の標準)
    xrange = xrange  #: イテレータによる range

    lzip = zip  #: list を返す zip (Python 2 の標準)
    from itertools import izip  #: イテレータによる zip
    from itertools import izip_longest

    dict_get_items = lambda d: d.items()  #: `dict` から items list を得る。
    dict_get_keys = lambda d: d.keys()  #: `dict` から keys list を得る。
    dict_get_values = lambda d: d.values()  #: `dict` から values list を得る。

    im_func = lambda m: m.im_func  #: インスタンスメソッドから func を得る。ビルトインクラスのメソッドだと AttributeError になる。

    reduce = reduce
    execfile = execfile

    def ucToStrList(xx):
        u"""
        `unicode` の可能性のある `list` をすべて `str` にする。
        """
        return [str(x) for x in xx]

else:
    BASESTR = str  #: Python 2 と 3 の差を吸収する文字列型チェック用。
    BYTES = bytes
    UNICODE = str
    LONG = int  #: Python 2 と 3 の差を吸収する長整数型チェック用。

    RePattern = _re.Pattern  #: 正規表現パターン型。

    lrange = lambda *a: list(range(*a))  # list を返す range (Python 3 には無い)
    xrange = range  #: イテレータによる range (Python 3 の標準)

    lzip = lambda *a: list(zip(*a))  #: list を返す zip (Python 3 には無い)
    izip = zip  #: イテレータによる zip
    from itertools import zip_longest as izip_longest

    dict_get_items = lambda d: list(d.items())  #: `dict` から items list を得る。
    dict_get_keys = lambda d: list(d)  #: `dict` から keys list を得る。
    dict_get_values = lambda d: list(d.values())  #: `dict` から values list を得る。

    im_func = lambda m: m.__func__  #: インスタンスメソッドから func を得る。ビルトインクラスのメソッドだと AttributeError になる。

    from functools import reduce

    def execfile(fname, globals=None, locals=None):
        if globals is None:
            globals = {}
        globals.update({
            '__file__': fname,
            '__name__': '__main__',
        })
        with open(fname, 'rb') as f:
            exec(compile(f.read(), fname, 'exec'), globals, locals)

    def ucToStrList(xx):
        u"""
        何もしない。
        """
        return xx


def im_self(m):
    u"""
    インスタンスメソッドから self を得る。
    """
    # m.im_self だと py3 で使えず、且つ py2 でもビルトインメソッドでは使えない。
    return m.__self__


def im_class(m):
    u"""
    インスタンスメソッドから type を得る。
    """
    # m.im_class だと py3 で使えず、且つ py2 でもビルトインメソッドでは使えない。
    return m.__self__.__class__


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
            paths = _os.environ[name].split(ENV_SEPARATOR)
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
        _os.environ[name] = ENV_SEPARATOR.join(paths)
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
    chars='abcdefghijklmnopqrstuvwxyz0123456789_'
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

    global _tempFileNamer
    if not _tempFileNamer:
        _tempFileNamer = _makeTempFileNamer()

    name = _os_path_join(dir, prefix + _tempFileNamer(n, chars) + suffix)
    while _os_path_exists(name):
        name = _os_path_join(dir, prefix + _tempFileNamer(n, chars) + suffix)
    return name

_tempFileNamer = None


def _makeTempFileNamer(seed=None):
    def proc(n, chars):
        return ''.join([choose(chars) for i in range(n)])
    choose = _Random(seed).choice
    return proc


#------------------------------------------------------------------------------
def iterTreeBreadthFirst(nodes, method):
    u"""
    木を幅優先反復する。

    :param `iterable` nodes: 基点ノードリスト。
    :param `str` method: 子ノード群を得るメソッド名。

    .. warning::
        循環していると無限ループになる。
    """
    while nodes:
        queue = nodes
        nodes = []
        for node in queue:
            yield node
            getter = getattr(node, method, None)
            if getter:
                for neighbor in getter():
                    nodes.append(neighbor)


def iterTreeDepthFirst(nodes, method):
    u"""
    木を深さ優先反復する。

    :param `iterable` nodes: 基点ノードリスト。
    :param `str` method: 子ノード群を得るメソッド名。

    .. warning::
        循環していると無限ループになる。
    """
    for node in nodes:
        yield node
        getter = getattr(node, method, None)
        if getter:
            for node in iterTreeDepthFirst(getter(), method):
                yield node

