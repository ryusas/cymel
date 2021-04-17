# -*- coding: utf-8 -*-
u"""
mel UI の :mayacmd:`layout` ラッパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..common import *
from .uitypes import *
from .control import Control

__all__ = [
    'Layout',
    'FrameLayout',
    'AutoLayout',
]

_cmds_setParent = cmds.setParent
_cmds_deleteUI = cmds.deleteUI
_cmds_layout = cmds.layout


#------------------------------------------------------------------------------
class Layout(uiParentClass('layout')):
    u"""
    mel UI の :mayacmd:`layout` ラッパークラス。

    `with` で :mayacmd:`setParent` が行える。
    この挙動は pymel より改善している
    （pymel では、必ず親に戻ってしまい元の状態には戻らない）。
    """
    UICMD = _cmds_layout  #: 対応する mel コマンドオブジェクト。

    def __enter__(self):
        cur = _cmds_setParent(q=True)
        name = self.name()
        if not getattr(self, '_lastCurrent', None) or cur != name:
            self._lastCurrent = cur
        _cmds_setParent(name)
        return self

    def __exit__(self, type, value, traceback):
        uiSetParent(self._lastCurrent)
        self._lastCurrent = None

    def exists(self):
        u"""
        UIが存在しているかどうか。

        :rtype: `bool`
        """
        return self.UICMD(self._name if (self._name == self._untrustedName) else self.name(), ex=True)

    def delete(self):
        u"""
        このレイアウトを削除する。
        """
        _cmds_deleteUI(self.name(), lay=True)

    def childNames(self):
        u"""
        子の名前リストを得る。

        :rtype: `list`
        """
        # xxxGrp を考慮して UICMD は利用しない。
        return _cmds_layout(self.name(), q=True, ca=True) or []

    def children(self):
        u"""
        子のリストを得る。

        :rtype: `list`
        """
        pre = self.name()
        # xxxGrp を考慮して UICMD は利用しない。
        names = _cmds_layout(pre, q=True, ca=True)
        if names:
            pre += '|'
            return [Control(pre + s) for s in names]
        return []

    def numChildren(self):
        u"""
          子の数を得る。

          :rtype: `int`
        """
        # xxxGrp を考慮して UICMD は利用しない。
        return _cmds_layout(self.name(), q=True, nch=True)

    def child(self, idxOrPath=0):
        u"""
          階層下のコントロールを得る。

          :param idxOrPath:
              子のインデックス（ゼロオリジン）か、
              階層下の相対パス。
          :rtype: `.Control`
        """
        name = self.name()
        pre = name + '|'
        if isinstance(idxOrPath, BASESTR):
            return Control(pre + idxOrPath)
        # xxxGrp を考慮して UICMD は利用しない。
        return Control(pre + _cmds_layout(name, q=True, ca=True)[idxOrPath])

    def clear(self):
        u"""
        子を全て削除する。
        """
        pre = self.name()
        uis = _cmds_layout(pre, q=True, ca=True)
        if uis:
            pre += '|'
            _cmds_deleteUI(*[(pre + ui) for ui in uis])

    def makeCurrent(self):
        u"""
        これをカレントペアレントにする。
        """
        _cmds_setParent(self.name())

    @staticmethod
    def pop():
        u"""
        カレントペアレントを一つ上に移動させる。
        """
        return Control(_cmds_setParent('..'))

registerTypedCls(Layout)


#------------------------------------------------------------------------------
class FrameLayout(uiParentClass('frameLayout')):
    u"""
    mel UI の :mayacmd:`frameLayout` のラッパークラス。
    """
    UICMD = cmds.frameLayout  #: 対応する mel コマンドオブジェクト。

    if MAYA_VERSION >= (2016,):
        def __new__(cls, *args, **kwargs):
            kwargs.pop('bs', None)
            kwargs.pop('borderStyle', None)
            return Layout.__new__(cls, *args, **kwargs)

registerTypedCls(FrameLayout)


#------------------------------------------------------------------------------
_FormLayout = uiClass('formLayout')


class AutoLayout(_FormLayout):
    u"""
    `.FormLayout` に自動レイアウト機能を追加したもの。
    """
    def __exit__(self, type, value, traceback):
        self.redistribute()
        super(AutoLayout, self).__exit__(type, value, traceback)

    def __new__(cls, *args, **kwargs):
        if kwargs:
            for k in _AUTOLAYOUT_OPTS:
                kwargs.pop(k, None)
        return _FormLayout.__new__(cls, *args, **kwargs)

    def __init__(
        self,
        arg0=None, horizontal=False, spacing=1, sideSpacing=None,
        reversed=False, ratios=None, adjustIndex=None,
        **kwargs
    ):
        u"""
        初期化。

        :param `bool` horizontal: 並べる方向。
        :param `int` spacing: コントロール間の空白。
        :param `int` sideSpacing:
            並び方向に対する幅の両脇のスペース。
            省略時は spacing と同じ値となる。
        :param `bool` reversed: 並びを反転するかどうか。
        :param `list` ratios:
            均等配置する為の比率。
            数に満たない分は自動的で埋められる。
        :param `int` adjustIndex:
            比率を利用せずに詰めて配置する場合、
            伸縮可能とする子のインデックスを指定する。
            インデックスは 1 から始まり、
            負数の場合は末尾からの意味になる。
        """
        super(AutoLayout, self).__init__(*([arg0] if arg0 else []), **kwargs)
        self._horizontal = horizontal
        self._spacing = spacing
        self._sideSpacing = sideSpacing
        self._reversed = reversed
        self._ratios = ratios and list(ratios) or []
        self._adjustIndex = adjustIndex

    def redistribute(self, ratios=None, adjustIndex=None):
        u"""
        子のコントロールを再配置する。

        :param `list` ratio: 配置比率を再指定出来る。
        :param `int` adjustIndex:
            詰めて配置する場合の伸縮可能インデックスを再指定出来る。
        """
        # 再指定された値の取り込み。
        if ratios:
            self._ratios = list(ratios)
        if adjustIndex:
            self._adjustIndex = adjustIndex
        else:
            adjustIndex = self._adjustIndex

        # 子を取得。
        children = self.children()
        if not children:
            return
        if self._reversed:
            children.reverse()
        num = len(children)

        # 下準備。
        if self._horizontal:
            dir0 = 'left'
            dir1 = 'right'
            af0 = 'top'
            af1 = 'bottom'
        else:
            dir0 = 'top'
            dir1 = 'bottom'
            af0 = 'left'
            af1 = 'right'

        spc = self._spacing
        sideSpc = spc if (self._sideSpacing is None) else self._sideSpacing

        afs = []
        acs = []
        aps = []
        ans = []

        # 詰めて配置する場合。
        if adjustIndex:
            bound = num - 1
            if adjustIndex < 0:
                adjustIndex = max(0, adjustIndex + num)
            else:
                adjustIndex = min(bound, adjustIndex - 1)

            for i, child in enumerate(children):
                afs.append((child, af0, sideSpc))
                afs.append((child, af1, sideSpc))

                if i is 0:
                    afs.append((child, dir0, spc))
                elif i <= adjustIndex:
                    acs.append((child, dir0, spc, children[i - 1]))
                else:
                    ans.append((child, dir0))

                if i == bound:
                    afs.append((child, dir1, spc))
                elif adjustIndex <= i:
                    acs.append((child, dir1, spc, children[i + 1]))
                else:
                    ans.append((child, dir1))

        # 比率で配置する場合。
        else:
            ratios = self._ratios[:num]
            ratios = ratios[:num]
            ratios += [1] * (num - len(ratios))
            totalPercent = 100. / float(sum(ratios))
            s = 0
            poss = []
            for v in ratios:
                s += v
                poss.append(float(s) * totalPercent)

            last = None
            for child, pos in zip(children, poss):
                afs.append((child, af0, sideSpc))
                afs.append((child, af1, sideSpc))
                if last:
                    acs.append((child, dir0, spc, last))
                else:
                    afs.append((child, dir0, spc))
                if pos:
                    aps.append((child, dir1, spc, pos))
                else:
                    ans.append((child, dir1))
                last = child

        # コマンド呼び出し。
        kwargs = dict(e=True, af=afs)
        if acs:
            kwargs['ac'] = acs
        if aps:
            kwargs['ap'] = aps
        if ans:
            kwargs['an'] = ans
        self.call(**kwargs)

_AUTOLAYOUT_OPTS = (
    'horizontal',
    'ratios',
    'reversed',
    'spacing',
    'sideSpacing',
    'adjustIndex',
)

