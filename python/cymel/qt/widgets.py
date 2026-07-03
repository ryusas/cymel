# -*- coding: utf-8 -*-
u"""
Maya に依存しない Qt ウィジェットヘルパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import sys

from ..pyutils import IS_WINDOWS
from .binding import (
    QApplication, QT_BINDING_NAME, QT_BINDING_VERSION, QT_MAJOR_VERSION,
    QT_VERSION, Qt, QtGui, QtWidgets, QWidget,
)

__all__ = [
    'getFirstTopLevelWindow', 'showWindow', 'showAppWindow',
    'getDpiScaling', 'unscaleTextFont', 'getWidgetByPathName',
    'dumpWidgetHierarchy', 'getWidgetFullPathName',
]

_QApp_instance = QApplication.instance


#------------------------------------------------------------------------------
def getFirstTopLevelWindow():
    u"""
    表示中の最初のトップレベル QWidget を取得する。

    :rtype: `QWidget`
    """
    widgets = [
        w for w in QApplication.topLevelWidgets()
        if not w.parentWidget() and not w.isHidden()
    ]
    if widgets:
        for widget in widgets:
            if type(widget) is QWidget:
                return widget
        return widgets[0]


def showWindow(wd, deleteOnClose=True):
    u"""
    ウィジェットをウィンドウとして表示する。

    アプリケーションのメインウィンドウや
    既に表示されているトップレベルウィンドウ（最初の一つ）
    が在れば、その子になる。

    :type wd: `QWidget`
    :param wd: ウィジェット。
    :param `bool` deleteOnClose:
        閉じた時に削除されるようにするかどうか。
        WA_DeleteOnClose 属性が上書きセットされる。
    """
    parent = getFirstTopLevelWindow()
    if parent:
        wd.setParent(parent)

    wd.setWindowFlags(Qt.Window)
    wd.setAttribute(Qt.WA_DeleteOnClose, deleteOnClose)
    wd.showNormal()


def showAppWindow(proc, deleteOnClose=True, setupRoundingOnNewApp=False, traceSettings=False):
    u"""
    既存または新規の QApplication 上でウィンドウを生成して表示する。

    QApplication が未初期化なら初期化され、メインループに入りリターンされない。
    組み込み環境下ならメインウィンドウ（やトップレベルウィンドウ）の子となり、
    リターンされる。

    :param `callable` proc:
        ウィジェット型や関数など、
        ウィジェットを生成するための実行可能オブジェクト。
    :param `bool` deleteOnClose:
        閉じた時に削除されるようにするかどうか。
        WA_DeleteOnClose 属性が上書きセットされる。
    :param `bool` setupRoundingOnNewApp:
        新規に開くアプリケーションで、且つ
        Qt6 以降で devicePixelRatio が非整数のスクリーンが1つ以上在る場合に、
        HighDpiScaleFactorRoundingPolicy を RoundPreferFloor に設定する。
        QGraphicsView でアンチエイリアスを使用した場合のアーティファクトを
        回避するためである。
        ちなみに、Mayaでは QT_ENABLE_HIGHDPI_SCALING=0 が設定されているため
        devicePixelRatio はすべて 1.0 となり問題は発生しない。
    :param `bool` traceSettings:
        Qtのバージョンやアプリケーションのセッティング等をprint出力する。
    :rtype: `QWidget`
    """
    app = _QApp_instance()
    if app:
        is_new = False
    else:
        is_new = True
        app = QApplication(sys.argv)
        QtWidgets.qApp = app
        if setupRoundingOnNewApp and QT_MAJOR_VERSION >= 6:
            for screen in app.screens():
                if screen.devicePixelRatio() % 1.:
                    app.setHighDpiScaleFactorRoundingPolicy(
                        Qt.HighDpiScaleFactorRoundingPolicy.RoundPreferFloor)
                    break

    if traceSettings:
        print('# Qt %s (%s %s)' % (QT_VERSION, QT_BINDING_NAME, QT_BINDING_VERSION))
        for key, value in os.environ.items():
            if key.startswith('QT_'):
                print('# %s=%r' % (key, value))
        if hasattr(app, 'highDpiScaleFactorRoundingPolicy'):
            policy = app.highDpiScaleFactorRoundingPolicy()
            print('# highDpiScaleFactorRoundingPolicy=%s' % (
                str(policy).split('.')[-1],))

    wd = proc()
    showWindow(wd, deleteOnClose)

    if is_new:
        sys.exit(_execApp(app))
    return wd


def _execApp(app):
    func = getattr(app, 'exec_', None)
    if func is None:
        func = getattr(app, 'exec')
    return func()


#------------------------------------------------------------------------------
def getWidgetByPathName(name, base=None, separator='|', includesLayout=True):
    u"""
    objectName のパスからウィジェットまたはレイアウトを検索する。

    指定パスの間に未知のウィジェットが存在する場合も許容され、
    くまなく探索される。

    :param `str` name:
        基点から下のパス名（基点を含まない）。
    :param base:
        基点のウィジェット。
        省略時はパスの先頭の名前がトップレベルから探される。
        それでも見つからない場合は `getFirstTopLevelWindow`
        で取得されるアプリケーションのメインウィンドウとなる。
    :param `str` separator:
        パスの区切り文字。
    :param `bool` includesLayout:
        レイアウトマネージャもノードとしてカウントするかどうか。
    :rtype: `QWidget` or `QLayout`
    """
    tokens = name.split(separator)
    tokens.reverse()

    if not base:
        top_name = tokens[-1]
        for child in QApplication.topLevelWidgets():
            if child.objectName() == top_name:
                tokens.pop()
                if not tokens:
                    return child
                base = child
                break
        if not base:
            base = getFirstTopLevelWindow()
            if not base:
                raise ValueError('application main window not found')

    def recursiveFind(widget, idx):
        repeat = 1
        if includesLayout:
            try:
                layout = widget.layout()
                if layout and layout.objectName() == tokens[idx]:
                    if not idx:
                        return layout
                    idx -= 1
                    repeat = 2
            except AttributeError:
                pass

        while repeat:
            name = tokens[idx]
            for child in widget.children():
                if child.objectName() == name:
                    if not idx:
                        return child
                    res = recursiveFind(child, idx - 1)
                else:
                    res = recursiveFind(child, idx)
                if res:
                    return res
            repeat -= 1
            idx += 1

    res = recursiveFind(base, len(tokens) - 1)
    recursiveFind = None
    if res:
        return res
    raise ValueError('widget not found: ' + name)


def dumpWidgetHierarchy(base=None, indent=''):
    u"""
    ウィジェットの objectName 階層を出力する。

    :type widget: `QWidget`
    :param widget:
        基点のウィジェット。
        省略時はトップレベルから全てがダンプされる。
    :param `str` indent:
        基点のレベルのインデントスペース。
    """
    if base:
        print("%s%s '%s'" % (indent, type(base).__name__, base.objectName()))
        indent += '  '
        for child in base.children():
            dumpWidgetHierarchy(child, indent)
    else:
        for child in QApplication.topLevelWidgets():
            if not child.parentWidget():
                dumpWidgetHierarchy(child, indent)


def getWidgetFullPathName(widget, separator='|'):
    u"""
    ウィジェットの objectName パスを取得する。

    :type widget: `QWidget`
    :param widget: ウィジェット。
    :param `str` separator: パスの区切り文字。
    :rtype: `str`
    """
    paths = []
    while widget:
        paths.append(widget.objectName())
        widget = widget.parentWidget()
    paths.reverse()
    return separator.join(paths)


#------------------------------------------------------------------------------
def getDpiScaling(widget=None):
    u"""
    汎用 Qt の論理 DPI スケールを取得する。

    :rtype: `float`
    """
    app = _QApp_instance()
    if QT_MAJOR_VERSION >= 5:
        if widget:
            wnd = widget.windowHandle()
            if wnd:
                return wnd.screen().logicalDotsPerInch() / 96.
            if hasattr(QApplication, 'screenAt'):
                screen = app.screenAt(QtGui.QCursor().pos())
                return screen.logicalDotsPerInch() / 96.
            idx = app.desktop().screenNumber(QtGui.QCursor().pos())
            return app.screens()[idx].logicalDotsPerInch() / 96.
        return app.primaryScreen().logicalDotsPerInch() / 96.
    return app.desktop().logicalDpiX() / 96.



def unscaleTextFont(textCtl, height=None, pixel=11, prepare=None):
    u"""
    固定サイズテキスト用の 逆スケール値と QFont or None を得る。

    :param textCtl:
        サイズの判定に用いるテキスト系コントロール。
        boundingRect, font, setFont メソッドを備えていること。
    :param `float` height:
        フォントがポイントサイズで指定された場合の基準となる高さを指定する。
        このサイズに合わせるためのスケール値が計算される。
        デフォルトの None は、環境に応じて変わるデフォルト値を意味する。
    :param `int` pixel:
        フォントがピクセルサイズで指定された場合の基準となるサイズを指定する。
        このサイズに合わせるためのスケール値が計算される。
    :paream `callable` prepare:
        情報をキャッシュから得られなかった場合に、
        ポイントサイズによる高さを調べる前に準備（仮の描画など）が必要な場合、
        その呼出可能オブジェクトを指定する。
    :rtype: `float`, `QFont` or None
    """
    font = textCtl.font()
    key = (font.key(), height, pixel)
    res = _UNSCALE_TEXT_CACHE.get(key)
    if not res:
        size = font.pixelSize()
        if size < 0:
            if prepare:
                prepare()
            h = textCtl.boundingRect().height()
            if not height:
                height = _getDefaultTextHeight()
            if h == height:
                res = 1., None
            else:
                scale = height / h
                font.setPointSizeF(font.pointSizeF() * scale)
                res = scale, font
        else:
            if size == pixel:
                res = 1., None
            else:
                font.setPixelSize(pixel)
                res = pixel / size, font
        _UNSCALE_TEXT_CACHE[key] = res
    return res


def _getDefaultTextHeight():
    global _DEFAULT_TEXT_HEIGHT
    if _DEFAULT_TEXT_HEIGHT:
        return _DEFAULT_TEXT_HEIGHT

    app = _QApp_instance()
    font = app.font()
    point_size = font.pointSizeF()
    if point_size < 0.:
        _DEFAULT_TEXT_HEIGHT = 12. if IS_WINDOWS else 15.
    else:
        _DEFAULT_TEXT_HEIGHT = round(
            app.fontMetrics().height() * 9. / (point_size * getDpiScaling()))
    return _DEFAULT_TEXT_HEIGHT

_DEFAULT_TEXT_HEIGHT = None
_UNSCALE_TEXT_CACHE = {}
