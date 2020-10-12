# -*- coding: utf-8 -*-
u"""
:mayacmd:`optionVar` ラッパー。
"""
from ..common import *

__all__ = ['OptionVar']

_optionVar = cmds.optionVar

_STR_NONE = '___None___'
_STR_TRUE = '___True___'
_STR_FALSE = '___False___'
_IntTypes = (int, long)


#------------------------------------------------------------------------------
class OptionVar(object):
    u"""
    :mayacmd:`optionVar` ラッパークラス。

    `dict` のような振る舞いをする。

    特別な対応をせずに、以下のタイプの値を扱うことができる。

    * `None` (文字列 '___None___' として保存される)
    * `bool` (文字列 '___True___' か '___False___' として保存される）
    * `int`
    * `float`
    * `str`
    * `int` シーケンス（型の混在は不可）
    * `float` シーケンス（型の混在は不可）
    * `str` シーケンス（型の混在は不可）
    * 空のシーケンス

    さらに、 `setTranslator` で :mayacmd:`optionVar` に
    セットする値との変換器をセットすることで、
    あらゆるタイプの値を扱えるようにすることも可能。

    任意の接頭辞を指定することで、
    :mayacmd:`optionVar` の保存と読み出し時に
    接頭辞が付加されるとともに、
    辞書として扱われる範囲を限定することができる。

    また、各値のデフォルト値を指定することも可能。
    デフォルト値が指定されていれば、
    実際に値が保存されていなくても値を持つようになり、
    :mayacmd:`optionVar` の肥大化が抑制される。

    .. note::
        ツールなどの開発時は、
        そのツール固有の接頭辞を指定し、
        一通りのデフォルト値を指定することで、
        そのツールのオプション辞書とする使い方を推奨する。
    """
    def __init__(self, prefix='', defaults=EMPTY_DICT):
        u"""
        初期化。

        :param `str` prefix:
            管理する変数名に付ける任意の接頭辞。
        :param `dict` dic:
            登録するデフォルト値の辞書。
        """
        self._prefix = prefix
        self._defaultDict = {}
        self._translators = {}
        if defaults:
            self.setDefaults(defaults)

    def __repr__(self):
        return "<%s '%s'>" % (type(self).__name__, self._prefix)

    def __contains__(self, key):
        return key in self._defaultDict or _optionVar(ex=self._prefix + key)

    def has_key(self, key):
        return key in self._defaultDict or _optionVar(ex=self._prefix + key)

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        for k in self.keys():
            yield k

    def __getitem__(self, key):
        k = self._prefix + key
        if _optionVar(ex=k):
            return self._evalVal(key, _optionVar(q=k))
        return self._defaultDict[key]

    def __setitem__(self, key, val):
        k = self._prefix + key
        if key in self._defaultDict:
            # 0, 1 はそのまま False, True と比較可能。
            if self._defaultDict[key] == val:
                _optionVar(rm=k)
                return

        trans = self._translators.get(key)
        if trans:
            val = trans[1](val)

        if val is None:
            _optionVar(sv=(k, _STR_NONE))
        elif val is True:
            _optionVar(sv=(k, _STR_TRUE))
        elif val is False:
            _optionVar(sv=(k, _STR_FALSE))
        elif isinstance(val, BASESTR):
            _optionVar(sv=(k, val))
        elif isinstance(val, float):
            _optionVar(fv=(k, val))
        elif isinstance(val, _IntTypes):
            _optionVar(iv=(k, val))

        elif hasattr(val, '__getitem__') or hasattr(val, '__iter__'):
            if val:
                v = val[0]
                if isinstance(v, BASESTR):
                    _optionVar(rm=k)
                    for v in val:
                        _optionVar(sva=(k, v))
                elif isinstance(v, float):
                    _optionVar(rm=k)
                    for v in val:
                        _optionVar(fva=(k, v))
                elif isinstance(v, _IntTypes):
                    _optionVar(rm=k)
                    for v in val:
                        _optionVar(iva=(k, v))
                else:
                    raise TypeError('unsupported value type in the sequence: ' + str(type(v)))
            else:
                _optionVar(rm=k)
                _optionVar(sva=(k, ''))
                _optionVar(ca=k)

        else:
            raise TypeError('unsupported value type: ' + str(type(val)))

    def __delitem__(self, key):
        notFound = True
        if key in self._defaultDict:
            del self._defaultDict[key]
            notFound = False

        k = self._prefix + key
        if _optionVar(ex=k):
            _optionVar(rm=k)
            notFound = False

        if notFound:
            raise KeyError(key)

    def prefix(self):
        u"""
        接頭辞を得る。

        :rtype: `str`
        """
        return self._prefix

    def get(self, key, default=None):
        u"""
        キーを指定して値を得る。

        :param key: キー。
        :returns: 格納されている値かデフォルト値、又は指定値。
        """
        k = self._prefix + key
        if _optionVar(ex=k):
            return self._evalVal(key, _optionVar(q=k))
        return self._defaultDict.get(key, default)

    def pop(self, key, *args):
        u"""
        値を取得して削除する。

        デフォルト値がセットされたキーの場合は、
        デフォルト値も削除される。

        :param key: キー。
        :returns: 格納されていた値かデフォルト値、又は指定値。
        """
        val = self
        if key in self._defaultDict:
            val = self._defaultDict.pop(key)

        k = self._prefix + key
        if _optionVar(ex=k):
            val = self._evalVal(key, _optionVar(q=k))
            _optionVar(rm=k)

        if val is self:
            if not args:
                raise KeyError(key)
            val = args[0]
        return val

    def clear(self):
        u"""
        全ての値とデフォルト値を削除する。
        """
        prefix = self._prefix
        for k in _optionVar(l=True):
            if k.startswith(prefix):
                _optionVar(rm=k)
        self._defaultDict.clear();

    def update(self, src):
        u"""
        指定した辞書で値を書き換える。

        :param `dict` src: ソース辞書。
        """
        for k, v in src.items():
            self[k] = v

    def setDefault(self, key, val):
        u"""
        キーに対するデフォルト値をセットする。

        :param `str` key: キー。
        :param val: 値。
        """
        self._defaultDict[key] = val
        k = self._prefix + key
        if self._evalVal(key, _optionVar(q=k)) == val:
            _optionVar(rm=k)

    def setDefaults(self, dic):
        u"""
        辞書によってデフォルト値をまとめて登録する。

        :param `dict` dic:
            登録するデフォルト値の辞書。
        """
        for key, val in dic.items():
            self.setDefault(key, val)

    def hasDefault(self, key):
        u"""
        デフォルト値を持つキーかどうか。

        :param `str` key: キー。
        :rtype: `bool`
        """
        return key in self._defaultDict

    def getDefault(self, key):
        u"""
        デフォルト値を得る。

        :param `str` key: キー。
        :returns: 登録された値。
        """
        return self._defaultDict[key]

    def removeDefault(self, key):
        u"""
        デフォルト値を削除する。

        現在の値がデフォルト値の場合、
        デフォルト値の削除後も現在の値を保持するために、
        :mayacmd:`optionVar` の書き込みが行われる。

        もし、完全に削除したい場合は、本メソッドではなく、
        del や `pop` を使用すべきである。

        :param `str` key: キー。
        """
        val = self._defaultDict.pop(key)
        k = self._prefix + key
        if not _optionVar(ex=k):
            self.__setitem__(k, val)

    def reset(self, key):
        u"""
        指定したキーの値をデフォルト値にリセットする。

        :param `str` key: キー。
        """
        if key not in self._defaultDict:
            raise KeyError(key)
        _optionVar(rm=self._prefix + key)

    def resetAll(self, ignores=None):
        u"""
        デフォルト値を持つ全てのキーをリセットする。

        :param iterable ignores: リセットしないキーリスト。
        """
        prefix = self._prefix
        if ignores:
            for k in self._defaultDict:
                if k not in ignores:
                    _optionVar(rm=prefix + k)
        else:
            for k in self._defaultDict:
                _optionVar(rm=prefix + k)

    def defaultKeys(self):
        u"""
        デフォルト値を持つキーのリストを得る。

        :rtype: `list`
        """
        return self._defaultDict.keys()

    def defaultValues(self):
        u"""
        デフォルト値のリストを得る。

        :rtype: `list`
        """
        return self._defaultDict.values()

    def defaultItems(self):
        u"""
        デフォルト値を持つキーとその値のペアのリストを得る。

        :rtype: `list`
        """
        return self._defaultDict.items()

    def nonDefaultKeys(self):
        u"""
        デフォルトでない（実際に保存されている）キーのリストを得る。

        :rtype: `list`
        """
        prefix = self._prefix
        start = len(prefix)
        return [k[start:] for k in _optionVar(l=True) if k.startswith(prefix)]

    def nonDefaultValues(self):
        u"""
        デフォルトでない（実際に保存されている）値のリストを得る。

        :rtype: `list`
        """
        prefix = self._prefix
        start = len(prefix)
        evalVal = self._evalVal
        return [
            evalVal(k[start:], _optionVar(q=k))
            for k in _optionVar(l=True) if k.startswith(prefix)]

    def nonDefaultItems(self):
        u"""
        デフォルトでない（実際に保存されている）キーと値のペアのリストを得る。

        :rtype: `list`
        """
        prefix = self._prefix
        start = len(prefix)
        evalVal = self._evalVal
        return [
            (k[start:], evalVal(k[start:], _optionVar(q=k)))
            for k in _optionVar(l=True) if k.startswith(prefix)]

    def hasNonDefaultValue(self, key):
        u"""
        デフォルト値ではない値が保存されているかどうか。

        :rtype: `bool`
        """
        return _optionVar(ex=self._prefix + key)

    def keys(self):
        u"""
        セットされているキーのリストを得る。

        実際の :mayacmd:`optionVar` に記録内容と
        デフォルト値の連結結果が得られる。

        :rtype: `list`
        """
        prefix = self._prefix
        start = len(prefix)
        keys = [k[start:] for k in _optionVar(l=True) if k.startswith(prefix)]
        keySet = frozenset(keys)
        return keys + [k for k in self._defaultDict if k not in keySet]

    def values(self):
        u"""
        セットされている値のリストを得る。

        実際の :mayacmd:`optionVar` に記録内容と
        デフォルト値の連結結果が得られる。

        :rtype: `list`
        """
        prefix = self._prefix
        start = len(prefix)
        evalVal = self._evalVal
        defaults = self._defaultDict
        keys = [k[start:] for k in _optionVar(l=True) if k.startswith(prefix)]
        keySet = frozenset(keys)
        vals = [evalVal(k, _optionVar(q=prefix + k)) for k in keys]
        return vals + [defaults[k] for k in defaults if k not in keySet]

    def items(self):
        u"""
        セットされているキーと値のペアのリストを得る。

        実際の :mayacmd:`optionVar` に記録内容と
        デフォルト値の連結結果が得られる。

        :rtype: `list`
        """
        prefix = self._prefix
        start = len(prefix)
        evalVal = self._evalVal
        defaults = self._defaultDict
        keys = [k[start:] for k in _optionVar(l=True) if k.startswith(prefix)]
        keySet = frozenset(keys)
        items = [(k, evalVal(k, _optionVar(q=prefix + k))) for k in keys]
        return items + [kv for kv in defaults.items() if kv[0] not in keySet]

    def setTranslator(self, key, getter_setter=(eval, repr)):
        u"""
        :mayacmd:`optionVar` に保存する値と実際の値の変換器をセットする。

        :param `str` key: キー。
        :param getter_setter:
            getter（保存値を実値に変換）と
            setter（実値を保存値に変換）のペアを指定する。
            省略すると (eval, repr) がセットされる。
            None を指定するとセット済みの変換器を解除する。
        """
        k = self._prefix + key
        if getter_setter:
            self._translators[k] = getter_setter
        else:
            del self._translators[k]

    def _evalVal(self, key, val):
        u"""
        :mayacmd:`optionVar` から得た値を解釈する。
        """
        if val == _STR_NONE:
            val = None
        elif val == _STR_TRUE:
            val = True
        elif val == _STR_FALSE:
            val = False

        trans = self._translators.get(key)
        if trans:
            return trans[0](val)
        return val

