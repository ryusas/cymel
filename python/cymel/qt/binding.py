# -*- coding: utf-8 -*-
u"""
PySide バインディングの判別と互換エイリアス。

Qt/PySide 由来の名前をそのまま公開するもの。

  - `QtCore`
  - `QtGui`
  - `QtWidgets`
  - `Qt`
  - `Property`
  - `Signal`
  - `Slot`
  - `QWidget`
  - `QApplication`

cymel が追加するバインディング情報。

  - `QT_BINDING_NAME` (str): 使用中のバインディング名。
  - `QT_BINDING_VERSION` (str): バインディングのバージョン文字列。
  - `QT_BINDING_VERSION_I` (tuple): バインディングのバージョンを数値タプル化したもの。
  - `QT_VERSION` (str): Qt のバージョン文字列。
  - `QT_VERSION_I` (tuple): Qt のバージョンを数値タプル化したもの。
  - `QT_MAJOR_VERSION` (int): Qt のメジャーバージョン。
  - `qtmodule`: 使用中の PySide モジュール。
  - `uic`: PySide/PySide2 の UI コンパイラモジュール。無い場合は None。

shiboken 由来の互換ヘルパー。

  - `wrapInstance`: C++ ポインタを Qt ラッパーに変換する。
  - `unwrapInstance`: Qt ラッパーから C++ ポインタを得る。
  - `isValidWrap`: Qt ラッパーが有効かどうかを返す。
  - `isInvalidWrap`: Qt ラッパーが無効かどうかを返す。
  - `isOwnedByPython`: インスタンスが Python 側に所有されているかどうかを返す。
  - `deleteInstance`: Qt ラッパーの対象インスタンスを削除する。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re as _re
import sys

__all__ = [
    'QT_BINDING_NAME', 'QT_BINDING_VERSION', 'QT_BINDING_VERSION_I',
    'QT_VERSION', 'QT_VERSION_I', 'QT_MAJOR_VERSION',
    'qtmodule', 'QtCore', 'QtGui', 'QtWidgets', 'Qt',
    'Property', 'Signal', 'Slot', 'uic',
    'wrapInstance', 'unwrapInstance', 'isValidWrap', 'isInvalidWrap',
    'isOwnedByPython', 'deleteInstance',
    'QWidget', 'QApplication',
]


def _initBinding():
    def _versionTuple(s):
        search = _re.compile(r'\d+').search
        return tuple([int(search(x).group(0)) for x in s.split('.') if search(x)])

    def _setCommon(name, module, core, gui, widgets, shiboken, uicmod):
        global QT_BINDING_NAME, QT_BINDING_VERSION, QT_BINDING_VERSION_I
        global QT_VERSION, QT_VERSION_I, QT_MAJOR_VERSION
        global qtmodule, QtCore, QtGui, QtWidgets, Qt, Property, Signal, Slot, uic
        global wrapInstance, unwrapInstance, isValidWrap, isInvalidWrap
        global isOwnedByPython, deleteInstance

        QT_BINDING_NAME = name
        qtmodule = module
        QtCore = core
        QtGui = gui
        QtWidgets = widgets
        Qt = core.Qt
        Property = core.Property
        Signal = core.Signal
        Slot = core.Slot
        uic = uicmod

        QT_BINDING_VERSION = getattr(module, '__version__', '')
        QT_VERSION = core.qVersion()
        QT_BINDING_VERSION_I = _versionTuple(QT_BINDING_VERSION)
        QT_VERSION_I = _versionTuple(QT_VERSION)
        QT_MAJOR_VERSION = QT_VERSION_I[0]

        wrapInstance = shiboken.wrapInstance
        get_cpp_pointer = shiboken.getCppPointer
        unwrapInstance = lambda x: get_cpp_pointer(x)[0]
        isValidWrap = shiboken.isValid
        isInvalidWrap = lambda x: not isValidWrap(x)
        isOwnedByPython = shiboken.ownedByPython
        deleteInstance = shiboken.delete

    def _setupSubModules():
        from types import ModuleType
        modules = sys.modules
        package_name = __name__.rsplit('.', 1)[0]
        for name, value in globals().items():
            if not name.startswith('_') and isinstance(value, ModuleType):
                modules[package_name + '.' + name] = value

    def _setupQAppCompat():
        try:
            QtWidgets.qApp = QtWidgets.QApplication.instance()
        except Exception:
            QtWidgets.qApp = None

    def _initPySide():
        import PySide as module
        from PySide import QtCore as core
        from PySide import QtGui as gui
        try:
            import shiboken
        except ImportError:
            from PySide import shiboken
        try:
            import pysideuic as uicmod
        except ImportError:
            uicmod = None

        widgets = gui
        core.QAbstractProxyModel = gui.QAbstractProxyModel
        core.QSortFilterProxyModel = gui.QSortFilterProxyModel
        core.QItemSelection = gui.QItemSelection
        core.QStringListModel = gui.QStringListModel
        core.QItemSelectionModel = gui.QItemSelectionModel
        core.QItemSelectionRange = gui.QItemSelectionRange

        _setCommon('PySide', module, core, gui, widgets, shiboken, uicmod)
        _setupSubModules()

    def _initPySide2():
        import PySide2 as module
        from PySide2 import QtCore as core
        from PySide2 import QtGui as gui
        from PySide2 import QtWidgets as widgets
        try:
            import shiboken2 as shiboken
        except ImportError:
            from PySide2 import shiboken2 as shiboken
        try:
            import pyside2uic as uicmod
        except ImportError:
            uicmod = None

        if hasattr(core, 'QStringListModel'):
            gui.QStringListModel = core.QStringListModel
        else:
            core.QStringListModel = gui.QStringListModel

        _setCommon('PySide2', module, core, gui, widgets, shiboken, uicmod)
        _setupQAppCompat()
        _setupSubModules()

    def _initPySide6():
        import PySide6 as module
        from PySide6 import QtCore as core
        from PySide6 import QtGui as gui
        from PySide6 import QtWidgets as widgets
        import shiboken6 as shiboken

        gui.QStringListModel = core.QStringListModel
        widgets.QAction = gui.QAction
        widgets.QActionGroup = gui.QActionGroup

        _setCommon('PySide6', module, core, gui, widgets, shiboken, None)
        _setupQAppCompat()
        _setupSubModules()

    initializers = {
        'PySide6': _initPySide6,
        'PySide2': _initPySide2,
        'PySide': _initPySide,
    }
    binding_names = sorted(initializers, reverse=True)

    for name in binding_names:
        if name in sys.modules:
            initializers[name]()
            return

    last_error = None
    for name in binding_names:
        try:
            initializers[name]()
            return
        except ImportError as exc:
            last_error = exc
    raise ImportError('could not decide PySide binding module: %s' % last_error)


_initBinding()
del _initBinding

QWidget = QtWidgets.QWidget
QApplication = QtWidgets.QApplication
