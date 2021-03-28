# -*- coding: utf-8 -*-
u"""
Maya操作関連。
"""
from ..common import *
from .utils import loadPlugin
import maya.OpenMaya as api1
import maya.api.OpenMaya as api2

__all__ = [
    'docmd',
    'doNothingCmd',
    'WaitCursor', 'waitCursor',
    'UndoChunk', 'undoChunk',
    'UndoTransaction', 'undoTransaction',
    'NonUndoable', 'nonUndoable',
    'PreserveSelection',
]

_waitCursor = cmds.waitCursor
_undoInfo = cmds.undoInfo
_undo = cmds.undo

if MAYA_VERSION >= (2016,):
    _setCurSel = api2.MGlobal.setActiveSelectionList
    _getCurSel = api2.MGlobal.getActiveSelectionList
else:
    _setCurSel = api1.MGlobal.setActiveSelectionList
    _1_MSelectionList = api1.MSelectionList
    _1_getActiveSelectionList = api1.MGlobal.getActiveSelectionList

    def _getCurSel():
        sel = _1_MSelectionList()
        _1_getActiveSelectionList(sel)
        return sel


#------------------------------------------------------------------------------
def docmd(do, undo, redo=None):
    u"""
    任意の callable オブジェクトを与えて undo 可能なコマンドとして実行する。

    そのままだと undo/redo が不可能な処理を undo 可能として実行することが出来る。

    :param do:
        最初の実行用の実行可能オブジェクト。
    :param undo:
        undo 用の実行可能オブジェクト。
    :param redo:
        redo 用の実行可能オブジェクト。
        省略すると do が使用される。

    >>> import maya.cmds as cmds
    >>> import cymel.main as cm
    >>> v = cmds.jointDisplayScale(q=True)
    >>> cm.docmd(lambda: cmds.jointDisplayScale(v*10), lambda: cmds.jointDisplayScale(v))
    >>> cmds.undo()
    >>> v == cmds.jointDisplayScale(q=True)
    True
    """
    if redo:
        _dopycmd(hex(id(do)), hex(id(undo)), hex(id(redo)))
    else:
        _dopycmd(hex(id(do)), hex(id(undo)))

loadPlugin('dopycmd')
_dopycmd = cmds.dopycmd


def _doNothing():
    pass
doNothingCmd = partial(docmd, _doNothing, _doNothing)  #: undoスタック1回分消費する何もしないコマンド。


#------------------------------------------------------------------------------
class WaitCursor(object):
    u"""
    ウェイトカーソルを表示するコンテキスト。

    インスタンス `waitCursor` が生成済み。

    >>> import time
    >>> import cymel.main as cm
    >>> with cm.waitCursor:
    ...     time.sleep(1)
    ...
    """
    __slots__ = ('_stack',)

    def __init__(self):
        self._stack = []

    def __enter__(self):
        state = _waitCursor(q=True, st=True)
        self._stack.append(state)
        if not state:
            _waitCursor(st=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self._stack.pop():
            _waitCursor(st=False)

waitCursor = WaitCursor()  #: `WaitCursor` の生成済みインスタンス。


#------------------------------------------------------------------------------
class UndoChunk(object):
    u"""
    1つのアンドゥチャンクを作るコンテキスト。

    インスタンス `undoChunk` が生成済み。

    >>> import maya.cmds as cmds
    >>> import cymel.main as cm
    >>> cmds.file(f=True, new=True)
    u'untitled'
    >>> cm.Transform()
    Transform('transform1')
    >>> with cm.undoChunk:
    ...     cm.Transform()
    ...     cm.Transform()
    ...
    Transform('transform2')
    Transform('transform3')
    >>> cmds.undo()
    >>> cm.Transform.ls('transform*')
    [Transform('transform1')]
    """
    __slots__ = tuple()

    def __enter__(self):
        _undoInfo(ock=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        _undoInfo(cck=True)

undoChunk = UndoChunk()  #: `UndoChunk` の生成済みインスタンス。


#------------------------------------------------------------------------------
class UndoTransaction(object):
    u"""
    コンテキストで例外が発生した場合にアンドゥするトランザクション。

    インスタンス `undoTransaction` が生成済み。
    """
    def __enter__(self):
        _undoInfo(ock=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            doNothingCmd()
            _undoInfo(cck=True)
            _undo()
        else:
            _undoInfo(cck=True)

    @classmethod
    def decorate(cls, proc):
        def wrap(*a, **k):
            with cls():
                return proc(*a, **k)
        return wrap

undoTransaction = UndoTransaction()  #: `UndoTransaction` の生成済みインスタンス。


#------------------------------------------------------------------------------
class NonUndoable(object):
    u"""
    アンドゥ不可で実行するコンテキスト。

    インスタンス `nonUndoable` が生成済み。

    >>> import maya.cmds as cmds
    >>> import cymel.main as cm
    >>> cmds.file(f=True, new=True)
    u'untitled'
    >>> with cm.undoChunk:
    ...     cm.Transform()
    ...     with cm.nonUndoable:
    ...         cm.Transform()
    ...         cm.Transform()
    ...     cm.Transform()
    ...
    Transform('transform1')
    Transform('transform2')
    Transform('transform3')
    Transform('transform4')
    >>> cmds.undo()
    >>> cm.Transform.ls('transform*')
    [Transform('transform2'), Transform('transform3')]

    .. warning::
        利用の際には、Mayaの状態に深刻な矛盾を発生させないよう
        細心の注意が必要である。

        例えば、以下のコードを実行してアンドゥことで、
        Maya を容易にクラッシュさせることが出来る。::

          cmds.createNode('transform')
          with cm.nonUndoable:
              cmds.delete()
    """
    __slots__ = ('_stack',)

    def __init__(self):
        self._stack = []

    def __enter__(self):
        state = _undoInfo(q=True, st=True)
        self._stack.append(state)
        if state:
            _undoInfo(swf=False)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._stack.pop():
            _undoInfo(swf=True)

nonUndoable = NonUndoable()  #: `NonUndoable` の生成済みインスタンス。


#------------------------------------------------------------------------------
class PreserveSelection(object):
    u"""
    元の選択状態を復元できるコンテキスト。

    >>> import maya.cmds as cmds
    >>> import cymel.main as cm
    >>> cm.Transform()
    Transform('transform1')
    >>> cm.Transform()
    Transform('transform2')
    >>> cmds.select(['transform*', 'persp'])
    >>> with cm.PreserveSelection():
    ...     cmds.delete('transform2')
    ...     cmds.select('side')
    ...
    >>> cmds.ls(sl=True)
    [u'transform1', u'persp']
    """
    __slots__ = ('nocmd', '_sel')

    def __init__(self, nocmd=False):
        u"""
        初期化。

        :param `bool` nocmd:
            コンテキストから抜ける際のセレクション復元処理を
            コマンドキューを消費せずに行うかどうか。
        """
        self.nocmd = nocmd

    def __enter__(self):
        self._sel = _getCurSel()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.nocmd:
            docmd(partial(_setCurSel, self._sel), partial(_setCurSel, _getCurSel()))
        else:
            _setCurSel(self._sel)

