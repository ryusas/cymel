# -*- coding: utf-8 -*-
u"""
循環参照によるメモリリークが解決された `ordereddict` 。
"""
from weakref import ref as _wref
try:
    from collections import OrderedDict as _OrderedDict
except ImportError:
    from .exts.ordereddict import OrderedDict as _OrderedDict

__all__ = ['CleanOrderedDict']

_wref_dict = {}


#------------------------------------------------------------------------------
class CleanOrderedDict(_OrderedDict):
    u"""
    破棄された後の参照の後始末も行う `OrderedDict` 。

    OrderedDict には、キーにしたオブジェクトの循環参照が生じる問題がある。
    その為、 OrderedDict が破棄されても、キーにしたオブジェクトは
    ガベージコレクトされるまで破棄されなくなってしまう。

    そこで、自身が破棄された後に、
    内部で保持されていたキーの相互参照を破棄する処理を追加した。
    """
    def __init__(self, *args, **kwargs):
        _OrderedDict.__init__(self, *args, **kwargs)

        def _finalize(w):
            for node in map.itervalues():
                del node[:]
            if _wref_dict:  # モジュール削除時に None になる場合があるので。
                del _wref_dict[key]

        map = self._OrderedDict__map
        key = id(self)
        _wref_dict[key] = _wref(self, _finalize)

