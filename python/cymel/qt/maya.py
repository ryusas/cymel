# -*- coding: utf-8 -*-
u"""
Maya UI に関する Qt ヘルパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..initmaya import IS_UIMODE as IS_MAYA_UI_ENABLED
from . import widgets as _widgets
from .binding import QWidget, wrapInstance

__all__ = [
    'IS_MAYA_UI_ENABLED', 'getMainWindow', 'getMayaWidget', 'getDpiScaling',
]

if IS_MAYA_UI_ENABLED:
    try:
        from maya.OpenMayaUI import MQtUtil as _MQtUtil
        import maya.cmds as _mayacmds
        _mayacmds_setParent = _mayacmds.setParent
        _MAYA_FIND_FUNCS = (
            ('control', _MQtUtil.findControl),
            ('layout', _MQtUtil.findLayout),
            ('window', _MQtUtil.findWindow),
            ('menuItem', _MQtUtil.findMenuItem),
        )
        _MAYA_FIND_FUNC_DICT_get = dict(_MAYA_FIND_FUNCS).get

        from ..pyutils import LONG

    except (ImportError, AttributeError):
        IS_MAYA_UI_ENABLED = False


def getMainWindow():
    u"""
    Maya のメインウィンドウを QWidget として取得する。

    :rtype: `QWidget`
    """


def getMayaWidget(name=None, uitype=None, cls=QWidget):
    u"""
    Maya UI 名に対応する Qt ウィジェットを取得する。

    :param `str` name:
        UI のフルパス名。
        省略した場合はカレントレイアウトとなる。

    :param `str` uitype:
        name を指定し cls が None でないときに有効。

        分かっていれば、Maya の UI タイプを文字列で指定する。
        'control', 'layout', 'window', 'menuItem'
        のいずれかを指定出来る。

        Windows では layout を control として取得出来たが
        Linux では出来ないことがあった（ものによる）。
        未指定の場合、取得できるまで全タイプが試されるが、
        分かっているなら指定した方が確実。

    :param `type` cls:
        `wrapInstance` での取得を試みる際に指定するクラス。
        None を指定すると `getWidgetByPathName` が利用される。

    :rtype: `QWidget`

    .. note::
        cls に None を指定しなければ、
        初めに Maya API と `wrapInstance` を用いた簡易的な手法が試される。
        まれに `wrapInstance` は `OverflowError` となり、その場合、
        `getWidgetByPathName` が使用される。
        その場合のクラスは自動的に適切なものに決定される。
    """


def getDpiScaling(widget=None):
    u"""
    Maya UI の DPI スケールを取得する。

    :rtype: `float`
    """
    return _widgets.getDpiScaling(widget)


if IS_MAYA_UI_ENABLED:
    _doc = getMainWindow.__doc__

    def getMainWindow():
        ptr = _MQtUtil.mainWindow()
        return ptr and wrapInstance(LONG(ptr), QWidget)

    getMainWindow.__doc__ = _doc


    _doc = getMayaWidget.__doc__

    def getMayaWidget(name=None, uitype=None, cls=QWidget):
        if cls:
            if name:
                func = _MAYA_FIND_FUNC_DICT_get(uitype)
                if func:
                    ptr = func(name)
                else:
                    ptr = None
                    for key, func in _MAYA_FIND_FUNCS:
                        ptr = func(name)
                        if ptr:
                            break
                if ptr:
                    try:
                        return wrapInstance(LONG(ptr), cls)
                    except OverflowError:
                        pass
            else:
                ptr = _MQtUtil.getCurrentParent()
                if ptr:
                    try:
                        return wrapInstance(LONG(ptr), cls)
                    except OverflowError:
                        name = _mayacmds_setParent(q=True)
        elif not name:
            name = _mayacmds_setParent(q=True)

        return _widgets.getWidgetByPathName(name)

    getMayaWidget.__doc__ = _doc


    _doc = getDpiScaling.__doc__

    def getDpiScaling(widget=None):
        global _MAYA_DPI_SCALE
        if not _MAYA_DPI_SCALE:
            try:
                _MAYA_DPI_SCALE = _mayacmds.mayaDpiSetting(q=True, rsv=True)
            except Exception:
                _MAYA_DPI_SCALE = 1.
        return _MAYA_DPI_SCALE

    getDpiScaling.__doc__ = _doc
    _MAYA_DPI_SCALE = 0
    _widgets.getDpiScaling = getDpiScaling

    del _doc
