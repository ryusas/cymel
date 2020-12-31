# -*- coding: utf-8 -*-
u"""
プラグラッパークラス。
"""
from ...common import *
from ..typeregistry import _FIX_SLOTS
from .plug_c import Plug_c
from .cyobject import CyObject
from ..datatypes import Matrix, Transformation, Vector, Quaternion
from ...utils import docmd, listEnum, correctNodeName
import maya.OpenMaya as api1
import maya.api.OpenMaya as api2

__all__ = ['Plug']

_api1_executeCommand = api1.MGlobal.executeCommand

_aliasAttr = cmds.aliasAttr
_setAttr = cmds.setAttr
_connectAttr = cmds.connectAttr
_disconnectAttr = cmds.disconnectAttr
_removeMultiInstance = cmds.removeMultiInstance
_deleteAttr = cmds.deleteAttr
_createNode = cmds.createNode
_animLayer = cmds.animLayer
_keyframe = cmds.keyframe
_connectionInfo = cmds.connectionInfo
_mute = cmds.mute

_MFn = api2.MFn
_MFn_kPairBlend = _MFn.kPairBlend
_MFn_kMute = _MFn.kMute
_MFn_kAnimLayer = _MFn.kAnimLayer
_MFn_kBlendNodeAdditiveRotation = _MFn.kBlendNodeAdditiveRotation
_MFn_kAnimCurve = _MFn.kAnimCurve

_UnitConvTypeNames = frozenset(['unitConversion', 'unitToTimeConversion', 'timeToUnitConversion'])

_STRANGE_ANIM_LAYER_CMD = MAYA_VERSION < (2018,)  # animLayer コマンドの引数指定の仕様が異なる。


#------------------------------------------------------------------------------
class Plug(Plug_c):
    u"""
    プラグラッパークラス。
    """
    if _FIX_SLOTS:
        __slots__ = tuple()

    def __lshift__(self, src):
        u"""
        プラグを接続する。
        """
        self.connect(src)

    def __rshift__(self, dst):
        u"""
        プラグを接続する。
        """
        dst.connect(self)

    def __floordiv__(self, dst):
        u"""
        プラグを切断する。
        """
        _disconnectAttr(str(self), str(dst))

    def reset(self):
        u"""
        デフォルト値にリセットする。
        """
        self.set(self.default())

    def setAlias(self, name=None):
        u"""
        プラグの別名を設定、又は削除する。

        :param `str` name:
            設定する別名。
            None や空文字を指定すると、既存の設定を削除する。
        """
        if name:
            _aliasAttr(name, self.name())
        else:
            _aliasAttr(self.name(), rm=True)

    def set(self, val, safe=False):
        u"""
        アトリビュート値を内部単位でセットする。

        None を指定することで、
        データ型アトリビュートの Null もセットできる。
        もちろん undo も可能。

        :param val: セットする値。
        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 などの数値系コンパウンドの場合は
            セットできる箇所だけセットされる。
            セットに失敗したアトリビュートの数が返される。
        :rtype: None or `int`
        """
        if self.isArray():
            raise RuntimeError("The attribute '%s' is a multi. Its values must be set individually." % self.name_())

        # None の場合は、APIを使った疑似コマンドでセットする。
        if val is None:
            do = self.apiGetSetNullProc()
            undo = self.apiGetUndoSetProc()
            if safe:
                try:
                    docmd(do, undo)
                except:
                    return 1
                return 0
            else:
                docmd(do, undo)

        # 通常の値の場合は、setAttr コマンドでセットする。
        else:
            subType = self.subType()
            typename = self.type()
            if subType and not typename.startswith(subType):
                typename += subType

            if safe:
                try:
                    _setRawValue(self.name_(), typename, val)
                except:
                    # 個々のセット操作をオーバーライド可能なように、きちんと Plug を呼び出す。
                    if subType:
                        n = 0
                        for p, v in zip(self.children(), val):
                            try:
                                p.set(v)
                            except:
                                n += 1
                        return n
                    return 1
                return 0
            else:
                _setRawValue(self.name_(), typename, val)

    def setu(self, val, safe=False):
        u"""
        アトリビュート値をUI設定単位でセットする。

        None を指定することで、
        データ型アトリビュートの Null もセットできる。
        もちろん undo も可能。

        :param val: セットする値。
        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 などの数値系コンパウンドの場合は
            セットできる箇所だけセットされる。
            セットに失敗したアトリビュートの数が返される。
        :rtype: None or `int`
        """
        if self.isArray():
            raise RuntimeError("The attribute '%s' is a multi. Its values must be set individually." % self.name_())

        # None の場合は、APIを使った疑似コマンドでセットする。
        if val is None:
            do = self.apiGetSetNullProc()
            undo = self.apiGetUndoSetProc()
            if safe:
                try:
                    docmd(do, undo)
                except:
                    return 1
                return 0
            else:
                docmd(do, undo)

        # 通常の値の場合は、setAttr コマンドでセットする。
        else:
            if safe:
                name = self.name()
                try:
                    _setUnitValue(name, self.type(), val)
                except:
                    # 個々のセット操作をオーバーライド可能なように、きちんと Plug を呼び出す。
                    if self.subType():
                        n = 0
                        for p, v in zip(self.children(), val):
                            try:
                                p.setu(v)
                            except:
                                n += 1
                        return n
                    return 1
                return 0
            else:
                _setUnitValue(self.name(), self.type(), val)

    def connect(
        self, src,
        force=False, f=False,
        lock=False, l=False,
        nextAvailable=False, na=False,
    ):
        u"""
        指定プラグからこのプラグへ接続する。

        いかなる場合でも完全な undo をサポートしている。

        常に出力側プラグが返され、
        nextAvailable が False の場合はこのプラグ、
        True の場合は決定した要素プラグとなる。

        :type src: `Plug`
        :param src: 入力元のアトリビュート。
        :param `bool` f|force:
            他の接続やロックなどのエラー要因を回避して接続する。
        :param `bool` l|lock:
            接続後にロックする。
        :param `bool` na|nextAvailable:
            次に利用可能なインデックスに接続する。
            isIndexMatters 設定に限らず利用できる。
            接続された要素プラグが返される。
        :rtype: `Plug` or None

        .. note::
            オプション指定は出来ないが、
            演算子 << でも同様の操作が可能。

        .. warning::
            `disconnect` と統一性を持たせるため、
            出力に対して入力を指定する仕様になっており、
            pymel の connect とは指定方向が逆である。
            pymel と同じ指定方向のものとして
            `connectTo` も利用できる。
        """
        force |= f
        lock |= l
        nextAvailable |= na
        if not self.isArray():
            nextAvailable = False

        # force ではないとき、ロックされていたらエラー。
        if not force and self.isLocked():
            raise RuntimeError('attribute is locked: ' + self.name_())

        # undo可能なように要素の追加を保証。
        addedSrcs = src.addElement()
        addedDsts = self.addElement()

        # コネクト済みならエラー。
        if not(nextAvailable or addedSrcs or addedDsts) and src.isConnectedTo(self):
            raise RuntimeError("already connected: %s -> %s" % (src, self))

        # 一時的なロックの解除。
        if force and not self.isNodeFromReferencedFile():
            tmpUnlocked = self.unlock(undoable=False)
        else:
            tmpUnlocked = EMPTY_TUPLE

        # nextAvailable をコマンド任せにすると undo できないので自前でやる。
        # （要素の追加だけでなく、コネクション自体も undo されない…）
        # ロック箇所も回避する（上位がロックされていなことは、force やエラーで保証済み）。
        if nextAvailable:
            self = self.nextAvailable(asPlug=True, checkLocked=True)
            if self.addElement():
                addedDsts.append(self)

        # 実行。
        try:
            _connectAttr(src.name_(), self.name_(), f=force)
        except:
            for p in addedSrcs:
                p.removeElement()
            for p in addedDsts:
                p.removeElement()
            raise
        else:
            if lock and self not in tmpUnlocked:
                _setAttr(self.name_(), l=True)

        # 一時的に解除されたロックの復元。
        finally:
            for x in tmpUnlocked:
                if x.isValid():
                    x.apiSetLocked(True)
        return self

    def connectTo(self, dst, **kwargs):
        u"""
        このプラグから指定プラグへ接続する。

        :type dst: `Plug`
        :param dst: 出力先のアトリビュート。
        :param kwargs: その他に `connect` のオプションを指定可能。
        :rtype: `Plug`

        .. note::
            オプション指定は出来ないが、
            演算子 >> でも同様の操作が可能。
        """
        return dst.connect(self, **kwargs)

    def disconnect(
        self, src=None,
        force=False, f=False,
        nextAvailable=False, na=False,
    ):
        u"""
        入力コネクションを切断する。

        いかなる場合でも完全な undo をサポートしている。

        nextAvailable が False の場合は
        切断した入力側プラグが返され、
        True の場合は出力側プラグのリストが返される。

        :type src: `Plug`
        :param src: 切断する入力プラグ。省略可能。
        :param `bool` f|force:
            ロックされていても極力エラーを回避して切断する
            （一時的にアンロックして元に戻す）。
        :param `bool` na|nextAvailable:
            マルチプラグと src を指定した場合に、
            接続されている要素を探して切断する。
            複数あれば全て切断され、そのリストが返される。
            isIndexMatters 設定に限らず利用できる。
        :rtype: `Plug` or `list`

        .. note::
            オプション指定は出来ないが、
            演算子 // でも同様の操作が可能。
        """
        force |= f
        if src:
            if (nextAvailable or na) and self.isArray():
                if src.longName() == 'output' and src.nodeType() in _UnitConvTypeNames:
                    pairs = self.connections(True, False, asPair=True)
                else:
                    pairs = self.connections(True, False, scn=True, asPair=True)
                res = [d._disconnect(s, force) for d, s in pairs if s == src]
                if not res:
                    raise RuntimeError('connection not found: %s -> %s[*]' % (src.name_(), self.name_()))
                return res
        else:
            src = self.connections(True, False, scn=True)
            if not src:
                raise RuntimeError('input connection not found: ' + self.name_())
            src = src[0]
        self._disconnect(src, force)
        return src

    def _disconnect(self, src, force):
        # 一時的なロックの解除。
        if force and not self.isNodeFromReferencedFile():
            tmpUnlocked = self.unlock(undoable=False)
        else:
            tmpUnlocked = EMPTY_TUPLE

        # 実行。
        try:
            _disconnectAttr(src.name_(), self.name_())
        except:
            raise

        # 一時的に解除されたロックの復元。
        finally:
            for x in tmpUnlocked:
                if x.isValid():
                    x.apiSetLocked(True)
        return self

    def toggle(self):
        u"""
        アトリビュート値をトグルする。

        現在の値の否定をセットするだけなので、
        型が bool でなくとも動作はする。

        :rtype: `bool`
        """
        v = not self.get()
        self.set(v)
        return v

    def setCaching(self, val, leaf=False):
        u"""
        Caching フラグを設定する。

        :param `bool` val: True だと有効、 False だと無効。
        :param `bool` leaf:
            プラグがコンパウンドの場合に True にすると、そのプラグは
            処理されず、コンパウンド階層のリーフが探され纏めて処理される。
        """
        self._setAttrFlags(leaf, ca=val)

    setCached = setCaching  # `setCaching` の別名。

    def setChannelBox(self, val, leaf=False):
        u"""
        Keyable でなくてもチャンネルボックスに出すかどうかを設定する。

        :param `bool` val: True だと有効、 False だと無効。
        :param `bool` leaf:
            プラグがコンパウンドの場合に True にすると、そのプラグは
            処理されず、コンパウンド階層のリーフが探され纏めて処理される。
        """
        self._setAttrFlags(leaf, cb=val)

    def setKeyable(self, val, leaf=False):
        u"""
        Keyable フラグを設定する。

        :param `bool` val: True だと有効、 False だと無効。
        :param `bool` leaf:
            プラグがコンパウンドの場合に True にすると、そのプラグは
            処理されず、コンパウンド階層のリーフが探され纏めて処理される。
        """
        self._setAttrFlags(leaf, k=val)

    def setLocked(self, val=True, leaf=False):
        u"""
        ロック、又はアンロックする。

        :param `bool` val: True だとロック、 False だとアンロック。
        :param `bool` leaf:
            プラグがコンパウンドの場合に True にすると、そのプラグは
            処理されず、コンパウンド階層のリーフが探され纏めて処理される。

        .. note::
            アンロックの場合は、プラグ階層上位や下位に対しても保証できる
            `unlock` メソッドが便利である。
        """
        self._setAttrFlags(leaf, l=val)

    lock = setLocked  #: `setLocked` の別名。

    def _setAttrFlags(self, leaf=False, **flagdict):
        u"""
        :mayacmd:`setAttr` コマンドでフラグをセットする汎用メソッド。

        :param `bool` leaf:
            プラグがコンパウンドの場合に True にすると、そのプラグは
            処理されず、コンパウンド階層のリーフが探され纏めて処理される。
        :param flagdict:
            :mayacmd:`setAttr` コマンドに渡すフラグ辞書。
        """
        # setAttr コマンドの undo バグ回避の為。
        has_k = 'k' in flagdict
        if has_k and flagdict['k']:
            # NOTE: k=True にする場合、「事前」に cb=False しないと undo で cb=True 状態に戻れなくなる。
            def set_flags(plug):
                name = plug.name_()
                if plug.isChannelBox():
                    _setAttr(name, cb=False)  # 事前。
                _setAttr(name, **flagdict)

        #elif flagdict.get('cb') and not has_k:
        elif 'cb' in flagdict and flagdict['cb'] and not has_k:
            # NOTE: cb=True にする場合、「同時」に k=False しないと undo で k=True 状態に戻れなくなる。
            def set_flags(plug):
                if plug.isKeyable():
                    _setAttr(plug.name_(), k=False, **flagdict)  # 同時。
                else:
                    _setAttr(plug.name_(), **flagdict)

        else:
            # 上記の条件に該当しなければ普通にセットして大丈夫。
            def set_flags(plug):
                _setAttr(plug.name_(), **flagdict)

        if leaf:
            def recursive(plug):
                if plug.isCompound():
                    for i in range(plug.numChildren()):
                        # NOTE: Array を想定していないから child を直接使っても危険ではないということにする。
                        recursive(plug.child(i))
                else:
                    set_flags(plug)
            recursive(self)
        else:
            set_flags(self)

    def unlock(self, below=False, undoable=True):
        u"""
        このプラグと階層上位や、下位（オプション）のプラグをアンロックする。

        実際にアンロックされたプラグが上位から並んだリストが返される。

        :param `bool` below: これより下層もアンロックする。
        :param `bool` undoable: undoの可否。
        :rtype: `list`

        .. note::
            ロック状態は上位から引き継がれるので、
            上層をアンロックせずに下層の判定はできない。
        """
        # isLocked は上位の影響を受け、そのプラグ自体の状態は分からないため、
        # まず、上位に向けロックされていなくなるまでプラグを収集。
        queue = []
        plug = self
        while plug.isLocked():
            queue.append(plug)
            if plug.isElement():
                plug = plug.array()
            elif plug.isChild():
                plug = plug.parent()
            else:
                break

        unlock = _unlockCmd if undoable else _unlockApi

        # このプラグから上位を上から順に「本当にロックされているもの」をアンロック。
        if queue:
            queue.reverse()
            results = [unlock(p) for p in queue if p.isLocked()]
        else:
            results = []

        # 下流もアンロックする。
        if below:
            for p in self.iterHierarchy():
                if p.isLocked():
                    results.append(unlock(p))
        return results

    def addElement(self, idx=None):
        u"""
        undo可能な形でマルチアトリビュート要素を追加する。

        上層の存在の有無も調べられ、
        存在していない箇所の追加と undo も保証する。

        処理したプラグが下位から並んだリストが返される
        （既に存在している場合は空リストとなる）。

        :param `int` idx:
            自身がマルチのとき、調べるインデックスを指定する。
            自身が要素（実在は不明）のときは省略できる。
            省略してもしなくても上位はチェックされる。
        :rtype: `list`
        """
        # 上位に遡り、要素プラグを集める。
        if idx is not None:
            plugs = [self[idx]]
            plug = self
        elif self.isElement():
            plugs = [self]
            plug = self.array()
        else:
            plugs = []
            plug = self
        while plug.isChild():
            plug = plug.parent()
            if plug.isElement():
                plugs.append(plug)
                plug = plug.array()
        plugs.reverse()

        # 上位から順に存在を調べ、存在していないところからのキューを得る。
        # 上位より先に下位を調べると、それによって上位が作られてしまうので、上位から調べる必要がある。
        queue = None
        for i, p in enumerate(plugs):
            if not p.elementExists():
                queue = plugs[i:]
                break
        if queue is None:
            return []

        # 上から順に並んだキューを元に「評価」と「削除」をコマンド化して呼び出す。
        _addElement(queue)

        queue.reverse()
        return queue

    def remove(self, b=False, f=False, force=False):
        u"""
        自身がマルチアトリビュートの要素プラグの場合にそれを削除する。

        `removeElement` にインデックスを指定しない場合と同じだが、
        こちらの場合は要素プラグ以外で使用するとエラーになる。

        削除された要素の数が返される。
        ただし、それにはアトリビュート階層下の
        マルチアトリビュート要素の数も含まれる。

        :param `bool` b:
            コネクションがあってもエラーにならずに削除する。
        :param `bool` f|force:
            コネクションだけでなく、ロックされていたりなどの
            エラー要因を可能な限り回避する。
            こちらのオプションだけで b=True も兼ねる。
        :rtype: `int`
        """
        if not self.isElement():
            raise ValueError('plug is not an element: ' + self.name_())
        self._removeElement(b, f or force)

    def removeAllElements(self, b=False, f=False, force=False):
        u"""
        自身がマルチアトリビュートのマルチプラグの場合にその全要素を削除する。

        `removeElement` にインデックスを指定しない場合と同じだが、
        こちらの場合はマルチプラグ以外で使用するとエラーになる。

        削除された要素の数が返される。
        ただし、それにはアトリビュート階層下の
        マルチアトリビュート要素の数も含まれる。

        :param `bool` b:
            コネクションがあってもエラーにならずに削除する。
        :param `bool` f|force:
            コネクションだけでなく、ロックされていたりなどの
            エラー要因を可能な限り回避する。
            こちらのオプションだけで b=True も兼ねる。
        :rtype: `int`
        """
        if not self.isArray():
            raise ValueError('plug is not an array: ' + self.name_())
        self._removeElement(b, f or force)

    def removeElement(self, idx=None, b=False, f=False, force=False):
        u"""
        マルチアトリビュートの要素を削除する。

        削除された要素の数が返される。
        ただし、それにはアトリビュート階層下の
        マルチアトリビュート要素の数も含まれる。

        :param `int` idx:
            自身がマルチのとき、削除するインデックスを指定する。
            省略すると、自身が要素ならそれが、
            マルチなら全ての要素が削除される。
        :param `bool` b:
            コネクションがあってもエラーにならずに削除する。
        :param `bool` f|force:
            コネクションだけでなく、ロックされていたりなどの
            エラー要因を可能な限り回避する。
            こちらのオプションだけで b=True も兼ねる。
        :rtype: `int`
        """
        if idx is None:
            self._removeElement(b, f or force)
        else:
            self[idx]._removeElement(b, f or force)

    def _removeElement(self, breakConn, force):
        isRefNode = self.isNodeFromReferencedFile()
        isArray = self.isArray()

        # force でコネクションがある場合は、このプラグの上位と、下流の接続先プラグとその上位を一時的にアンロックする。
        # （ロックそのものはエラーにならないが、コネクションがロックされているとエラーになる）
        # この操作は undo 可能でないと、条件によってはコネクションが復元されないようだ。
        tmpUnlocked = []
        if force:
            breakConn = True
            for dst in self.connections(False, True):
                if not dst.isNodeFromReferencedFile():
                    tmpUnlocked.extend(dst.unlock())
            if not isRefNode and (tmpUnlocked or self.isDestination(below=True)):
                tmpUnlocked.extend(self.unlock())

        # undoで状態が完全に戻るようにする対策。
        # 下位の本当にロックされているプラグをアンロックする。
        # 下位のコネクションの無い要素プラグを下層から順に削除操作対象にする。
        if isRefNode:
            thisUnlocked = EMPTY_TUPLE
            queue = [p for p in self.iterHierarchy(evaluate=True) if p.isElement() and not p.isConnected()]
        else:
            queue = list(self.iterHierarchy(evaluate=True))
            # このプラグ以下のロック判別のために上位を一時的にアンロックし、
            # 下位の本当にロックされているプラグをアンロックする。
            uppers = self.unlock()
            thisUnlocked = [_unlockCmd(p) for p in queue if p.isLocked()]
            if uppers:
                for x in uppers:
                    x.apiSetLocked(True)
                if uppers[-1] == self:
                    _unlockCmd(self)
                    thisUnlocked.insert(0, self)
            queue = [p for p in queue if p.isElement() and not p.isConnected()]
        queue.reverse()

        #print('tmpUnlocked=%r' % (tmpUnlocked,))
        #print('thisUnlocked=%r' % (thisUnlocked,))
        #print('removeElems=%r' % (queue,))

        # 下位から順に削除。
        try:
            removedElems = []
            name = None
            for plug in queue:
                name = plug.name_()
                _removeMultiInstance(name, b=breakConn)
                removedElems.append(plug)

        # エラー発生時の処理。
        except Exception as err:
            # 既に削除したものを復元。
            if removedElems:
                removedElems.reverse()
                _addElement(removedElems)
            # undo時の復元保証のためにアンロックしたものを復元。
            for x in thisUnlocked:
                _setAttr(x.name_(), l=True)

            # コマンドのメッセージだと格好悪いので自身のエラーに変更。
            if 'connected' in err.message:
                if not isArray or not name:
                    name = self.name_()
                raise RuntimeError('attribute is connected: ' + name)
            raise

        # 一時的に解除したロックの復元。
        finally:
            for x in tmpUnlocked:
                if x.isValid():
                    _setAttr(x.name_(), l=True)

        return len(queue)

    def delete(self, force=False):
        u"""
        ダイナミックアトリビュートを削除する。

        :param `bool` f|force:
            コネクションがあったり、ロックされていたりなどの
            エラー要因を回避して削除する。
        """
        if self.isElement():
            raise ValueError('plug is an element: ' + self.name_())
        #if not self.isDynamic():
        #    raise ValueError('attribute is not dynamic: ' + self.name_())

        isRefNode = self.isNodeFromReferencedFile()

        # force でコネクションがある場合は、このプラグの上位と、下流の接続先プラグとその上位を一時的にアンロックする。
        # この操作は undo 可能でないと、条件によってはコネクションが復元されないようだ。
        tmpUnlocked = []
        if force:
            if not isRefNode:
                tmpUnlocked = self.unlock()
            for dst in self.connections(False, True):
                if not dst.isNodeFromReferencedFile():
                    tmpUnlocked.extend(dst.unlock())
        elif self.isLocked():
            raise RuntimeError('attribute is locked: ' + self.name_())

        # undoで状態が完全に戻るようにする対策。
        # 下位の本当にロックされているプラグをアンロック。
        # 下位のコネクションの無い要素プラグを下層から順に削除操作対象にする。
        if isRefNode:
            thisUnlocked = EMPTY_TUPLE
            queue = [p for p in self.iterHierarchy(evaluate=True) if p.isElement() and not p.isConnected()]
        else:
            queue = list(self.iterHierarchy(evaluate=True))
            thisUnlocked = [_unlockCmd(p) for p in queue if p.isLocked()]
            queue = [p for p in queue if p.isElement() and not p.isConnected()]
        queue.reverse()

        #print('tmpUnlocked=%r' % (tmpUnlocked,))
        #print('thisUnlocked=%r' % (thisUnlocked,))
        #print('removeElems=%r' % (queue,))

        # 下位の要素から順に削除。
        try:
            removedElems = []
            for plug in queue:
                _removeMultiInstance(plug.name_(), b=True)
                removedElems.append(plug)
            _deleteAttr(self.name_())

        # エラー発生時の処理。
        except Exception as err:
            # 既に削除したものを復元。
            if removedElems:
                removedElems.reverse()
                _addElement(removedElems)
            # undo時の復元保証のためにアンロックしたものを復元。
            for x in thisUnlocked:
                _setAttr(x.name_(), l=True)
            raise

        # 一時的に解除したロックの復元。
        finally:
            for x in tmpUnlocked:
                if x.isValid():
                    _setAttr(x.name_(), l=True)

    def iterHierarchy(self, evaluate=False, connected=False, checker=gettrue):
        u"""
        プラグ階層下（マルチ要素、コンパウンドの子）をイテレーションする。

        :param `bool` evaluate:
            マルチ要素を収集する際、マルチプラグを評価する。
        :param `bool` connected:
            マルチ要素を収集する際、コネクションを元にする。
        :param `callable` checker:
            プラグを1つ受け `bool` を返す関数を指定する。
            False を返すところから下層には降りない。
        """
        if checker(self):
            yield self
        else:
            return

        if self.isArray():
            if connected:
                queue = self.connectedElements()
            else:
                if evaluate:
                    self.evaluateNumElements()
                queue = self.elements()
        elif self.isCompound():
            queue = self.children()
        else:
            return

        for plug in queue:
            for plug in plug.iterHierarchy(evaluate, connected):
                yield plug

    def iterElements(self, start=None, end=None, step=1, all=False, infinite=False):
        u"""
        マルチアトリビュート要素をイテレーションする。

        Python のスライスと同じ感覚で、開始、終了、ステップを指定する。
        それぞれ負数を指定することも可能。

        全ての引数を省略すると、存在する全要素がイテレーションされる。

        :param `int` start:
            開始する論理インデックスを指定する。
            負数を指定すると、存在する要素の末尾のインデックスを -1 として
            さかのぼった位置になる。
            省略時(None)は、存在する要素の開始点となる
            （stepが正の場合は最小インデックス、負の場合は最大インデックス）。
        :param `int` end:
            終了する論理インデックスを指定する。
            実際に取得されるのはこの1つ前の位置までである。
            負数を指定すると、存在する要素の末尾のインデックスを -1 として
            さかのぼった位置になる。
            省略時(None)は、存在する要素の終了点の1つ先の位置となる
            （stepが正の場合は最小インデックス-1、負の場合は最大インデックス+1）。
        :param `int` step:
            インデックスのステップ数を指定する。
        :param `bool` all:
            要素が存在するかどうかにかかわらず得るかどうか。
            infinite=True の場合は all=True ともみなされる。
        :param `bool` infinite:
            要素が存在するかどうかにかかわらず得るとともに、
            end を無視し、無限にイテレーションする。
            ただし、step が負の場合は 0 未満にはならない。
            step が正の場合は無限ループに注意。
        """
        if abs(step) < 1:
            raise RuntimeError('invalid step: ' + str(step))

        # start の解釈。
        if start is None:
            indices = self.indices()
            idx = indices[-1 if step < 0 else 0] if indices else 0
        elif start < 0:
            indices = self.indices()
            idx = (start + indices[-1] + 1) if indices else 0
        else:
            indices = None
            idx = max(0, start)

        # 無限の場合（要素が存在するかどうかも関係ない）。
        if infinite:
            while idx >= 0:
                yield self[idx]
                idx += step

        # 無限でない場合。
        else:
            # end の解釈。
            if end is None:
                if indices is None:
                    indices = self.indices()
                if not indices:
                    end = 0
                elif step < 0:
                    end = indices[0] - 1
                else:
                    end = indices[-1] + 1
            elif end < 0:
                if indices is None:
                    indices = self.indices()
                end = (end + indices[-1] + 1) if indices else 0

            # 要素が存在するかどうか関係ない場合。
            if all:
                if step < 0:
                    while idx > end:
                        yield self[idx]
                        idx += step
                else:
                    while idx < end:
                        yield self[idx]
                        idx += step

            # 存在する要素のみの場合。
            elif indices:
                # 効率化のため、step == abs(1) の場合は、indices をスライスしてイテレーションする。
                if step == 1:
                    n = len(indices)
                    s = 0
                    while s < n and indices[s] < idx:
                        s += 1
                    e = n
                    while 0 < e and end <= indices[e - 1]:
                        e -= 1
                    for idx in indices[s:e]:
                        yield self[idx]

                elif step == -1:
                    print(idx, end, indices)
                    n = len(indices)
                    s = n - 1
                    while 0 < s and idx < indices[s]:
                        s -= 1
                    e = -1
                    while e < n and indices[e + 1] <= end:
                        e += 1
                    for idx in (indices[s::-1] if e < 0 else indices[s:e:-1]):
                        yield self[idx]

                # 効率を考えなければ、基本的にはこれでいける。
                else:
                    indicesSet = frozenset(indices)
                    if step < 0:
                        while idx > end:
                            if idx in indicesSet:
                                yield self[idx]
                            idx += step
                    else:
                        while idx < end:
                            if idx in indicesSet:
                                yield self[idx]
                            idx += step

    def listEnum(self, reverse=False):
        u"""
        enum アトリビュートの名前と値のペアのリストを得る。

        :param `bool` reverse:
            ペアの並び順を入れ替え、
            (名前, 値) ではなく (値, 名前) にする。
        :rtype: `list`
        """
        if self.isDynamic():
            return listEnum(self.name_(), None, reverse)
        else:
            return listEnum(self.nodeType(), self.shortName(), reverse)

    def animLayers(self, selected=False, exact=False):
        u"""
        プラグが属するアニメーションレイヤー名リストを得る。

        `layeredPlug` に all=True を指定した場合と同様に
        レイヤー並びの降順に得られる。

        :param `bool` selected:
            セレクト状態のレイヤーに限定する。
            ただし、ベースレイヤーだけは、
            デフォルトでは状態にかかわらず得られる。
        :param `bool` exact:
            selected=True の場合に、
            ベースレイヤーもセレクト状態に限定するかどうか。
        :rtype: `list`
        """
        self = self.proxyMaster()
        results = []

        # レイヤーによるブレンドチェーンを遡って探索する。
        cons = self.inputs(checkChildren=False)
        while cons:
            # 入力がレイヤー以外の何かだった場合の振り替え。
            con = cons[0]
            if con.hasNodeFn(_MFn_kPairBlend):
                cons = _pairBlendInput(con).inputs(checkChildren=False)
                continue
            elif con.hasNodeFn(_MFn_kMute):
                cons = con.node().plug_('i').inputs(checkChildren=False)
                continue

            # 入力ソースの .msg 出力をチェック。
            blend = con.node()
            cons = blend.plug_('msg').outputs(checkChildren=False)
            if not cons:
                break

            # .msg 出力先に animLayer ノードが在れば、それを取得。このノードはブレンドノードであるとする。
            layer = None
            for c in cons:
                if c.hasNodeFn(_MFn_kAnimLayer):
                    layer = c.nodeName()
                    break
            if not layer:
                # 予期しないノードで塞がれている場合は、探索を終了。
                break

            # そのレイヤーが条件に合致すれば、それを得る。
            if not selected or _animLayer(layer, q=True, sel=True):
                results.append(layer)

            # アトリビュート名のサフィックスを決定。
            if blend.hasFn(_MFn_kBlendNodeAdditiveRotation):
                xyz = self.shortName()[-1]
            else:
                xyz = ''

            # さらに手前の入力ソースを検索。
            cons = blend.plug_('ia' + xyz).inputs(checkChildren=False)  # .ia がそのレイヤー手前の入力。

        # ベースレイヤーを追加。
        layer = _animLayer(q=True, root=True)
        if layer and (not(selected and exact) or _animLayer(layer, q=True, sel=True)):
            results.append(layer)

        return results

    def layeredPlug(
        self, layer=None, selected=False, exact=False, best=False, all=False,
        asPair=False, allowNonLayer=False
    ):
        u"""
        アニメーションレイヤーによる代理プラグを得る。

        allowNonLayer=True とすることで、
        アニメーションレイヤーが使われていなくても
        その他の仕組み（
        :mayanode:`pairBlend` と :mayanode:`mute` を想定
        ）による代理プラグを得る手段としても利用できる。

        オプションの組み合わせ例を以下に示す。

        * 属する最上位のレイヤーのプラグを得る : デフォルト
        * 現在の状態でキーを打つ際に対象となるレイヤーのプラグを得る : best=True
        * ベースレイヤーのプラグを得る : layer=''
        * プラグが属する全レイヤーのプラグを得る : all=True
        * プラグが属する選択レイヤーの上位のものを得る : selected=True
        * プラグが属する選択レイヤーの全てを得る : all=True, selected=True
        * 指定レイヤーに属していればそのプラグを得る : layer="レイヤー名", exact=True
        * 指定レイヤーに属していればそのプラグ、そうでなければ上位から順次検索 : layer="レイヤー名"
        * 指定レイヤーに属しており選択状態であればそのプラグを得る : layer="レイヤー名", selected=True, exact=True
        * 指定レイヤーに属しており選択状態であればそのプラグ、そうでなければ順次検索 : layer="レイヤー名", selected=True

        :param `str` layer:
            検索するアニメーションレイヤー。

            デフォルトの None では、プラグが属するレイヤーを上位から優先して検索する。
            ""（空文字列）を指定すると、ベースレイヤーを指定することと同義になる。

            プラグが指定レイヤーに属していなかった場合、デフォルト動作では、
            属するレイヤーが上位から順次検索される。
            つまり、 `animLayers` と同様に、レイヤーエディターの並び順で得られる。

        :param `bool` selected:
            検索対象のレイヤーをセレクト状態のものに限定する。

            layer が指定された場合、そのレイヤーがセレクト状態である場合に絞り込む。

            layer が指定されない場合や、レイヤーがセレクト状態でなかったり
            プラグがメンバーでなかった場合に、順次検索されるレイヤーに対しても
            セレクト状態のもののみに絞り込む。

        :param `bool` exact:
            layer や selected オプションを修飾する。

            デフォルトの False の場合、プラグが指定レイヤーのメンバーでない場合は
            他のレイヤーやベースレイヤーも順次探索される。
            また、selected が指定されていても、レイヤーを順次探索した結果の最後と
            してのベースレイヤーについてはセレクト状態を問わない。

            True を指定すると厳密な動作となり、
            layer 指定時は、プラグがそのメンバーでなければ None が返される。
            また、レイヤーを順次探索した結果の最後のベースレイヤーについても
            selected フラグがチェックされるようになる。

        :param `bool` best:
            現在の状態でのキーを打つ対象となるレイヤーのプラグを得る。

        :param `bool` all:
            True を指定すると戻り値は必ず `list` となる。

            layer が指定されないか、指定したレイヤーのメンバーでないか selected フラグが
            一致しないかで、所属レイヤーが順次検索される場合の動作を変更する。
            デフォルトの False では、layer が None か "" かにより、
            上位優先で最初に見つけたレイヤーか最後のベースレイヤーのどれか一つのプラグが
            返される。 True を指定すると、順次検索した全てレイヤー（selected チェックでの
            絞り込みはされる）のプラグが取得される。

        :param `bool` asPair:
            True を指定すると `Plug` と、それが対応するレイヤー名のペアが返される。

        :param `bool` allowNonLayer:
            プラグがベースレイヤーにしか属しておらず（レイヤーブレンドされていない）、
            それ以外のスイッチ系のノードが挟まっている場合、その入力プラグを得る。
            :mayanode:`pairBlend` と :mayanode:`mute` を想定している。

        :returns: `Plug` や (`Plug`, `str`) 、又はそれらの `list`
        """
        self = self.proxyMaster()

        selfName = self.name_()
        pcls = type(self)

        # best オプションが指定された場合 layer を得る。
        if best:
            s = layer
            layer = _animLayer(selfName, q=True, bl=True)
            if s is not None and s != layer:
                return [] if all else None

        # レイヤー指定された場合、そのプラグを探す。
        isBaseLayer = False
        if layer is not None:
            # selected オプションが指定された場合、指定レイヤーがセレクト状態でなければ None を返す。
            if selected:
                if layer:
                    if not _animLayer(layer, q=True, sel=True):
                        return [] if all else None
                    isBaseLayer = layer == _animLayer(q=True, root=True)
                else:
                    layer = _animLayer(q=True, root=True)
                    # ベースレイヤーが存在しない場合は非セレクト状態ともみなす。
                    if not(layer and _animLayer(layer, q=True, sel=True)):
                        return [] if all else None
                    isBaseLayer = True
            else:
                isBaseLayer = not layer or layer == _animLayer(q=True, root=True)

            # ベースレイヤー以外のレイヤー指定の場合、プラグを探す（ベースレイヤーは -lp ではクエリ出来ない）。
            if isBaseLayer:
                selected = False  # ベースレイヤーのセレクト状態は既に判定済みな為、チェックを省略出来る。
            else:
                if _STRANGE_ANIM_LAYER_CMD:
                    plugName = _animLayer(selfName, layer, q=True, lp=True)  # けったいな引数指定順。
                else:
                    plugName = _animLayer(layer, q=True, lp=selfName)
                if plugName:
                    p = pcls(plugName)
                    if asPair:
                        p = (p, layer)
                    return [p] if all else p

                # exact オプションが指定された場合は、メンバーでないなら None を返す。
                if exact:
                    return [] if all else None

        # ここまでで以下のケースが残る:
        #  - レイヤー指定されていない
        #  - レイヤー指定されたがメンバーでなかった (レイヤー指定されていない場合と同様に扱う)
        #  - ベースレイヤーが指定された (selectedチェック済み)

        # レイヤーによるブレンドチェーンを遡って探索する。
        result = [] if all else None
        plug = self
        cons = plug.inputs(checkChildren=False)
        while cons:
            # 入力がレイヤー以外の何かだった場合の振り替え。
            con = cons[0]
            if con.hasNodeFn(_MFn_kPairBlend):
                if allowNonLayer:
                    plug = _pairBlendInput(con, pcls)
                    cons = plug.inputs(checkChildren=False)
                else:
                    cons = _pairBlendInput(con).inputs(checkChildren=False)
                continue
            p_ = con.node().plug_
            if con.hasNodeFn(_MFn_kMute):
                if allowNonLayer:
                    plug = p_('i', pcls)
                    cons = plug.inputs(checkChildren=False)
                else:
                    cons = p_('i').inputs(checkChildren=False)
                continue

            # 入力ソースの .msg 出力をチェック。
            cons = p_('msg').outputs(checkChildren=False)
            if not cons:
                break

            # .msg 出力先に animLayer ノードが在れば、それを取得。このノードはブレンドノードであるとする。
            layer = None
            for c in cons:
                if c.hasNodeFn(_MFn_kAnimLayer):
                    layer = c.nodeName()
                    break
            if not layer:
                # 予期しないノードで塞がれている場合は、探索を終了。
                break

            # アトリビュート名のサフィックスを決定。
            xyz = con.shortName()[-1] if con.isChild() else ''

            # そのレイヤーが条件に合致すれば、プラグを得る。
            if not isBaseLayer and (not selected or _animLayer(layer, q=True, sel=True)):
                p = p_('ib' + xyz, pcls)  # .ib がそのレイヤーの入力。
                if asPair:
                    p = (p, layer)
                if not all:
                    return p
                result.append(p)

            # さらに手前の入力ソースを検索。
            plug = p_('ia' + xyz, pcls)  # .ia がそのレイヤー手前の入力。
            cons = plug.inputs(checkChildren=False)

        # selected オプションが指定され（ベースレイヤー指定された場合はチェック済みで False になっている）、
        # 且つ exact 指定されている場合、ベースレイヤーが存在しないか非セレクト状態なら、最も手前のプラグを採用しない。
        if selected and exact:
            layer = _animLayer(q=True, root=True)
            if not(layer and _animLayer(layer, q=True, sel=True)):
                return result
        elif asPair:
            layer = _animLayer(q=True, root=True)

        # 最も手前のプラグ（ベースレイヤー、又はそのままのプラグ）。
        if asPair:
            plug = (plug, layer)
        if not all:
            return plug
        result.append(plug)
        return result

    def pairBlendPlug(self, in1=True, in2=False, cur=False, inUse=False, byWeight=False):
        u"""
        :mayanode:`pairBlend` の入力プラグを得る。

        :param `bool` in1: 入力 1 のプラグを得る。
        :param `bool` in2: 入力 2 のプラグを得る。
        :param `bool` cur:
            in1 と in2 の指定は無視して、
            pairBlend の currentDriver をチェックして 1 か 2 を得る。
        :param `bool` inUse:
            得たい入力系統が使用されている場合にのみ得る。
        :param `bool` byWeight:
            in1, in2, cur, そして inUse の指定を全て無視して、
            pairBlend の mode や weight をチェックして、
            利用されている入力のタプルを得る。
        :rtype:
            byWeight が True の場合は `tuple` 、
            in1 と in2 が両方 True の場合は `tuple` 、
            そうでない場合は単一の `Plug` か None。
        """
        if byWeight:
            in1 = True
            in2 = True
            cur = False
            inUse = True
        elif not(cur or in1 or in2):
            return

        self = self.proxyMaster()

        cons = self.inputs(checkChildren=False)
        while cons:
            con = cons[0]

            # 入力が pairBlend ノードな場合。
            if con.hasNodeFn(_MFn_kPairBlend):
                sn = con.shortName()[-2:]
                p_ = con.node().plug_

                # cur=True の場合、 currentDriver を得て、入力 1 か 2 か決める。
                if cur:
                    if p_('c').get() == 2:
                        in1 = False
                        in2 = True
                    else:
                        in1 = True
                        in2 = False

                # inUse=True の場合、入力 1 と 2 それぞれの利用状況を得る。
                get1 = in1
                get2 = in2
                if inUse:
                    if sn.startswith('r'):
                        i = p_('rm').get()
                    else:
                        i = p_(sn + 'm').get()
                    if i is 2:
                        get1 = False
                    elif i is 1:
                        get2 = False
                    elif byWeight:
                        w = p_('w').get()
                        if w == 1.:
                            get1 = False
                        elif not w:
                            get2 = False

                # 入力 1 と 2 それぞれのプラグを得る。
                pcls = type(self)
                res1 = p_('i' + sn + '1', pcls) if get1 else None
                res2 = p_('i' + sn + '2', pcls) if get2 else None

                # 値を返す。
                if byWeight:
                    if res1:
                        if res2:
                            return res1, res2
                        return (res1,)
                    elif res2:
                        return (res2,)
                    return EMPTY_TUPLE
                if in1 and in2:
                    return res1, res2
                elif in1:
                    return res1
                elif in2:
                    return res2
                return

            # 入力が mute ノードな場合。
            elif con.hasNodeFn(_MFn_kMute):
                cons = con.node().plug_('i').inputs(checkChildren=False)

            # 入力がその他の場合は終了。
            else:
                break

        # 何も得られない。
        if byWeight:
            return EMPTY_TUPLE
        if in1 and in2:
            return None, None
        return

    def belongsToLayer(self, layer):
        u"""
        指定したアニメーションレイヤーのメンバーかどうか。

        :param `str` layer:
            アニメーションレイヤー名
            （文字列か、文字列として評価してノード名になるもの）。
            ベースレイヤーは実体が無いため指定出来ない。
        :rtype: `bool`
        """
        layer = str(layer)
        for p in self.proxyMaster().outputs(checkChildren=False):
            if p.shortName() == 'dsm' and p.nodeName() == layer:
                return True
        return False

    def createAnimCurve(self, unitless=False, cls=CyObject):
        u"""
        アトリビュート型に応じた animCurve ノードを生成する。

        アトリビュートへの接続はしない。

        :param `bool` unitless:
            ドリブンキー用の animCurve を生成する。
        :param cls:
            得たいオブジェクトのクラス。
            通常はデフォルトのままで良い。
            `str` を指定すれば名前のまま得られる。
        :rtype: `.AnimCurve` 派生タイプ
        """
        self = self.proxyMaster()
        return cls(_createNode(
            (_ATTRTYPE_ANIMCURVEU_DICT if unitless else _ATTRTYPE_ANIMCURVET_DICT)[self.type()],
            n=correctNodeName(self.plugName())
        ))

    def animCurves(self, dk=False):
        u"""
        アトリビュートに接続された全 animCurve のリストを得る。

        アニメーションレイヤーによって複数の animCurve を
        持っている場合は、それら全てを得られる。

        :param `bool` dk: ドリブンキーも含めるかどうか。
        :rtype: `list`
        """
        if dk:
            res = [x._animCurve(True) for x in self.layeredPlug(all=True)]
            return [x for x in res if x]
        # コマンドでは animCurveT? のみ得られるが、入力コネクションが無いものに限定する。
        names = _keyframe([x.name_() for x in self.layeredPlug(all=True)], q=True, n=True)
        if names:
            return [CyObject(x) for x in names if not _connectionInfo(x + '.i', ied=True)]
        return []

    def _animCurve(self, dk):
        cons = self.inputs(checkChildren=False)
        if cons:
            con = cons[0]
            if con.hasNodeFn(_MFn_kAnimCurve):
                node = con.node()
                if dk or not _isDrivenKey(node):
                    return node

    def animCurve(self, dk=False, direct=False):
        u"""
        アトリビュートに接続された animCurve を1つ得る。

        :param `bool` dk: ドリブンキーも含めるかどうか。
        :param `bool` direct:
            直接接続された animCurve に限定して得るかどうか。
            デフォルトでは、
            :mayanode:`pairBlend` や :mayanode:`mute` や
            アニメーションレイヤーの状態（レイヤー選択や
            Solo 設定など）が考慮された最適な animCurve が得られる。
        :rtype: `.AnimCurve` 派生タイプ or None
        """
        if direct:
            return self.proxyMaster()._animCurve(dk)

        elif dk:
            #return self.layeredPlug(best=True)._animCurve(True)
            blp = self.layeredPlug(best=True)
            res = blp._animCurve(True)
            if res:
                return res
            for p in self.layeredPlug(all=True):
                if p != blp:
                    res = p._animCurve(True)
                    if res:
                        return res

        else:
            # コマンドでは animCurveT? のみ得られるが、入力コネクションが無いものに限定する。
            name = _keyframe(self.name_(), q=True, n=True)
            if name:
                name = name[0]
                if not _connectionInfo(name + '.i', ied=True):
                    return CyObject(name)

    def isMuted(self):
        u"""
        ミュートされているかどうか。
        """
        return _mute(self.name(), q=True)

    def mute(self, **kwargs):
        u"""
        ミュートする。
        """
        _mute(self.name())

    def unmute(self, **kwargs):
        u"""
        ミュート解除する。
        """
        _mute(self.name(), d=True, f=True)

CyObject.setGlobalPlugClass(Plug)


#------------------------------------------------------------------------------
_ATTRTYPE_ANIMCURVET_DICT = {
    'bool': 'animCurveTU',
    'byte': 'animCurveTU',
    'char': 'animCurveTU',
    'short': 'animCurveTU',
    'long': 'animCurveTU',
    'float': 'animCurveTU',
    'double': 'animCurveTU',
    'enum': 'animCurveTU',

    'floatLinear': 'animCurveTL',
    'doubleLinear': 'animCurveTL',
    'floatAngle': 'animCurveTA',
    'doubleAngle': 'animCurveTA',
    'time': 'animCurveTT',
}  #: アトリビュートタイプ名から適した animCurveT? ノードタイプ名を得る辞書。
_ATTRTYPE_ANIMCURVEU_DICT = {
    'bool': 'animCurveUU',
    'byte': 'animCurveUU',
    'char': 'animCurveUU',
    'short': 'animCurveUU',
    'long': 'animCurveUU',
    'float': 'animCurveUU',
    'double': 'animCurveUU',
    'enum': 'animCurveUU',

    'floatLinear': 'animCurveUL',
    'doubleLinear': 'animCurveUL',
    'floatAngle': 'animCurveUA',
    'doubleAngle': 'animCurveUA',
    'time': 'animCurveUT',
}  #: アトリビュートタイプ名から適した animCurveU? ノードタイプ名を得る辞書。


def _2_MTime_rawToUI(v):
    return _2_MTime(v, _2_MTime_kSeconds).asUnits(_2_MTime_uiUnit())

_2_MTime = api2.MTime
_2_MTime_uiUnit = _2_MTime.uiUnit
_2_MTime_kSeconds = _2_MTime.kSeconds

_2_MAngle_rawToUI = api2.MAngle.internalToUI
_2_MDistance_rawToUI = api2.MDistance.internalToUI


def _setAttr_generic(name, val, **kwargs):
    u"""
    generic 型アトリビュートに :mayacmd:`setAttr` する。

    :param name: Mayaアトリビュート名。
    :param v:
        セットする値。
        数値、文字列、matrix、3次元ベクトルに対応。
    """
    if isinstance(val, Number):
        _setAttr(name, val)
    elif isinstance(val, BASESTR):
        _setAttr(name, val, type='string')
    elif isinstance(val, _MATRIX_TYPES):
        _setAttr(name, *val, type='matrix')
    elif isinstance(val, _VECTOR_TYPES):
        n = len(val)
        if n == 16:
            _setAttr(name, *val, type='matrix')
        elif 2 <= n <= 4:
            _setAttr(name, *val, type='double' + str(n))
        else:
            _setAttr(name, n, *val, type='doubleArray')
    else:
        raise ValueError('not supported value type: ' + repr(val))

_MATRIX_TYPES = (
    Matrix,
    Transformation,
    api2.MMatrix,
    api2.MFloatMatrix,
)
_VECTOR_TYPES = (
    Vector,
    api2.MVector,
    api2.MPoint,
    api2.MColor,
    api2.MFloatVector,

    Quaternion,
    api2.MQuaternion,

    Sequence,
)


def _setAttr_string(name, val):
    _setAttr(name, val, type='string')


def _setAttr_matrix(name, val):
    # Matrix は * を付けても付けなくても大丈夫だが、
    # Transformation や list や tuple は付けないとダメ。
    _setAttr(name, *val, type='matrix')


def _setAttr_vals(name, val):
    _setAttr(name, *val)


def _setAttr_raw_distance(name, val):
    _setAttr(name, _2_MDistance_rawToUI(val))


def _setAttr_raw_angle(name, val):
    _setAttr(name, _2_MAngle_rawToUI(val))


def _setAttr_raw_time(name, val):
    _setAttr(name, _2_MTime_rawToUI(val))


def _setAttr_raw_distances(name, val, **kwargs):
    _setAttr(name, *[_2_MDistance_rawToUI(x) for x in val])


def _setAttr_raw_angles(name, val, **kwargs):
    _setAttr(name, *[_2_MAngle_rawToUI(x) for x in val])


#def _setAttr_raw_times(name, val, **kwargs):
#    _setAttr(name, *[_2_MTime_rawToUI(x) for x in val])


def _makeScalarArraySetter(typename):
    def setter(name, val):
        _setAttr(name, val, type=typename)
    return setter


def _makeDataArraySetter(typename):
    def setter(name, val):
        _setAttr(name, len(val), *val, type=typename)
    return setter


_CMD_SETUVAL_DICT = {
    'bool': _setAttr,
    'byte': _setAttr,
    'char': _setAttr,
    'short': _setAttr,
    'long': _setAttr,
    'float': _setAttr,
    'double': _setAttr,
    'enum': _setAttr,

    'floatLinear': _setAttr,
    'doubleLinear': _setAttr,
    'floatAngle': _setAttr,
    'doubleAngle': _setAttr,
    'time': _setAttr,

    'string': _setAttr_string,

    'matrix': _setAttr_matrix,
    'at:matrix': _setAttr_matrix,
    'fltMatrix': _setAttr_matrix,

    'short2': _setAttr_vals,
    'short3': _setAttr_vals,
    'long2': _setAttr_vals,
    'long3': _setAttr_vals,
    'float2': _setAttr_vals,
    'float3': _setAttr_vals,
    'double2': _setAttr_vals,
    'double3': _setAttr_vals,
    'double4': _setAttr_vals,
    'reflectance': _setAttr_vals,
    'spectrum': _setAttr_vals,

    'generic': _setAttr_generic,

    'doubleArray': _makeScalarArraySetter('doubleArray'),
    'floatArray': _makeScalarArraySetter('floatArray'),
    'Int32Array': _makeScalarArraySetter('Int32Array'),
    'Int64Array': _makeScalarArraySetter('Int64Array'),

    'stringArray': _makeDataArraySetter('stringArray'),
    'vectorArray': _makeDataArraySetter('vectorArray'),
    'floatVectorArray': _makeDataArraySetter('floatVectorArray'),
    'pointArray': _makeDataArraySetter('pointArray'),
    'matrixArray': _makeDataArraySetter('matrixArray'),
}

_CMD_SETVAL_DICT = dict(_CMD_SETUVAL_DICT)
_CMD_SETVAL_DICT.update({
    'doubleLinear': _setAttr_raw_distance,
    'floatLinear': _setAttr_raw_distance,
    'doubleAngle': _setAttr_raw_angle,
    'floatAngle': _setAttr_raw_angle,
    'time': _setAttr_raw_time,

    'float2floatLinear': _setAttr_raw_distances,
    'float3floatLinear': _setAttr_raw_distances,
    'double2doubleLinear': _setAttr_raw_distances,
    'double3doubleLinear': _setAttr_raw_distances,
    'double4doubleLinear': _setAttr_raw_distances,

    'float2floatAngle': _setAttr_raw_angles,
    'float3floatAngle': _setAttr_raw_angles,
    'double2doubleAngle': _setAttr_raw_angles,
    'double3doubleAngle': _setAttr_raw_angles,
    'double4doubleAngle': _setAttr_raw_angles,

    # NOTE: 数値コンパウンドに time は使用できないので不要。
    #'double2time': _setAttr_raw_times,
    #'double3time': _setAttr_raw_times,
    #'double4time': _setAttr_raw_times,
})


def _makePlugValueSetter(tbl_get):
    def setter(name, ttype, val):
        proc = tbl_get(ttype)
        if proc:
            return proc(name, val)

        typ = ttype.split(':')[-1]

        #if typ.endswith('Array'):
        #    try:
        #        # 長さ指定が要らないスカラー Array 系。
        #        _setAttr(name, val, type=typ)
        #        #print('<<<<<<<<<<<<<<<< ' + typ + ' >>>>>>>>>>>>>>>>')
        #        return
        #    except:
        #        try:
        #            # 長さ指定が要るその他の Array 系。
        #            _setAttr(name, len(val), *val, type=typ)
        #            #print('@@@@@@@@@@@@@@@@ ' + typ + ' @@@@@@@@@@@@@@@@')
        #            return
        #        except:
        #            pass

        # それ以外の多くの型はこれでいける。
        try:
            _setAttr(name, *val, type=typ)
            #print('################ ' + typ + ' ################')
        except:
            raise ValueError('attribute type not supported by setAttr: ' + ttype)

    return setter

_setUnitValue = _makePlugValueSetter(_CMD_SETUVAL_DICT.get)
_setRawValue = _makePlugValueSetter(_CMD_SETVAL_DICT.get)


#------------------------------------------------------------------------------
def _addElement(queue):
    u"""
    1つの要素プラグに関わるプラグの上から順に並んだキューを元に「評価」と「削除」をコマンド化して呼び出す。
    """
    top = queue[0]
    if len(queue) is 1:
        docmd(top.evaluator(), partial(_api1_executeCommand, 'removeMultiInstance ' + top.name_()))
    else:
        # 評価は上から。undoのための削除は最上位のみで良い（redoはそのundoではなくdoなので）。
        def doit():
            for p in evals:
                p()
        evals = [p.evaluator() for p in queue]
        docmd(doit, partial(_api1_executeCommand, 'removeMultiInstance ' + top.name_()))


def _unlockCmd(plug):
    _setAttr(plug.name_(), l=False)
    return plug


def _unlockApi(plug):
    plug.apiSetLocked(False)
    return plug


def _pairBlendInput(out, pcls=None):
    p_ = out.node().plug_
    sn = out.shortName()[-2:]

    # Check the blending mode.
    i = p_('rm' if sn.startswith('r') else (sn + 'm')).get()
    if i is 2:  # 2 only
        return p_('i' + sn + '2', pcls)
    elif i is 1:  # 1 only
        return p_('i' + sn + '1', pcls)

    # Check the weight.
    #elif byWeight:
    #    w = p_('w').get()
    #    if w == 1.:  # 2 only
    #        return p_('i' + sn + '2', pcls)
    #    elif not w:  # 1 only
    #        return p_('i' + sn + '1', pcls)

    # Check the currentDriver.
    if p_('c').get() == 2:
        return p_('i' + sn + '2', pcls)
    else:
        return p_('i' + sn + '1', pcls)


def _isDrivenKey(anim):
    p = anim.plug_('i')
    return p.type() != 'time' and p.isDestination()

