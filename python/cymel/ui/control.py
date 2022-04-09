# -*- coding: utf-8 -*-
u"""
mel UI の :mayacmd:`control` ラッパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ..common import *
from .uitypes import *
from weakref import ref as _wref

__all__ = ['Control']

# 以下をパッケージで保証。
# - Layout
# - Window
# - Menu
# - MenuItem
# - SubMenuItem
# - _PARENTABLE_LAYOUTS
# - _PARENTABLE_LAYOUTS_AND_OPTIONMENU

_cmds_control = cmds.control
_cmds_window = cmds.window
_cmds_layout = cmds.layout
_cmds_setParent = cmds.setParent
_cmds_menuItem = cmds.menuItem
_cmds_lsUI = cmds.lsUI
_cmds_objectTypeUI = cmds.objectTypeUI
_cmds_deleteUI = cmds.deleteUI

_str_eq = UNICODE.__eq__
_str_ne = UNICODE.__ne__
_str_le = UNICODE.__le__
_str_lt = UNICODE.__lt__
_str_ge = UNICODE.__ge__
_str_gt = UNICODE.__gt__

_op_str = {
    _str_le: '<=',
    _str_lt: '<',
    _str_ge: '>=',
    _str_gt: '>',
}.get


#------------------------------------------------------------------------------
class Control(object):
    u"""
    mel UI の :mayacmd:`control` ラッパークラス。
    """
    UICMD = _cmds_control  #: 対応する mel コマンドオブジェクト。

    def __new__(cls, *args, **kwargs):
        # 固定引数が指定された場合は既存UIかも知れない。
        nArgs = len(args)
        uitype = None
        lastCurrent = ZERO
        if nArgs >= 1:
            name = args[0]
            if not name:
                return
            # 第一引数がオブジェクトなら、そこからクラスとUIタイプ名を取得。
            if isinstance(name, Control):
                uitype = name.type()
                cls0 = type(name)
                name = name.name()
                if not issubclass(cls, cls0):
                    cls = cls0

            # 第一引数が名前なら、既存UIの取得か新規生成となる。
            else:
                # Window 派生クラスなら、既存ウィンドウ指定か新規ウィンドウ生成となる。
                if issubclass(cls, Window):
                    if _cmds_window(name, ex=True):
                        uitype = 'window'

                # フルパス、又はカレントレイアウトと接続したパスを優先的に検査。
                if name.startswith('|'):
                    fullPath = name
                else:
                    # Mayaはカレント下でなくても候補が複数在ると最後のを得てしまうが、カレント直下に限定する。
                    fullPath = _cmds_setParent(q=True)
                    if fullPath and fullPath != 'NONE':
                        fullPath += '|' + name
                    else:
                        fullPath = None
                if fullPath:
                    # フルパスで既存UIが在るかチェック。
                    # NOTE:
                    #   Maya は型違い同名を許容してしまう。それが作られてしまうと uiType() 関数がうまく動かないので注意。
                    #   生成自体をエラーにすることも出来るが、ここだけでやっても不完全なので、やめておく。
                    if cls.UICMD(fullPath, ex=True):
                        # 結構レアケースだと思うが、フルパス名がどこかの相対パスともマッチしてしまう場合を除外する。
                        try:
                            if cls.UICMD(fullPath, q=True, fpn=True) == fullPath:
                                name = fullPath
                                uitype = uiType(name)
                        # -fpn を提供しないコマンドならチェックは諦める。
                        except TypeError:
                            name = fullPath
                            uitype = uiType(name)

                # フルパス＋指定型で見つからない場合は、曖昧な探索に任せる。
                if not uitype:
                    # 名前に | を含む場合は、既存名しか有り得ないものとする。
                    if '|' in name:
                        # control コマンドで扱えるなら -fpn が得られる。
                        if _cmds_control(name, ex=True):
                            name = _cmds_control(name, q=True, fpn=True)
                            uitype = uiType(name)
                        # -fpn が得られない場合はパスが不完全かも知れない。menuItem なら親のパスを得て補完する。
                        else:
                            uitype = uiType(name)
                            if issubclass(uiClass(uitype), MenuItem):
                                tkns = name.split('|')
                                name = _cmds_control('|'.join(tkns[:-1]), q=True, fpn=True) + '|' + tkns[-1]

                    # 抽象クラス指定なら、既存名しか有り得ないものとする。
                    elif cls is Control or cls is Layout:
                        # そのコマンドで扱えるなら -fpn が得られる。
                        if cls.UICMD(name, ex=True):
                            name = cls.UICMD(name, q=True, fpn=True)
                            uitype = uiType(name)
                        # -fpn が得られない場合はパスが不完全かも知れない。lsUI と突き合わせて補完する。
                        else:
                            tmp = uiType(name)
                            if tmp and issubclass(uiClass(tmp), MenuItem):
                                end = '|' + name
                                for s in _cmds_lsUI(mi=True, l=True):
                                    if s.endswith(end):
                                        name = s
                                        uitype = tmp
                                        break
                            if not uitype:
                                return

                # 既存名指定のUIタイプが決まったならクラスを取得。
                if uitype:
                    cls0 = uiClass(uitype)
                    if cls0:
                        # サブメニューの場合は 'menu' -> Menu となるので、menuItem ならば SubMenuItem とする。
                        if cls0 is Menu:
                            lastCurrent = None
                            if _cmds_menuItem(name, ex=True):
                                cls0 = SubMenuItem
                        elif issubclass(cls0, _PARENTABLE_LAYOUTS_AND_OPTIONMENU):
                            lastCurrent = None
                    else:
                        # 不明なクラスなら Layout か Control のどちらか。
                        if _cmds_layout(name, ex=True):
                            cls0 = Layout
                            lastCurrent = None
                        else:
                            cls0 = Control
                    # 指定されたクラスが型に合わないなら修正する。
                    if not issubclass(cls, cls0):
                        cls = cls0

        # 新規UI生成。
        if not uitype:
            # ウィンドウやレイアウト生成前の setParent の保存。
            if issubclass(cls, _PARENTABLE_LAYOUTS):
                lastCurrent = _cmds_setParent(q=True)

            # メニュー生成前の setParent -menu の保存。
            elif issubclass(cls, MenuItem):
                # クラスが MenuItem で subMenu=True なら SubMenuItem にする。
                if kwargs.get('sm', kwargs.get('subMenu')):
                    cls = SubMenuItem
                    lastCurrent = _cmds_setParent(q=True, menu=True)
            elif issubclass(cls, SubMenuItem):
                # クラスが SubMenuItem なら subMenu=True にする。
                if 'subMenu' in kwargs:
                    kwargs['subMenu'] = True
                else:
                    kwargs['sm'] = True
                lastCurrent = _cmds_setParent(q=True, menu=True)
            elif issubclass(cls, Menu):
                lastCurrent = _cmds_setParent(q=True, menu=True)

            # コントロール生成。
            name = cls.UICMD(*args, **kwargs)
            uitype = uiType(name)
            if not name:
                uitype = cls.UICMD.__name__
            #print('CREATE: %s (%s)' % (name, uitype))

        # オブジェクトを生成。
        #obj = super(Control, cls).__new__(cls)
        obj = object.__new__(cls)  # NOTE: 効率の為 Control と他の何かを多重継承したクラスは無いものとして super を利用しない。

        # NOTE: ドック化によってパスが変わる可能性を考慮した仕組み。
        #   _orgName  ... 最初のパス。
        #   _name ... 現在のパス。_untrustedName が None でなければ name() でチェックされる。
        #   _untrustedName ... パスが変わる可能性がある場合、先頭のその部分（ window|foo|bar なら window|foo の部分）。
        #   _hash ... パスの変わらない部分をハッシュ化（ window|foo|bar なら |foo|bar の部分）。
        obj._name = name
        obj._orgName = name
        obj.__wref = None
        if name.startswith('MayaWindow|'):
            obj._untrustedName = None  # パスはもう変わらない。
            obj._hash = hash(name)
        else:
            tkns = name.split('|')
            if len(tkns) == 1:
                obj._untrustedName = None  # パスはもう変わらない。
                obj._hash = hash(name)
            else:
                obj._untrustedName = tkns[0] + '|' + tkns[1]  # ドック化によってパスが変わる可能性あり。
                obj._hash = hash(name[len(tkns[0]):])  # 変わらない部分をハッシュ化。

        obj._uitype = uitype
        if lastCurrent is not ZERO:
            obj._lastCurrent = lastCurrent
        return obj

    #def __init__(self, *args, **kwargs):
    #    u""" 初期化。 """

    def __repr__(self):
        return "%s('%s')" % (type(self).__name__, self.name())

    def __str__(self):
        return self.name()

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        return self.__compare(other, True, _str_eq)

    def __ne__(self, other):
        return self.__compare(other, False, _str_ne)

    def __le__(self, other):
        return self.__compare(other, True, _str_le)

    def __lt__(self, other):
        return self.__compare(other, False, _str_lt)

    def __ge__(self, other):
        return self.__compare(other, True, _str_ge)

    def __gt__(self, other):
        return self.__compare(other, False, _str_gt)

    def __compare(self, other, eqval, proc):
        # 名前比較はドック化によって変わることを考慮し、
        # 変わる前と変わった後の両方を許容。
        if isinstance(other, Control):
            if self._orgName == other._orgName:
                return eqval

            if self._untrustedName:
                # self のパスが変わった可能性がある。
                selfName = self.name()
                if other._untrustedName:
                    # さらに other のパスが変わった可能性もある。
                    otherName = other.name()
                    if selfName == otherName or self._orgName == otherName:
                        return eqval

                return proc(selfName, other._orgName)

            elif other._untrustedName:
                # other のパスが変わった可能性がある。
                return proc(self._orgName, other.name())

            return proc is _str_ne or proc(self._orgName, other._orgName)

        elif isinstance(other, BASESTR):
            if self._orgName == other:
                return eqval

            if self._untrustedName:
                # self のパスが変わった可能性がある。
                return proc(self.name(), other)

            return proc is _str_ne or proc(self._orgName, other)

        opname = _op_str(proc)
        if opname:
            raise TypeError(
                '%r not supported between instances of %r and %r' % (
                    opname, type(self).__name__, type(other).__name__))
        return not eqval

    def type(self):
        u"""
        UIタイプ名を得る。

        :rtype: `str`
        """
        return self._uitype

    def name(self):
        u"""
        フルパスUI名を得る。

        :rtype: `str`
        """
        # ウィンドウの最上位レイアウトが floatingWindow と判定されるならドック化されたと判断。
        if self._untrustedName and _cmds_layout(self._untrustedName, ex=True):
            try:
                uitype = _cmds_objectTypeUI(self._untrustedName)
            except:  # workspaceControl の場合にエラーになることがある。
                uitype = None
            if uitype == 'floatingWindow':
                # 正しいパスを取得。最上位レイアウトに限り layout -q -fpn だと正しいパスを得られない。
                lastCurrent = _cmds_setParent(q=True)
                newPath = _cmds_setParent(self._untrustedName)
                try:
                    _cmds_setParent(lastCurrent)
                except:
                    pass

                # パスをリプレース。
                self._name = newPath + self._name[len(self._untrustedName):]
                #print('FIXPATH: ' + self._orgName + ' -> ' + self._name)
                self._untrustedName = None  # もう変わらない。
        return self._name

    def shortName(self):
        u"""
        パスを含まないUI名を得る。

        :rtype: `str`
        """
        return self._name.split('|')[-1]  # ドック化の名前の修正は不要。

    def relativeName(self, base):
        u"""
        上位のUIからの相対名を得る。

        :type base: `.Control` or `str`
        :param base: 基準となる上位のUI。
        :rtype: `str`
        """
        base = str(base)
        name = self.name()
        if name.startswith(base):
            return name[len(base):]
        return name

    def window(self):
        u"""
        UIの属するウィンドウを得る。

        :rtype: `.Window`
        """
        return Window(self.name().split('|')[0])

    def parent(self):
        u"""
        親UIを得る。

        :rtype: `.Layout` or `.Menu`
        """
        return Control('|'.join(self.name().split('|')[:-1]))

    def exists(self):
        u"""
        UIが存在しているかどうか。

        :rtype: `bool`
        """
        return self.UICMD(self.name(), ex=True)

    def delete(self):
        u"""
        このコントロールを削除する。
        """
        _cmds_deleteUI(self.name())

    def get(self, name):
        u"""
        コントロールの属性値を得る。

        :param `str` name: 属性名（コマンドオプション名）。
        :returns: 属性値（型は属性による）。
        """
        return self.UICMD(self.name(), q=True, **{name: True})

    def set(self, name, value):
        u"""
        コントロールの属性値をセットする。

        :param `str` name: 属性名（コマンドオプション名）。
        :param value: 属性値（型は属性による）。
        :returns: コマンドの戻り値。
        """
        return self.UICMD(self.name(), e=True, **{name: value})

    def call(self, **kwargs):
        u"""
        コントロールのコマンドを呼び出す。

        このメソッドを経ずとも、
        オブジェクトを直接呼び出すことも可能。

        :param kwargs: コマンドのキーワード引数。
        :returns: コマンドの戻り値。
        """
        return self.UICMD(self.name(), **kwargs)

    def __call__(self, **kwargs):
        return self.UICMD(self.name(), **kwargs)

    @staticmethod
    def getCurrent():
        u"""
        カレントペアレントを得る。

        :rtype: `.Control`
        """
        # NOTE: window は control -ex でも大丈夫なのだが、layout だとダメな場合がある（window直下のレイアウトやドック化された後など）。
        cur = _cmds_setParent(q=True)
        #if _cmds_control(cur, ex=True):
        if (_cmds_layout if '|' in cur else _cmds_window)(cur, ex=True):
            return Control(cur)

    def ref(self):
        u"""
        弱参照を得る。
        """
        if not self.__wref:
            self.__wref = _wref(self)
        return self.__wref

    def makeWeakCB(self, name, *args, **kwargs):
        u"""
        このインスタンスを参照せずにメソッドを呼び出す関数ラッパーを返す。

        :param `str` name: メソッド名。
        :param args: 固定化する引数リスト。
        :param kwargs: 固定化するキーワード引数。
        """
        wref = self.ref()

        if args:
            if kwargs:
                def _func(*aa, **kk):
                    win = wref()
                    if win:
                        for k in kwargs:
                            if not k in kk:
                                kk[k] = kwargs[k]
                        getattr(win, name)(*(args + aa), **kk)

            else:
                def _func(*aa, **kk):
                    win = wref()
                    if win:
                        getattr(win, name)(*(args + aa), **kk)

        elif kwargs:
            def _func(*aa, **kk):
                win = wref()
                if win:
                    for k in kwargs:
                        if not k in kk:
                            kk[k] = kwargs[k]
                    getattr(win, name)(*aa, **kk)

        else:
            def _func(*aa, **kk):
                win = wref()
                if win:
                    getattr(win, name)(*aa, **kk)

        return _func

    def getValue(self):
        u"""
        値を得る。

        UIコントロールごとの違いを吸収する。
        """
        info = _VALUE_ARG_DICT.get(self._uitype)
        if not info:
            raise ValueError('getValue unsupported: ' + self._uitype)
        name = self.name()

        if isinstance(info, dict):
            n = self.numChildren() - 1
            if n > 1:
                dat = info.get('get')
                if dat:
                    key = dat[n - 1]
                else:
                    return [self.UICMD(name, q=True, **{k: True}) for k in info['each'][:n]]
            else:
                key = info['each'][0]
        elif isinstance(info, tuple):
            n = self.numChildren() - 1
            if n > 1:
                return [self.UICMD(name, q=True, **{k: True}) for k in info[:n]]
            key = info[0]
        else:
            key = info
        return self.UICMD(name, q=True, **{key: True})

    def setValue(self, val):
        u"""
        値をセットする。

        UIコントロールごとの違いを吸収する。

        :param val: セットする値。
        """
        info = _VALUE_ARG_DICT.get(self._uitype)
        if not info:
            raise ValueError('setValue unsupported: ' + self._uitype)
        name = self.name()

        if isinstance(info, dict):
            if isinstance(val, Sequence) and not isinstance(val, BASESTR):
                n = len(val)
                if n > 1:
                    dat = info.get('set')
                    if dat:
                        key = dat[n - 1]
                    else:
                        key = info.get('set4')
                        if key:
                            if n < 4:
                                val = list(val) + [0] * (4 - n)
                        else:
                            for k, v in zip(info['each'], val):
                                self.UICMD(name, e=True, **{k: v})
                            return
                else:
                    key = info['each'][0]
                    val = val[0]
            else:
                key = info['each'][0]
        elif isinstance(info, tuple):
            if isinstance(val, Sequence) and not isinstance(val, BASESTR):
                for k, v in zip(info, val):
                    self.UICMD(name, e=True, **{k: v})
                return
            key = info[0]
        else:
            key = info
        self.UICMD(name, e=True, **{key: val})

registerTypedCls(Control)


#------------------------------------------------------------------------------
_VALUE_ARG_DICT = {
    'checkBox': 'v',
    'checkBoxGrp': {'each': ('v1', 'v2', 'v3', 'v4'), 'set': ('v1', 'va2', 'va3', 'va4')},

    'floatField': 'v',
    'floatSliderGrp': 'v',
    'floatFieldGrp': {'each': ('v1', 'v2', 'v3', 'v4'), 'get': ('v1', 'v', 'v', 'v'), 'set4': 'v'},

    'intField': 'v',
    'intSliderGrp': 'v',
    'intFieldGrp': {'each': ('v1', 'v2', 'v3', 'v4'), 'get': ('v1', 'v', 'v', 'v'), 'set4': 'v'},

    'textField': 'tx',  # 'fi',
    'textFieldGrp': 'tx',  # 'fi',
    'textFieldButtonGrp': 'tx',  # 'fi',

    'symbolCheckBox': 'v',
    'iconTextCheckBox': 'v',

    'optionMenu': 'sl',
    'optionMenuGrp': 'sl',

    'radioButtonGrp': 'sl',
}  #: getValue と setValue に対応するための定義テーブル。

