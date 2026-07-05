# -*- coding: utf-8 -*-
u"""
オプションボックスフレームワーク。

Maya 標準の option box を Python から構築するための基底クラスを提供する。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from functools import partial as _partial
from weakref import ref as _wref

import maya.OpenMaya as _api1
import maya.cmds as cmds
import maya.mel as mel

from ..common import *
from ..utils.operation import WaitCursor
from ..utils.optionvar import OptionVar
from ..utils.utils import escapeForMel as _escapeForMel, getDpiScaling as _getDpiScaling

__all__ = ['OptionBox']

_executeCommand = _api1.MGlobal.executeCommand
_getMelVar = lambda x: mel.eval(x + '=' + x)


_MAYA_DPI_INV_SCALE = 1. / _getDpiScaling()
if MAYA_VERSION >= (2016,):
    _WINDOW_WIDTH_OFFSET = int(round(16 * _MAYA_DPI_INV_SCALE))
else:
    _WINDOW_WIDTH_OFFSET = 20

if MAYA_VERSION >= (2025,):
    def _deleteMenuOnClose(menu):
        cmds.evalDeferred(_partial(cmds.deleteUI, menu))
else:
    _deleteMenuOnClose = cmds.deleteUI

if _MAYA_DPI_INV_SCALE == 1.:
    def _scaledSize(size):
        return size
else:
    def _scaledSize(size):
        return int(size * _MAYA_DPI_INV_SCALE)


class OptionBox(with_metaclass(Singleton, object)):
    u"""
    オプションボックス作成のための抽象基底クラス。

    オプションボックスを開発する場合は、このクラスを継承し、
    ツール名、オプション接頭辞、デフォルト値などのクラス属性を定義したうえで、
    UI 構築と値のロード/セーブ、および実行コード生成を実装する。

    最小構成の例::

        import cymel.ui as cmu

        class MyOptionBox(cmu.OptionBox):
            TOOL_NAME = 'Test'
            TOOL_VERSION = '1.0.0'
            BUTTON_LABEL = 'Test'
            OPT_PREFIX = TOOL_NAME + '.'
            DEFAULTS = dict(foo=False, bar=1.0)

            def assemblePyCode(self):
                return 'print(dict(%s))' % self.assemblePyCodeWithArgs()

            def createContents(self, tabId):
                if tabId == 1:
                    cmu.CheckBoxGrp('foo', ncb=1, l1='Foo', cc=self.onChanged)
                    cmu.FloatFieldGrp('bar', l='Bar')

            def loadOptions(self, tabId=None):
                if (tabId == 1 or tabId is None) and self.isTabReady(1):
                    cmu.Control('foo').setValue(self.get('foo'))
                    cmu.Control('bar').setValue(self.get('bar'))

            def saveOptions(self, tabId=None):
                if (tabId == 1 or tabId is None) and self.isTabReady(1):
                    self.set('foo', cmu.Control('foo').getValue())
                    self.set('bar', cmu.Control('bar').getValue())

            def updateState(self, tabId=None):
                if (tabId == 1 or tabId is None) and self.isTabReady(1):
                    cmu.Control('bar').set('enable', cmu.Control('foo').getValue())

        # MyOptionBox().perform(0)  # Execute the command using the current settings.
        # MyOptionBox().perform(1)  # Open the Options box.
        # MyOptionBox().perform(2)  # Retrieve the command string to be executed using the current settings.

    """
    TOOL_NAME = 'Abstract'
    OPT_PREFIX = ''
    TOOL_VERSION = '0.0.0'
    BRIEF = ''
    COMMAND_LABEL = ''
    HELP_URL = ''
    SUPPORTED_VERSION = (8, 5)

    BUTTON_LABEL = 'Execute'
    APPLY_BUTTON_LABEL = None
    CLOSE_BUTTON_LABEL = None

    TAB_LABELS = ('Main',)
    DEFAULT_TAB_INDEX = 1
    DEFAULTS = {}
    NO_RESETS = tuple()
    DEFUNCT_KEYS = tuple()
    SKIP_DEFAULT_VALUES = True
    COMMAND_DEFAULTS = {}

    MIN_WIDTH = None
    MIN_HEIGHT = None
    INIT_WIDTH = False
    INIT_HEIGHT = False
    SHOW_ERROR_DIALOG = False

    @classmethod
    def get_instance(cls):
        u"""
        現在保持されているシングルトンインスタンスを得る。

        :rtype: `OptionBox` or None
        """
        ref = getattr(cls, '_singleton_ref', None)
        return ref() if ref else None

    @classmethod
    def getValidUIInstance(cls):
        u"""
        現在有効な UI を持つインスタンスを得る。

        このクラスと派生クラスを深さ優先で調べ、
        生存中の option box UI を持つ最初のインスタンスを返す。

        :rtype: `OptionBox` or None
        """
        for subcls in iterTreeDepthFirst([cls], lambda c: c.__subclasses__()):
            obj = subcls.get_instance()
            if obj and obj.isUIAlive():
                return obj

    @classmethod
    def _mel_ui_call(cls, method_name, *args, **kwargs):
        obj = cls.get_instance()
        if obj:
            getattr(obj, method_name)(*args, **kwargs)

    @classmethod
    def melCB(cls, method_name, *args, **kwargs):
        u"""
        このシングルトンインスタンスのメソッドを呼び出すコールバック文字列を得る。

        Maya 標準 option box の一部コールバックは、Python 関数や Python
        コードを直接セットすると安定しないため、MEL 側から設定する文字列を返す。

        :param `str` method_name: 呼び出すメソッド名。
        :param args: メソッドへ渡す追加位置引数。
        :param kwargs: メソッドへ渡す追加キーワード引数。
        :rtype: `str`
        """
        values = [repr(method_name)]
        values.extend([repr(x) for x in args])
        values.extend(['%s=%r' % (k, v) for k, v in kwargs.items()])
        modname = cls.__module__
        code = 'import %s; %s.%s._mel_ui_call(%s)' % (
            modname, modname, cls.__name__, ', '.join(values))
        return 'python(\\"' + _escapeForMel(code) + '\\")'

    def __init__(self):
        def finalizer(r):
            for menu in menus:
                if cmds.menu(menu, ex=True):
                    _deleteMenuOnClose(menu)

        menus = []
        self._menus = menus
        self._wref = _wref(self, finalizer)

        defaults = dict(
            (self.keyToStore(key), val)
            for key, val in self.DEFAULTS.items())
        self.optionvar = OptionVar(self.OPT_PREFIX, defaults)
        self._no_reset_keys = [self.keyToStore(key) for key in self.NO_RESETS]

        for key in self.DEFUNCT_KEYS:
            key = self.keyToStore(key)
            if key in self.optionvar:
                del self.optionvar[key]

        self._tab_layout = None
        self._custom_layout = None

    def ref(self):
        u"""
        弱参照を得る。

        :rtype: `weakref.ref`
        """
        return self._wref

    def perform(self, cmdi):
        u"""
        Maya 標準 option box から呼び出される入口。

        :param `int` cmdi:
            0 なら現在の設定で実行、1 なら option box を開く、
            2 なら現在の設定で実行される Python コード文字列を返す。
        :returns:
            実行時またはコード取得時はコマンド文字列。表示時は空文字列。
        """
        if cmdi == 0:
            return self.execute(echo=True)
        if cmdi == 1:
            self.show()
            return ''
        if cmdi == 2:
            return self.assembleCodeToEcho()

    def assemblePyCode(self):
        u"""
        実行用 Python コードを生成して返す。

        派生クラスで必ず実装する。`assemblePyCodeWithArgs` を使うと、
        optionVar に保存された値から関数呼び出しや引数リストを組み立てられる。

        :rtype: `str`
        """
        raise NotImplementedError('assemblePyCode')

    def title(self):
        u"""
        ウィンドウタイトルを返す。

        オーバーライドすることで任意に変更できる。

        :rtype: `str`
        """
        return self.TOOL_NAME + ' (v.' + self.TOOL_VERSION + ') Options'

    def createLayout(self, tabId):
        u"""
        タブ内のレイアウトを生成する。

        `TAB_LABELS` に ``None`` や空値を指定してタブレイアウトを使わない場合は、
        `tabId` には 0 が渡される。基底の実装は :mayacmd:`columnLayout`
        だが、派生クラスで任意のレイアウトに置き換えられる。

        :param `int` tabId:
            1 から始まるタブインデックス。タブを使わない場合は 0。
        :rtype: `str`
        """
        return cmds.columnLayout(adjustableColumn=True)

    def createContents(self, tabId):
        u"""
        タブ内の UI コントロールを生成する。

        派生クラスで必ず実装する。呼び出し時には対象タブのレイアウトが
        :mayacmd:`setParent` 済みであり、未生成のタブが初めて表示された時に
        一度だけ呼ばれる。

        :param `int` tabId:
            1 から始まるタブインデックス。タブを使わない場合は 0。
        """
        raise NotImplementedError('createContents')

    def loadOptions(self, tabId=None):
        u"""
        保存されたオプション値を UI にセットする。

        派生クラスで必ず実装する。`tabId` が ``None`` の場合は、
        生成済みの全タブを対象にすることを想定している。

        :param `int` tabId:
            1 から始まるタブインデックス。``None`` の場合は全体。
        """
        raise NotImplementedError('loadOptions')

    def saveOptions(self, tabId=None):
        u"""
        UI から値を読み取って保存する。

        派生クラスで必ず実装する。`tabId` が ``None`` の場合は、
        生成済みの全タブを対象にすることを想定している。

        :param `int` tabId:
            1 から始まるタブインデックス。``None`` の場合は全体。
        """
        raise NotImplementedError('saveOptions')

    def updateState(self, tabId=None):
        u"""
        UI の有効/無効などの状態を更新する。

        必要な場合だけ派生クラスで実装する。`tabId` が ``None`` の場合は、
        生成済みの全タブを対象にすることを想定している。

        :param `int` tabId:
            1 から始まるタブインデックス。``None`` の場合は全体。
        """

    def keyToStore(self, key):
        u"""
        実行用キーを保存用キーへ変換する。

        コマンド実行時の引数名と :class:`~cymel.utils.optionvar.OptionVar`
        に保存するキー名を分けたい場合に、`keyToExec` と対でオーバーライドする。

        :param `str` key: コマンド実行にも使われる通常のキー。
        :returns: `OptionVar` に保存するキー。
        :rtype: `str`
        """
        return key

    def keyToExec(self, key):
        u"""
        保存用キーを実行用キーへ変換する。

        :param `str` key: `keyToStore` で変換された後の保存用キー。
        :returns: コマンド実行に使う通常のキー。
        :rtype: `str`
        """
        return key

    def onChanged(self, *args, **kwargs):
        u"""
        汎用的に使える UI のチェンジコールバック。

        デフォルトでは `updateState` を呼ぶ。
        """
        self.updateState()

    def assembleCodeToEcho(self, pyCode=None):
        u"""
        エコー用のコマンド文字列を得る。

        :param `str` pyCode:
            エコーしたい Python コード。省略時は `assemblePyCode` が呼ばれる。
        :rtype: `str`
        """
        return pyCode or self.assemblePyCode()

    def execute(self, echo=False, addQueue=True):
        u"""
        現在の設定でコマンドを実行する。

        :param `bool` echo:
            実行コードを標準出力へ表示するかどうか。
            表示される文字列は Python コードそのもの。
        :param `bool` addQueue:
            Maya の RecentCommandQueue に追加するかどうか。
            リピート実行から呼ぶ場合は二重登録を避けるため ``False`` にする。
        :rtype: `str`
        """
        self.checkMayaVersion()
        return self.execPyCode(self.assemblePyCode(), echo, addQueue)

    def execPyCode(self, pyCode, echo=False, addQueue=True):
        u"""
        指定した Python コードを実行する。

        :param `str` pyCode: 実行する Python コード。
        :param `bool` echo: 実行コードを標準出力へ表示するかどうか。
        :param `bool` addQueue: RecentCommandQueue に追加するかどうか。
        :rtype: `str`
        """
        if not pyCode:
            return ''

        if echo:
            print(pyCode)

        if IS_UIMODE:
            if self.SHOW_ERROR_DIALOG:
                try:
                    exec(pyCode)
                except Exception as err:
                    _confirmException(err)
                    raise
            else:
                exec(pyCode)

            if addQueue:
                self._addToRecentCommandQueue()
        else:
            exec(pyCode)

        return pyCode

    def _addToRecentCommandQueue(self):
        cls = type(self)
        cmd = 'python("import %s; %s.%s().execute(addQueue=False)")' % (
            cls.__module__, cls.__module__, cls.__name__)
        label = self.COMMAND_LABEL or self.TOOL_NAME or self.BRIEF or cmd
        mel.eval('addToRecentCommandQueue("%s", "%s")' % (
            _escapeForMel(cmd), _escapeForMel(label)))

    def execPyCodeFromUI(self, code, *dummy):
        u"""
        UI コールバックから指定した Python コードを実行する。

        コールバックから渡される余分な引数は無視される。

        :param `str` code: 実行する Python コード。
        """
        self.execPyCode(code, echo=True)

    def isUIAlive(self):
        u"""
        表示した option box UI が存在しているかどうか。

        option box が閉じられたり他ツールに差し替えられたりした後に、
        別途保持しているインスタンスから UI の生存を確認できる。

        :rtype: `bool`
        """
        layout = self._tab_layout or self._custom_layout
        return bool(layout and cmds.layout(layout, ex=True))

    def show(self):
        u"""
        option box を表示する。

        既に UI が存在していれば、そのウィンドウを前面に出す。
        未生成の場合は Maya 標準の option box 領域を取得し、タブ、
        ボタン、メニューコールバックを設定する。
        """
        self.checkMayaVersion()

        layout = self._tab_layout or self._custom_layout
        if layout and cmds.layout(layout, ex=True):
            cmds.showWindow(layout.split('|')[0])
            return

        box = mel.eval('getOptionBox')
        cmds.setParent(box)

        if self.TAB_LABELS:
            self._tab_layout = cmds.tabLayout(
                tabsVisible=(len(self.TAB_LABELS) > 1),
                scrollable=True,
                preSelectCommand=self._onTabShown,
                cr=True)

            for idx, label in enumerate(self.TAB_LABELS):
                tabId = idx + 1
                self.createLayout(tabId)
                cmds.setParent(self._tab_layout)
                cmds.tabLayout(self._tab_layout, e=True, tli=(tabId, label))

            if self.DEFAULT_TAB_INDEX != 1:
                cmds.tabLayout(
                    self._tab_layout, e=True,
                    selectTabIndex=self.DEFAULT_TAB_INDEX)
        else:
            # NOTE:
            #   この形式では preSelectCommand による参照保持が無い。
            #   派生クラス側でインスタンスが解放されないように保持すること。
            self._custom_layout = self.createLayout(0)

        tabId = self._onTabShown()

        # NOTE:
        #   オプションボックス機構は過去の互換性の為の処理がされているようで、
        #   コールバックに python 関数や python コードをセットするとうまく動かない。
        #   コールバックのコードが mel か python のどちらのコードとして評価されるかは、
        #   mel か python の cmds のどちらからセットしたかで決まるようなので、mel.eval でセットする。
        codes = [
            'button("-e", "-l","%s", "-c","%s", getOptionBoxApplyBtn())' % (
                _escapeForMel(self.BUTTON_LABEL), self.melCB('_onApply')),
            'button("-e", "-c","%s", getOptionBoxSaveBtn())' % self.melCB('_onSave'),
            'button("-e", "-c","%s", getOptionBoxResetBtn())' % self.melCB('_onReset'),
            'setOptionBoxTitle("%s")' % _escapeForMel(self.title()),
            'menuItem("-e", "-l","Help on %s Options", "-c","%s", getOptionBoxHelpItem())' % (
                _escapeForMel(self.TOOL_NAME), self.melCB('showHelp')),
            'showOptionBox()',
        ]
        if self.APPLY_BUTTON_LABEL is not None:
            codes.append('button("-e", "-l","%s", getOptionBoxApplyBtn())' % (
                _escapeForMel(self.APPLY_BUTTON_LABEL),))
        if self.CLOSE_BUTTON_LABEL is not None:
            codes.append('button("-e", "-l","%s", getOptionBoxCloseBtn())' % (
                _escapeForMel(self.CLOSE_BUTTON_LABEL),))
        mel.eval('; '.join(codes))

        cmds.menuItem(_getMelVar('$gOptionBoxEditMenuSaveItem'), e=True, ecr=False)
        cmds.menuItem(_getMelVar('$gOptionBoxEditMenuResetItem'), e=True, ecr=False)
        cmds.menuItem(_getMelVar('$gOptionBoxHelpItem'), e=True, ecr=False)

        if MAYA_VERSION >= (2016, 5) and mel.eval('exists onCloseCommand'):
            cmds.window(box.split('|')[0], e=True, cc=lambda: _executeCommand('onCloseCommand'))

        self.growUpWindowSize(tabId, self.INIT_WIDTH, self.INIT_HEIGHT, 1)

    def showHelp(self, *args):
        u"""
        `HELP_URL` を表示する。

        Maya の :mayacmd:`showHelp` を優先し、失敗した場合は
        Python 標準の :mod:`webbrowser` にフォールバックする。
        """
        if self.HELP_URL:
            try:
                cmds.showHelp(self.HELP_URL, absolute=True)
            except Exception:
                import webbrowser
                webbrowser.open(self.HELP_URL)

    def growUpWindowSize(self, tabId=None, fitW=False, fitH=False, addW=0):
        u"""
        ウィンドウサイズがタブにとって十分でなければリサイズする。

        多くの場合、UI 構築後に呼ぶ。`fitW` や `fitH` を ``True`` にすると、
        小さくなる方向の調整も行う。

        :param `int` tabId:
            1 から始まるタブインデックス。省略時はカレントタブ。
        :param `bool` fitW: 幅が小さくなる場合もリサイズする。
        :param `bool` fitH: 高さが小さくなる場合もリサイズする。
        :param `int` addW: 計算された幅へ追加するピクセル数。
        """
        layout = self.getLayout(tabId)
        if not layout:
            return

        wnd = layout.split('|')[0]
        wndW, wndH = cmds.window(wnd, q=True, wh=True)
        wndW = _scaledSize(wndW)
        wndH = _scaledSize(wndH)
        width = self.MIN_WIDTH or (
            _scaledSize(cmds.layout(layout, q=True, w=True)) +
            _WINDOW_WIDTH_OFFSET + addW)
        height = self.MIN_HEIGHT or (
            _scaledSize(cmds.layout(layout, q=True, h=True)) + 80)

        if fitW or wndW < width:
            if fitH or wndH < height:
                cmds.window(wnd, e=True, wh=(width, height))
            else:
                cmds.window(wnd, e=True, w=width)
        elif fitH or wndH < height:
            cmds.window(wnd, e=True, h=height)

    def checkMayaVersion(self):
        u"""
        Maya バージョンをチェックし、非サポートならエラーにする。

        `SUPPORTED_VERSION` には ``(2024,)`` のようなタプルか、
        旧互換の数値を指定できる。
        """
        if _isUnsupportedMayaVersion(self.SUPPORTED_VERSION):
            raise RuntimeError(
                'Sorry, this tool supports maya version ' +
                str(self.SUPPORTED_VERSION) + ' or later.')

    def resetOptions(self):
        u"""
        保持しているオプション値をデフォルトにリセットする。

        `NO_RESETS` に指定したキーは対象外になる。
        """
        self.optionvar.resetToDefaults(ignores=self._no_reset_keys)

    def get(self, key):
        u"""
        保持している値を取得する。

        `keyToStore` で保存用キーへ変換した後、`get_` に処理を委譲する。

        :param `str` key: 実行用キー。
        :returns: 保存されている値。
        """
        return self.get_(self.keyToStore(key))

    def get_(self, rawkey):
        u"""
        保存用キーを指定して値を取得する。

        値の取得をカスタマイズしたい場合に派生クラスでオーバーライドする。
        標準では内部の :class:`~cymel.utils.optionvar.OptionVar` からそのまま返す。

        :param `str` rawkey: `keyToStore` で変換された後のキー。
        :returns: 保存されている値。
        """
        return self.optionvar[rawkey]

    def set(self, key, val):
        u"""
        値を保存する。

        `keyToStore` で保存用キーへ変換した後、`set_` に処理を委譲する。

        :param `str` key: 実行用キー。
        :param val: 保存する値。
        """
        self.set_(self.keyToStore(key), val)

    def set_(self, rawkey, val):
        u"""
        保存用キーを指定して値を保存する。

        値の保存をカスタマイズしたい場合に派生クラスでオーバーライドする。
        標準では内部の :class:`~cymel.utils.optionvar.OptionVar` にそのまま渡す。

        :param `str` rawkey: `keyToStore` で変換された後のキー。
        :param val: 保存する値。
        """
        self.optionvar[rawkey] = val

    def assemblePyCodeWithArgs(
            self, modName=None, funcName=None, args=None, kwargs=None,
            argKeys=None, ignoreKeys=None, qualifyKeys=None, asDict=False):
        u"""
        実行用 Python コードを生成するためのヘルパー。

        以下の順で引数が組み立てられる。

        1. `args` で指定された値が位置引数になる。
        2. `argKeys` で指定されたキーの保存値が位置引数として追加される。
        3. `kwargs` で指定された値がキーワード引数になる。
        4. 内部の optionVar からキーワード引数を自動収集する。

        `SKIP_DEFAULT_VALUES` が ``True`` の場合は、デフォルト値と同じ値は
        自動収集されない。`COMMAND_DEFAULTS` を使うと、実行コマンド側の
        デフォルト値が保存用 `DEFAULTS` と異なる場合の比較値を指定できる。

        自動収集では次の条件を考慮する。

        * `kwargs` に直接指定されたキーは重複収集しない。
        * `argKeys` に指定されたキーはキーワード引数としては収集しない。
        * `ignoreKeys` に含まれるキーは収集しない。
        * `qualifyKeys` が指定された場合は、そのキーだけを収集する。

        :param `str` modName:
            関数を含むモジュール名。`funcName` と共に指定すると
            ``import module; module.func(...)`` 形式を返す。
        :param `str` funcName:
            呼び出す関数名。省略した場合は引数リスト部分だけを返す。
        :param iterable args: 直接指定する位置引数の値。
        :param `dict` kwargs: 直接指定するキーワード引数の値。
        :param iterable argKeys: optionVar から位置引数として取り出すキー。
        :param container ignoreKeys: 自動収集から除外する実行用キー。
        :param container qualifyKeys: 自動収集の対象にする実行用キー。
        :param `bool` asDict:
            ``True`` の場合はコード文字列ではなくキーワード引数辞書を返す。
        :returns: Python コード文字列、またはキーワード引数辞書。
        """
        kwargs = kwargs.copy() if kwargs else {}
        ignoreKeys = set(ignoreKeys) if ignoreKeys else set()
        ignoreKeys.update(kwargs)
        if argKeys:
            ignoreKeys.update(argKeys)
        qualifyKeys = set(qualifyKeys) if qualifyKeys else None

        for rawkey in self._commandOptionKeys():
            if self.optionvar.hasDefault(rawkey):
                key = self.keyToExec(rawkey)
                if key not in ignoreKeys and (qualifyKeys is None or key in qualifyKeys):
                    kwargs[key] = self.get_(rawkey)

        if asDict:
            return kwargs

        codeArgs = []
        if args:
            codeArgs.extend([repr(x) for x in args])
        if argKeys:
            codeArgs.extend([repr(self.get(key)) for key in argKeys])
        codeArgs.extend(['%s=%r' % (key, val) for key, val in kwargs.items()])

        argCode = ', '.join(codeArgs)
        if funcName:
            if modName and modName != '__main__':
                return 'import %s; %s.%s(%s)' % (modName, modName, funcName, argCode)
            return '%s(%s)' % (funcName, argCode)
        return argCode

    def _commandOptionKeys(self):
        optvar = self.optionvar
        if self.SKIP_DEFAULT_VALUES:
            commandDefaults = self.COMMAND_DEFAULTS
            if commandDefaults:
                keys = [
                    key for key, val in optvar.items()
                    if (
                        commandDefaults[key] != val
                        if key in commandDefaults
                        else (not optvar.hasDefault(key) or optvar.getDefault(key) != val)
                    )]
            else:
                keys = optvar.nonDefaultKeys()
        else:
            keys = list(optvar)

        return keys

    def isTabReady(self, tabId):
        u"""
        タブの中身が生成済みなら :mayacmd:`setParent` して ``True`` を返す。

        `loadOptions` や `saveOptions` で、まだ表示されていない遅延生成タブを
        誤って操作しないために利用する。

        :param `int` tabId: 1 から始まるタブインデックス。
        :rtype: `bool`
        """
        layout = self.getLayout(tabId)
        if layout and cmds.layout(layout, q=True, nch=True):
            cmds.setParent(layout)
            return True
        return False

    def getLayout(self, tabId=None):
        u"""
        指定 ID のレイアウトを得る。

        :param `int` tabId:
            1 から始まるタブインデックス。省略時はカレントタブ。
            タブレイアウトを使わない場合は 0。
        :rtype: `str` or None
        """
        if self._tab_layout:
            if tabId is None:
                tabId = cmds.tabLayout(self._tab_layout, q=True, selectTabIndex=True)
            children = cmds.tabLayout(self._tab_layout, q=True, childArray=True)
            if children:
                return self._tab_layout + '|' + children[tabId - 1]
        if not tabId:
            return self._custom_layout

    def currentTabId(self):
        u"""
        カレントタブインデックスを得る。

        タブレイアウトを使っていない場合は 0 を返す。

        :rtype: `int`
        """
        return cmds.tabLayout(self._tab_layout, q=True, selectTabIndex=True) if self._tab_layout else 0

    def _onTabShown(self):
        layout = self._tab_layout
        if layout:
            tabId = cmds.tabLayout(layout, q=True, selectTabIndex=True)
            layout += '|' + cmds.tabLayout(layout, q=True, childArray=True)[tabId - 1]
        else:
            tabId = 0
            layout = self._custom_layout

        if not cmds.layout(layout, q=True, nch=True):
            try:
                isColumnLayout = cmds.objectTypeUI(layout) == 'columnLayout'
            except RuntimeError:
                isColumnLayout = False

            with WaitCursor():
                cmds.setParent(layout)
                if isColumnLayout:
                    cmds.setUITemplate('DefaultTemplate', pushTemplate=True)
                try:
                    self.createContents(tabId)
                    self.loadOptions(tabId)
                    self.updateState(tabId)
                finally:
                    if isColumnLayout:
                        cmds.setUITemplate(popTemplate=True)
        return tabId

    def _onApply(self, *args):
        self.save()
        self.execute(True)

    def _onSave(self, *args):
        self.save()

    def _onReset(self, *args):
        self.reset()

    def load(self):
        u"""
        オプション値を UI にロードする。

        現在の option box レイアウトを :mayacmd:`setParent` したうえで、
        `loadOptions` と `updateState` を呼ぶ。
        """
        cmds.setParent(self._tab_layout or self._custom_layout)
        self.loadOptions()
        self.updateState()

    def save(self):
        u"""
        UI の状態をオプション値として保存する。

        現在の option box レイアウトを :mayacmd:`setParent` したうえで、
        `updateState` と `saveOptions` を呼ぶ。数値フィールド編集中に
        Apply された場合などを考慮し、保存前に状態更新を行う。
        """
        cmds.setParent(self._tab_layout or self._custom_layout)
        self.updateState()
        self.saveOptions()

    def reset(self):
        u"""
        オプション値をリセットして UI を更新する。

        `NO_RESETS` の値を未保存状態で失わないように、まず `saveOptions` を呼び、
        その後 `resetOptions`、`loadOptions`、`updateState` の順で処理する。
        """
        cmds.setParent(self._tab_layout or self._custom_layout)
        self.saveOptions()
        self.resetOptions()
        self.loadOptions()
        self.updateState()

    def addMenu(self, **kwargs):
        u"""
        option box のメニューバーにメニューを追加する。

        :param kwargs: :mayacmd:`menu` コマンドに渡す引数。
        :rtype: `str`
        """
        current = cmds.setParent(q=True)
        window = (self._tab_layout or self._custom_layout or mel.eval('getOptionBox')).split('|')[0]
        try:
            cmds.setParent(window)
            menu = cmds.menu(**kwargs)
            self._menus.append(menu)
            return menu
        finally:
            if current:
                cmds.setParent(current)

    def makeWeakCB(self, name, *args, **kwargs):
        u"""
        このインスタンスを強参照しないメソッドコールバックを得る。

        UI コールバックに直接 bound method を渡すとインスタンス寿命が延びるため、
        弱参照経由で対象メソッドを呼ぶ関数を返す。

        :param `str` name: 呼び出すメソッド名。
        :param args: メソッドへ渡す固定位置引数。
        :param kwargs: メソッドへ渡す固定キーワード引数。
        :rtype: callable
        """
        wref = self._wref

        if args:
            if kwargs:
                def _func(*aa, **kk):
                    win = wref()
                    if win:
                        for key in kwargs:
                            if key not in kk:
                                kk[key] = kwargs[key]
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
                    for key in kwargs:
                        if key not in kk:
                            kk[key] = kwargs[key]
                    getattr(win, name)(*aa, **kk)
        else:
            def _func(*aa, **kk):
                win = wref()
                if win:
                    getattr(win, name)(*aa, **kk)
        return _func

def _isUnsupportedMayaVersion(version):
    if isinstance(version, tuple):
        return MAYA_VERSION < version
    return (MAYA_VERSION[0] + (MAYA_VERSION[1] / 10.)) < version


def _confirmException(err):
    msg = '%s:\n%s' % (type(err).__name__, UNICODE(err))
    cmds.confirmDialog(m=msg, icon='warning', t='Error', b=['OK'])
