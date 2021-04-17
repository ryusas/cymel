# -*- coding: utf-8 -*-
u"""
mel UI の :mayacmd:`uiTemplate` ラッパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..common import *

__all__ = ['UITemplate']

_cmds_uiTemplate = cmds.uiTemplate
_cmds_setUITemplate = cmds.setUITemplate
_cmds_deleteUI = cmds.deleteUI


#------------------------------------------------------------------------------
class UITemplate(object):
    u"""
    mel UI の :mayacmd:`uiTemplate` ラッパークラス。

    `with` で :mayacmd:`setUITemplate` が行える。

    .. code-block:: python

        import maya.cmds as cmds
        import cymel.ui as cmu

        template = cmu.UITemplate('ExampleTemplate', force=True)
        template.define(cmds.button, width=100, height=40, align='left')
        template.define(cmds.frameLayout, borderVisible=True, labelVisible=False)

        wnd = cmu.Window()
        with template:
            cmu.FrameLayout()
            cmu.Button()
        wnd.show()
    """
    def __init__(self, name=None, force=False, **kwargs):
        u"""
        初期化。

        :param `str` name:
            UIテンプレート名。
            省略するか、存在しない名前を指定すると新規生成される。
        :param `bool` force:
            既存のUIテンプレート名を指定した場合に、
            既存のものを削除して作り直すかどうか。
        """
        if name:
            if _cmds_uiTemplate(name, ex=True):
                if force:
                    _cmds_deleteUI(name, uiTemplate=True)
                    self._name = _cmds_uiTemplate(name, **kwargs)
                else:
                    self._name = name
            else:
                self._name = _cmds_uiTemplate(name, **kwargs)
        else:
            self._name = _cmds_uiTemplate(**kwargs)

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self._name)

    def __enter__(self):
        _cmds_setUITemplate(self._name, pushTemplate=True)
        return self

    def __exit__(self, type, value, traceback):
        _cmds_setUITemplate(popTemplate=True)

    def name(self):
        return self._name

    def push(self):
        return _cmds_setUITemplate(self._name, pushTemplate=True)

    def pop(self):
        return _cmds_setUITemplate(popTemplate=True)

    def delete(self):
        u"""
        このテンプレートを削除する。
        """
        _cmds_deleteUI(self._name, uiTemplate=True)

    def define(self, uiType, **kwargs):
        u"""
        テンプレートにUIオプション値を設定する。

        uiTemplate -defineTemplate 相当の機能

        :param uiType: cmds の ui 関数、又はオブジェクト。
        :param kwargs: uiType関数に渡すテンプレートにするオプション引数
        """
        if isinstance(uiType, Iterable):
            funcs = [_resolveUIFunc(x) for x in uiType]
        else:
            funcs = [_resolveUIFunc(uiType)]
        kwargs['defineTemplate'] = self._name
        for func in funcs:
            func(**kwargs)

    @classmethod
    def exists(cls, name):
        return _cmds_uiTemplate(name, exists=True)


def _resolveUIFunc(obj):
    if isinstance(obj, BASESTR):
        return getattr(cmds, obj, None)
    elif isinstance(obj, Callable):
        return obj
    raise ValueError(repr(obj) + ' is not a known ui type')

