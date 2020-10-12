# -*- coding: utf-8 -*-
u"""
mel UI の :mayacmd:`window` ラッパー。
"""
from ..common import *
from .uitypes import *
from .control import Control

__all__ = ['Window']

_cmds_setParent = cmds.setParent
_cmds_deleteUI = cmds.deleteUI
_cmds_window = cmds.window


#------------------------------------------------------------------------------
class Window(uiParentClass('window')):
    u"""
    mel UI の :mayacmd:`window` ラッパークラス。

    `with` で :mayacmd:`setParent` が行える。
    """
    UICMD = _cmds_window  #: 対応する mel コマンドオブジェクト。

    def __enter__(self):
        cur = _cmds_setParent(q=True)
        if not getattr(self, '_lastCurrent', None) or cur != self._name:
            self._lastCurrent = cur
        _cmds_setParent(self._name)
        return self

    def __exit__(self, type, value, traceback):
        uiSetParent(self._lastCurrent)
        self._lastCurrent = None

    def name(self):
        u"""
        ウィンドウ名を得る。

        :rtype: `str`
        """
        return self._name

    def window(self):
        u"""
        このウィンドウそのものを得る。

        :rtype: `Window`
        """
        return self

    def parent(self):
        u"""
        親は得られない。

        :rtype: None
        """
        return

    def show(self):
        u"""
        ウィンドウを表示する。
        """
        cmds.showWindow(self._name)

    def delete(self):
        u"""
        ウィンドウを削除する。
        """
        _cmds_deleteUI(self._name, wnd=True)

    def layout(self):
        u"""
        ウィンドウが持つレイアウトを1つ得る。

        :rtype: `.Layout`
        """
        # ドック化された場合はレイアウトのパスが得られる。
        name = cmds.control(self._name, q=True, fpn=True)
        if '|' in name:
            return Control(name)

        # ドック化されていないなら、全レイアウトから直下のものを選出する。
        pre = name + '|'
        names = [s for s in cmds.lsUI(cl=True, l=True) if s.startswith(pre)]
        if names:
            names.sort()
            return Control(names[0])

    def layouts(self):
        u"""
        ウィンドウが持つレイアウトを全て得る。

        :rtype: `list`
        """
        # ドック化された場合はレイアウトのパスが得られる。
        name = cmds.control(self._name, q=True, fpn=True)
        if '|' in name:
            return [Control(name)]

        # ドック化されていないなら、全レイアウトから直下のものを選出する。
        pre = name + '|'
        return [Control(s) for s in cmds.lsUI(l=True, cl=True) if s.startswith(pre) and len(s.split('|')) is 2]

    def children(self):
        u"""
        ウィンドウが持つ子コントロールを全て得る。

        :rtype: `list`
        """
        # ドック化された場合はレイアウトのパスが得られる。
        name = cmds.control(self._name, q=True, fpn=True)
        if '|' in name:
            return [Control(name)]

        # ドック化されていないなら、全コントロールから直下のものを選出する。
        pre = name + '|'
        return [Control(s) for s in cmds.lsUI(l=True, ctl=True) if s.startswith(pre) and len(s.split('|')) is 2]

    def makeCurrent(self):
        u"""
        これをカレントペアレントにする。
        """
        _cmds_setParent(self._name)

    def changeToDockControl(self, allowedArea=('left', 'right'), area=None, **kwargs):
        u"""
        ウィンドウをドッキングコントロール化する。

        :rtype: `.DockControl`
        """
        name = self.name()
        title = _cmds_window(name, q=True, t=True)
        wh = _cmds_window(name, q=True, wh=True)
        if not area:
            area = allowedArea[0]
        return DockControl(
            name + 'Dock', l=title, w=wh[0], h=wh[1], con=name,
            aa=allowedArea, a=area, **kwargs)

registerTypedCls(Window)


#------------------------------------------------------------------------------
class DockControl(uiParentClass('dockControl')):
    u"""
    mel UI の :mayacmd:`dockControl` ラッパークラス。

    mel のクラスとしては、
    ドッキング状態の場合は :mayacmd:`layout` であり、
    フローティング状態の場合は :mayacmd:`window` となるように
    動的に切り替わるため、
    ラッパークラスとしては `.Control` 派生に固定されている。
    """
    UICMD = cmds.dockControl  #: 対応する mel コマンドオブジェクト。

registerTypedCls(DockControl)

