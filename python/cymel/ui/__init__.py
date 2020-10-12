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
