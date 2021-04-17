# -*- coding: utf-8 -*-
u"""
mel UI のメニュー系のラッパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..common import *
from .uitypes import *
from .control import Control

__all__ = [
    'MenuBarLayout',
    'Menu',
    'MenuItem',
    'SubMenuItem',
    'PopupMenu',
    'OptionMenu',
    'OptionMenuGrp',
]

_cmds_setParent = cmds.setParent
_cmds_menuBarLayout = cmds.menuBarLayout
_cmds_menu = cmds.menu
_cmds_deleteUI = cmds.deleteUI


#------------------------------------------------------------------------------
class MenuBarLayout(uiParentClass('menuBarLayout')):
    u"""
    mel UI の :mayacmd:`menuBarLayout` ラッパークラス。

    `with` で :mayacmd:`setParent` が行える。

    Maya 標準コマンドに基づき、
    レイアウトされたメニューを得るには `children` ではなく
    `menus` などのメソッドを用いなければならない。
    とはいえ `.Menu` からは `.Control.parent`
    でレイアウトを取得出来る。
    """
    UICMD = _cmds_menuBarLayout  #: 対応する mel コマンドオブジェクト。

    def menuNames(self):
        u"""
        メニューの名前リストを得る。

        :rtype: `list`
        """
        return _cmds_menuBarLayout(self.name(), q=True, ma=True) or []

    def menus(self):
        u"""
        メニューのリストを得る。

        :rtype: `list`
        """
        pre = self.name()
        names = _cmds_menuBarLayout(pre, q=True, ma=True)
        if names:
            pre += '|'
            return [Control(pre + s) for s in names]
        return []

    def numMenus(self):
        u"""
        メニューの数を得る。

        :rtype: `int`
        """
        return _cmds_menuBarLayout(self.name(), q=True, nm=True)

    def menu(self, idxOrPath=0):
        u"""
        メニューを得る。

        :param idxOrPath:
            子のインデックス（ゼロオリジン）か、
            階層下の相対パス。
        :rtype: `.Control`
        """
        name = self.name()
        pre = name + '|'
        if isinstance(idxOrPath, BASESTR):
            return Control(pre + idxOrPath)
        return Control(pre + _cmds_menuBarLayout(name, q=True, ma=True)[idxOrPath])

    def clear(self):
        u"""
        子とメニューを全て削除する。
        """
        pre = self.name()
        uis = _cmds_menuBarLayout(pre, q=True, ma=True)
        if uis:
            pre += '|'
            _cmds_deleteUI(*[(pre + ui) for ui in uis])
        super(MenuBarLayout, self).clear()

registerTypedCls(MenuBarLayout)


#------------------------------------------------------------------------------
class Menu(uiParentClass('menu')):
    u"""
    mel UI の :mayacmd:`menu` ラッパークラス。

    `with` で :mayacmd:`setParent` が行える。
    """
    UICMD = _cmds_menu  #: 対応する mel コマンドオブジェクト。

    def __enter__(self):
        name = self.name()
        cur = _cmds_setParent(q=True, menu=True)
        if not getattr(self, '_lastCurrent', None) or cur != name:
            self._lastCurrent = cur
        _cmds_setParent(name, menu=True)
        return self

    def __exit__(self, type, value, traceback):
        uiSetParent(self._lastCurrent, menu=True)
        self._lastCurrent = None

    def childNames(self):
        u"""
        子のメニューアイテム名リストを得る。

        :rtype: `list`
        """
        # SubMenuItem を考慮して UICMD は利用しない。
        names = _cmds_menu(self.name(), q=True, ia=True)
        return names if names else []

    def children(self):
        u"""
        子のメニューアイテムのリストを得る。

        :rtype: `list`
        """
        pre = self.name()
        # SubMenuItem を考慮して UICMD は利用しない。
        names = _cmds_menu(pre, q=True, ia=True)
        if names:
            pre += '|'
            return [Control(pre + s) for s in names]
        return []

    def numChildren(self):
        u"""
        メニューアイテム数を得る。

        :rtype: `int`
        """
        # SubMenuItem を考慮して UICMD は利用しない。
        return _cmds_menu(self.name(), q=True, ni=True)

    def child(self, idxOrPath=0):
        u"""
        階層下のメニューアイテムを得る。

        :param idxOrPath:
            子のインデックス（ゼロオリジン）か、
            階層下の相対パス。
        :rtype: `.Control`
        """
        name = self.name()
        pre = name + '|'
        if isinstance(idxOrPath, BASESTR):
            return Control(pre + idxOrPath)
        # SubMenuItem を考慮して UICMD は利用しない。
        return Control(pre + _cmds_menu(name, q=True, ia=True)[idxOrPath])
    #----

    def clear(self):
        u"""
        子のメニューアイテムを全て削除する。
        """
        pre = self.name()
        # SubMenuItem を考慮して UICMD は利用しない。
        uis = _cmds_menu(pre, q=True, ia=True)
        if uis:
            pre += '|'
            _cmds_deleteUI(*[(pre + ui) for ui in uis])

    def makeCurrent(self):
        u"""
        これをカレントペアレントメニューにする。
        """
        _cmds_setParent(self.name(), menu=True)

    @staticmethod
    def getCurrent():
        u"""
        カレントペアレントメニューを得る。

        :rtype: `Menu`
        """
        cur = _cmds_setParent(q=True, menu=True)
        # SubMenuItem を考慮して UICMD は利用しない。
        if _cmds_menu(cur, ex=True):
            return Control(cur)

    @staticmethod
    def pop():
        u"""
        カレントペアレントメニューを一つ上に移動させる。
        """
        return Control(_cmds_setParent('..', menu=True))

registerTypedCls(Menu)


#------------------------------------------------------------------------------
class MenuItem(uiParentClass('menuItem')):
    u"""
    mel UI の :mayacmd:`menuItem` ラッパークラス。

    subMenu=True を指定すると `.SubMenuItem` となる。

    .. note::
        :mayacmd:`menuItem` は :mayacmd:`control` では
        ないようなのだが、このモジュールでは `.Control`
        の派生型としている。
    """
    UICMD = cmds.menuItem  #: 対応する mel コマンドオブジェクト。

registerTypedCls(MenuItem)


#------------------------------------------------------------------------------
class SubMenuItem(Menu):
    u"""
    `.Menu` として振る舞う :mayacmd:`menuItem` -subMenu のラッパークラス。

    `with` で :mayacmd:`setParent` が行える。

    .. note::
        `MenuItem` と異なり `Menu` の派生型である。
    """
    UICMD = cmds.menuItem  #: 対応する mel コマンドオブジェクト。

#registerTypedCls(SubMenuItem)


#------------------------------------------------------------------------------
class PopupMenu(uiParentClass('popupMenu')):
    u"""
    mel UI の :mayacmd:`popupMenu` ラッパークラス。

    `with` で :mayacmd:`setParent` が行える。
    """
    UICMD = cmds.popupMenu  #: 対応する mel コマンドオブジェクト。

registerTypedCls(PopupMenu)


#------------------------------------------------------------------------------
class OptionMenu(uiParentClass('optionMenu')):
    u"""
    mel UI の :mayacmd:`optionMenu` ラッパークラス。

    `with` で :mayacmd:`setParent` が行える。
    """
    UICMD = cmds.optionMenu  #: 対応する mel コマンドオブジェクト。

    def getValue(self):
        u"""
        値を得る。

        :rtype: `int`
        """
        return self.UICMD(self.name(), q=True, sl=True)

    def setValue(self, val):
        u"""
        値をセットする。

        :param `int` val: セットする値。
        """
        self.UICMD(self.name(), e=True, sl=val)

registerTypedCls(OptionMenu)


#------------------------------------------------------------------------------
class OptionMenuGrp(uiParentClass('optionMenuGrp')):
    u"""
    mel UI の :mayacmd:`optionMenuGrp` ラッパークラス。

    `with` で :mayacmd:`setParent` が行える。
    """
    UICMD = cmds.optionMenuGrp  #: 対応する mel コマンドオブジェクト。

    def __enter__(self):
        self.menu().__enter__()
        return super(OptionMenuGrp, self).__enter__()

    def __exit__(self, type, value, traceback):
        self.menu().__exit__(type, value, traceback)
        return super(OptionMenuGrp, self).__exit__(type, value, traceback)

    def menu(self):
        u"""
        `OptionMenu` を取得する。

        :rtype: `OptionMenu`
        """
        for child in self.children():
            if isinstance(child, OptionMenu):
                return child

    def getValue(self):
        u"""
        値を得る。

        :rtype: `int`
        """
        return self.UICMD(self.name(), q=True, sl=True)

    def setValue(self, val):
        u"""
        値をセットする。

        :param `int` val: セットする値。
        """
        self.UICMD(self.name(), e=True, sl=val)

registerTypedCls(OptionMenuGrp)

