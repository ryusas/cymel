# -*- coding: utf-8 -*-
u"""
UI系機能。

cymel.ui 以下の全てが展開されている。
"""
from .control import *
from .layout import *
from .window import *
from .menu import *
from .uitemplate import *

control.Layout = Layout
control.Window = Window
control.Menu = Menu
control.MenuItem = MenuItem
control.SubMenuItem = SubMenuItem
control._PARENTABLE_LAYOUTS = (Layout, Window)
control._PARENTABLE_LAYOUTS_AND_OPTIONMENU = (Layout, Window, OptionMenu)

from . import uitypes
uitypes._generateSimpleClasses()
from .uitypes import *

def _all():
    from types import ModuleType
    return [k for k, v in globals().items()
        if not k.startswith('_') and not isinstance(v, ModuleType)]
__all__ = _all()
del _all
