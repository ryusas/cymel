# -*- coding: utf-8 -*-
u"""
MELグローバル変数ラッパー。
"""
from ..pyutils import Singleton
import maya.mel as mel

__all__ = ['MelVar', 'melvar']

_mel_eval = mel.eval


#------------------------------------------------------------------------------
class MelVar(object):
    u"""
    MELグローバル変数ラッパークラス。

    `dict` のような振る舞いをする。
    唯一のインスタンス `melvar` が生成済み。

    参照のみが可能で、セットや削除はサポートされない。
    """
    __metaclass__ = Singleton

    def __contains__(self, key):
        return ('$' + key) in _mel_eval('env()')

    def has_key(self, key):
        return ('$' + key) in _mel_eval('env()')

    def __len__(self):
        return len(_mel_eval('env()'))

    def __iter__(self):
        for k in _mel_eval('env()'):
            yield k[1:]

    def __getitem__(self, key):
        try:
            return _mel_eval('$%s=$%s' % (key, key))
        except RuntimeError:
            raise KeyError(key)

    def __setitem__(self, key, val):
        raise TypeError('setter is not surported')

    def __delitem__(self, key):
        raise TypeError('deleter is not surported')

    def keys(self):
        for k in _mel_eval('env()'):
            yield k[1:]

    def values(self):
        for k in _mel_eval('env()'):
            yield _mel_eval('%s=%s' % (k, k))

    def items(self):
        for k in _mel_eval('env()'):
            yield k[1:], _mel_eval('%s=%s' % (k, k))

    def get(self, key, default=None):
        try:
            return _mel_eval('$%s=$%s' % (key, key))
        except RuntimeError:
            return default

melvar = MelVar()  #: `MelVar` の唯一のインスタンス。

