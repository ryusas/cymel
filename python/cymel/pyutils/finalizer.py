# -*- coding: utf-8 -*-
u"""
任意のオブジェクトが破棄されたときに呼び出されるファイナライザ機能。

クラスの特殊メソッド __del__ には以下の問題がある。

* __del__ 中の例外は補足できない。
* インタプリタが終了する時に呼ばれる事は保証されない。
* 循環参照がある場合で且つ __del__ が在ると解放されなくなる。
  （循環参照があると `gc` は __del__ を呼び出す適切なタイミングを保証出来なくなる為）

.. note::
    __del__ が在ると循環参照の状況で解放されなくなる問題は
    python 3.4 以降（ :pep:`442` ）で解決されている。
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from weakref import ref as _wref
import traceback

__all__ = [
    'registerFinalizer',
    'deregisterFinalizer',
    'trackDestruction',
]


#------------------------------------------------------------------------------
def registerFinalizer(obj, proc):
    u"""
    オブジェクトが破棄された時に呼び出されるプロシージャを登録する。

    :param obj: 対象のオブジェクト。
    :param `callable` proc:
        登録するプロシージャ。
    :rtype: `int` (ファイナライザID)
    """
    r = _wref(obj, _finalizer)
    k = id(r)
    _wref_dict[k] = (r, proc)
    return k


def deregisterFinalizer(key):
    u"""
    登録済みファイナライザを削除する。

    :param `int` key: 登録時に返されたID。
    """
    del _wref_dict[key]


def _finalizer(r):
    if _wref_dict:  # モジュール削除時に None になる場合があるので。
        try:
            _wref_dict.pop(id(r))[1]()
        except:
            traceback.print_exc()

_wref_dict = {}


#------------------------------------------------------------------------------
def trackDestruction(obj, logger=None, maxChars=0):
    u"""
    ファイナライザを使って、オブジェクトの削除を簡易にログする。

    :param obj: 対象のオブジェクト。
    :param logger:
        ログ用に `str` を受け取れる任意の実行可能オブジェクト。
        省略時は print される。
    :param `int` maxChars:
        ログ出力される repr の文字数がこの数を超える場合に
        メッセージを調整する。ゼロの場合はその判定をしない。
    :rtype: `int` (ファイナライザID)
    """
    try:
        s = repr(obj)
        if maxChars:
            n = len(s)
            if n > maxChars:
                if not s.startswith('<'):
                    s = '<' + s
                s = s[:maxChars - 27] + ' ... at 0x%016X>' % id(obj)
    except:
        s = '<%s instance at 0x%016X>' % (type(obj).__name__, id(obj))

    global _TRACKER_COUNT
    _TRACKER_COUNT += 1

    if logger:
        def proc():
            global _TRACKER_COUNT
            _TRACKER_COUNT -= 1
            logger('DESTRUCT: ' + s + ' (tracking=' + str(_TRACKER_COUNT) + ')')
        logger('BEGIN_TRACK: ' + s + ' (tracking=' + str(_TRACKER_COUNT) + ')')
    else:
        def proc():
            global _TRACKER_COUNT
            _TRACKER_COUNT -= 1
            print('# DESTRUCT: ' + s + ' (tracking=' + str(_TRACKER_COUNT) + ')')
        print('# BEGIN_TRACK: ' + s + ' (tracking=' + str(_TRACKER_COUNT) + ')')

    return registerFinalizer(obj, proc)

_TRACKER_COUNT = 0

