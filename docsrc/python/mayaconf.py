# -*- coding: utf-8 -*-
u"""
mayaモジュールドキュメンテーション用のsphinxコンフィギュレーション。
"""
from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import sys
import os
import inspect

#------------------------------------------------------------------------------
MAYA_DOC_URL = 'https://download.autodesk.com/global/docs/maya2013/en_US/'
MAYA_API1_URL = 'http://docs.autodesk.com/MAYAUL/2013/ENU/Maya-API-Documentation/'
MAYA_API2_URL = 'http://docs.autodesk.com/MAYAUL/2013/ENU/Maya-API-Documentation/python-api/'


#------------------------------------------------------------------------------
def get_std_extlinks():
    u"""
    標準の extlinks 定義を得る。

    :rtype: `dict`
    """
    return _EXTLINKS.copy()

_EXTLINKS = {
    'mayanode': (MAYA_DOC_URL + 'Nodes/%s.html', '%s'),
    'mayacmd': (MAYA_DOC_URL + 'CommandsPython/%s.html', '%s'),
    'mayaapi2': (MAYA_API2_URL + '%s.html', '%s'),
    'mayaapi1': (MAYA_API1_URL + 'index.html?url=cpp_ref/class_%s.html', '%s',),
}


#------------------------------------------------------------------------------
def set_all_filters():
    u"""
    標準のフィルターを全てセットする。
    """
    import jinja2
    jinja2.filters.FILTERS['in_module'] = filter_in_module
    jinja2.filters.FILTERS['if_alias'] = filter_if_alias
    jinja2.filters.FILTERS['in_class'] = filter_in_class
    jinja2.filters.FILTERS['uppercase'] = filter_uppercase
    jinja2.filters.FILTERS['if_constant'] = filter_if_constant


#------------------------------------------------------------------------------
def chk_if_alias(val, name):
    u"""
    エイリアスかどうかチェックする。

    :param val: モジュール属性値。
    :param name: モジュール属性名。
    :rtype: `bool`
    """
    return _has_name(val) and val.__name__ != name


def chk_if_no_alias(val, name):
    u"""
    エイリアスでないかどうかチェックする。

    :param val: モジュール属性値。
    :param name: モジュール属性名。
    :rtype: `bool`
    """
    return not _has_name(val) or val.__name__ == name


def _has_name(val):
    try:
        return hasattr(val, '__name__')
    except:
        return False


#----------------------------------------------------
IGNORE_MODULES = set()  #: 全メンバーのドキュメント化を抑制するモジュール名のセット。

NO_CHECK_IN_MODULE = set()  #: モジュールの直接メンバーかどうかのチェックをしない（インポートしたものもドキュメント対象にする）モジュール名のセット。

IGNORE_ALIASES_MODULES = set()  #: エイリアスのドキュメント化を抑制するモジュール名のセット。

ALL_INHERITED_MEMBERS = set()  #: 継承しているだけのクラスメンバーも全てドキュメントする ``モジュール名.クラス名`` のセット。

ORIGINAL_ALIASES = {
    #'BASESTR': 'cymel.utils.pyutils',
    #'BYTES': 'cymel.utils.pyutils',
    #'UNICODE': 'cymel.utils.pyutils',
    #'LONG': 'cymel.utils.pyutils',
    #'lrange': 'cymel.utils.pyutils',
    #'xrange': 'cymel.utils.pyutils',
    #'lzip': 'cymel.utils.pyutils',
    #'izip': 'cymel.utils.pyutils',
    #'izip_longest': 'cymel.utils.pyutils',
    #'reduce': 'cymel.utils.pyutils',

    'O': 'cymel.core.cyobjects.cyobject',
    'BB': 'cymel.core.datatypes.boundingbox',
    'E': 'cymel.core.datatypes.eulerrotation',
    'M': 'cymel.core.datatypes.matrix',
    'Q': 'cymel.core.datatypes.quaternion',
    'X': 'cymel.core.datatypes.transformation',
    'V': 'cymel.core.datatypes.vector',
}  #: よく使うエイリアスとそれを定義しているモジュールの辞書。


def filter_in_module(names, modname):
    u"""
    モジュールメンバーかどうかのフィルター。

    アンダースコアで始まる非公開名は除去しつつ、モジュールメンバー以外を除外する。

    標準テンプレートにおいて、フィルター 'in_module' として使う。

    以下の属性を参照する。

    * `IGNORE_MODULES`

      全メンバーのドキュメント化を抑制するモジュール名のセット。

    * `NO_CHECK_IN_MODULE`

      モジュールの直接メンバーかどうかのチェックをしない
      （インポートしたものもドキュメント対象にする）モジュール名のセット。
    """
    # 特定モジュールは完全に無視。
    if modname in IGNORE_MODULES:
        return []

    # 特定モジュールはスルー。
    if modname in NO_CHECK_IN_MODULE:
        return names

    modname_dot = modname + '.'
    len_modname_dot = len(modname_dot)
    mod = sys.modules[modname]

    def _in_module(name):
        # 非公開名は無視。
        if name.startswith('_'):
            return

        obj = getattr(mod, name)
        res = name

        # モジュールの直接メンバーかどうか。
        owner = getattr(obj, '__module__', 0)
        if owner != 0:
            if not owner:
                return
            if owner != modname:
                if owner.startswith(modname_dot):
                    if isinstance(obj, type):
                        res = '~%s.%s' % (owner[len_modname_dot:], name)
                else:
                    return

        # ドキュメントを持たない（型のdocstringと同じ）場合、
        if type(obj).__doc__ == obj.__doc__:
            # さらに sphinx の特殊ドキュメントを調べ、それも持たなければ無視（他からのコピーである）。
            if not _find_attr_docs(modname, name):
                return

        # エイリアスでないかどうかチェック。
        return chk_if_no_alias(obj, name) and res

    results = []
    for s in names:
        s = _in_module(s)
        if s:
            results.append(s)
    return results


def filter_if_alias(names, modname):
    u"""
    エイリアスかどうかのフィルター。

    アンダースコアで始まる非公開名は除去しつつ、他からインポートしたエイリアスのみにする。

    標準テンプレートにおいて、フィルター 'if_alias' として使う。

    以下の属性を参照する。

    * `IGNORE_ALIASES_MODULES`

      エイリアスのドキュメント化を抑制するモジュール名のセット。
      機械的に生成した大量のエイリアスを無視したり、
      数値や文字列のモジュール判別が出来ない為、モジュール名決め打ちで逃げる。

    * `ORIGINAL_ALIASES`

      よく使うエイリアスとそれを定義しているモジュールの辞書。
      ここに挙げるエイリアスは指定モジュール以外ではドキュメント化されない。
    """
    if modname in IGNORE_ALIASES_MODULES:
        return []
    mod = sys.modules[modname]
    return [
        s for s in names if (
            not s.startswith('_')
            and (s not in ORIGINAL_ALIASES or ORIGINAL_ALIASES[s] == modname)
            and chk_if_alias(getattr(mod, s), s)
        )
    ]


def filter_in_class(names, modname, clsname):
    u"""
    クラスメンバーかどうかのフィルター。

    標準テンプレートにおいて、フィルター 'in_class' として使う。

    以下の属性を参照する。

    * `ALL_INHERITED_MEMBERS`

      継承しているだけのクラスメンバーもドキュメント化されるようにする
      ``モジュール名.クラス名`` を含む `set` 。
    """
    if (modname + '.' + clsname) not in ALL_INHERITED_MEMBERS:
        # 継承しているだけの属性を除外する場合。
        def _in_class(name):
            try:
                return name in cls.__dict__
            except AttributeError:
                return getattr(cls, name) != getattr(cls.__bases__[0], name, None)
        cls = getattr(sys.modules[modname], clsname)
        return [s for s in names if _in_class(s)]
    return names


def filter_uppercase(names):
    u"""
    全て大文字かどうかのフィルター。

    標準テンプレートにおいて、フィルター 'uppercase' として使う。
    """
    return [s for s in names if s.isupper()]


def filter_if_constant(names, modname):
    u"""
    定数としてドキュメントに列挙するかどうかのフィルター。

    全て大文字で、且つクラスでは無いものが抽出される。

    標準テンプレートにおいて、フィルター 'if_constant' として使う。
    """
    mod = sys.modules[modname]
    return [s for s in names if s.isupper() and not isinstance(getattr(mod, s), type)]


#------------------------------------------------------------------------------
def _find_attr_docs(modname, name):
    u"""
    |sphinx| の |python| 用 ModuleAnalyzer を使用して、pydoc でない特殊指定のドキュメント文字列を得る。
    クラスの attributes やモジュールの data でよく用いられる。
    """
    if modname in _attrDocsDict:
        d = _attrDocsDict[modname]
    else:
        try:
            _attrDocsDict[modname] = d = ModuleAnalyzer.for_module(modname).find_attr_docs()
        except PycodeError as e:
            raise RuntimeError("sphinx.pycode parsing failure: %s" % modname)
    key = ('', name)
    if key in d:
        return d[key]

from sphinx.pycode import ModuleAnalyzer
from sphinx.errors import PycodeError
_attrDocsDict = {}

