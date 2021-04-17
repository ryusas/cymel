# -*- coding: utf-8 -*-
u"""
循環参照によるメモリリークが解決された `ordereddict` 。
"""
import sys as _sys

__all__ = ['CleanOrderedDict']


#------------------------------------------------------------------------------
if _sys.hexversion < 0x3060000:
    try:
        from collections import OrderedDict as _OrderedDict
    except ImportError:
        from .exts.ordereddict import OrderedDict as _OrderedDict
    from weakref import ref as _wref

    if _sys.hexversion < 0x3000000:
        _dict_itervalues = lambda d: d.itervalues()
    else:
        _dict_itervalues = lambda d: d.values()

    class CleanOrderedDict(_OrderedDict):
        u"""
        破棄された後の参照の後始末も行う `OrderedDict` 。

        OrderedDict では、キーにしたオブジェクトの循環参照が生じており、
        値を保持したまま OrderedDict インスタンスが破棄されると、
        キーはガベージコレクトされるまで破棄されなくなってしまう。

        そこで、自身が破棄された後に、
        内部で保持されていたキーの相互参照を破棄する処理を追加した。
        """
        def __init__(self, *args, **kwargs):
            _OrderedDict.__init__(self, *args, **kwargs)

            def _finalize(w):
                for node in _dict_itervalues(map):
                    del node[:]
                if _wref_dict:  # モジュール削除時に None になる場合があるので。
                    del _wref_dict[key]

            map = self._OrderedDict__map
            key = id(self)
            _wref_dict[key] = _wref(self, _finalize)

    _wref_dict = {}

else:
    CleanOrderedDict = dict  #: `dict` の別名。Python3.6 以降では dict が OrderedDict 相当になり、キーの循環参照問題も解決されている。

