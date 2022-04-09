# -*- coding: utf-8 -*-
u"""
mel UI タイプ情報と、自動生成UIクラス。
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from ..common import *

#__all__ = [
#    'registerTypedCls',
#    'uiClass',
#    'uiParentClass',
#    'uiType',
#    'uiSetParent',
#    'dumpUIHierarchy',
#    'inspectUIInheritance',
#]

_cmds_objectTypeUI = cmds.objectTypeUI
_cmds_setParent = cmds.setParent


#------------------------------------------------------------------------------
def _generateSimpleClasses():
    u"""
    未生成のUIクラスを全て生成する。
    """
    for name in _UICMD_DICT:
        uiClass(name)


#------------------------------------------------------------------------------
def registerTypedCls(cls):
    u"""
    UIタイプ(コマンド)名と一対一で関連付けるクラスを登録する。

    :param `type` cls: クラス。
    """
    key = cls.UICMD.__name__
    if IS_UIMODE:
        registered = _UICMD_TO_UICLS_get(key)
        if registered:
            raise TypeError("%s failed because command '%s' is already linked with %s." % (cls.__name__, key, registered.__name__))
        #print('REGISTER: %s: %s(%s)' % (key, cls.__name__, cls.__bases__[0].__name__))
    _UICMD_TO_UICLS[key] = cls

_UICMD_TO_UICLS = {}  #: UIコマンドに対応するクラス辞書。クラス追加したらここに追加する。
_UICMD_TO_UICLS_get = _UICMD_TO_UICLS.get


#------------------------------------------------------------------------------
def uiClass(uitype):
    u"""
    UIタイプ名からクラスを得る。未登録なら生成される。

    :param `str` uitype: UIタイプ名。
    :rtype: `type`
    """
    cls = _UICMD_TO_UICLS_get(uitype)
    if cls:
        return cls

    base = uiClass(_UICMD_DICT[uitype])

    if base.__name__ == 'layout':
        doc = base.__doc__.replace(u'layout` の抽象基底クラス', uitype + u'` のラッパークラス')
    else:
        doc = u'mel の :mayacmd:`%s` ラッパークラス。' % uitype
                   
    clsname = uitype[0].upper() + uitype[1:]
    cls = type(clsname, (base,), {'__doc__': doc, 'UICMD': getattr(cmds, uitype)})
    setattr(sys.modules[__name__], clsname, cls)
    registerTypedCls(cls)
    return cls


def uiParentClass(uitype):
    u"""
    UIタイプ名から親クラスを得る。未登録なら生成される。

    :param `str` uitype: UIタイプ名。
    :rtype: `type`
    """
    return uiClass(_UICMD_DICT[uitype])


#------------------------------------------------------------------------------
def uiType(name):
    u"""
    UIパス名からそのタイプにマッチするコマンド名を得る。

    :param `str` name: UIパス名。
    :rtype: `str`
    """
    try:
        uitype = _cmds_objectTypeUI(name)
    except RuntimeError:
        if '|' in name:
            # Grp系の子など、正常に得られない場合の対応。
            for uitype in _ELEM_UITYPES:
                if getattr(cmds, uitype)(name, ex=True):
                    return uitype
            return
        # window でエラーになる場合の対応。
        uitype = _UITYPE_TO_UICMD['floatingWindow']
    else:
        # dockControl の場合、レイアウトが window と認識されるので、その対応。
        if uitype == 'floatingWindow' and '|' in name:
            for uitype in _LAYOUT_CMDNAMES:
                if getattr(cmds, uitype)(name, ex=True):
                    return uitype
            return 'window'

        # 辞書から適切なタイプを得る。
        uitype = _UITYPE_TO_UICMD.get(uitype, uitype)

    if isinstance(uitype, BASESTR):
        return uitype
    for cmd in uitype:
        if cmd(name, ex=True):
            return cmd.__name__


#------------------------------------------------------------------------------
def uiSetParent(path, **kwargs):
    u"""
    dockControl でパスが変わる事を想定した安全な setParent
    """
    try:
        _cmds_setParent(path, **kwargs)
    except:
        tkns = path.split('|')
        if len(tkns) >= 3:
            tmp = tkns[0] + '|' + tkns[1]
            try:
                fixedPath = _cmds_setParent(tmp)
            except:
                pass
            else:
                fixedPath += path[len(tmp):]
                _cmds_setParent(fixedPath, **kwargs)


#------------------------------------------------------------------------------
def dumpUIHierarchy(obj, indent=''):
    u"""
    UI 階層をダンプする。

    :param obj: UIオブジェクト。
    :param `str` indent: インデント文字列。
    """
    print(indent + obj.shortName() + ' (' + obj.type() + ')')
    getChildren = getattr(obj, 'children', None)
    if getChildren:
        indent += '  '
        for child in getChildren():
            dumpUIHierarchy(child, indent)


def inspectUIInheritance():
    u"""
    MayaのUI型について調べる。

    バージョンアップ時などに実行して調べるためのもの。
    そして、この出力を元に
    _UICMD_DICT と _UITYPE_TO_UICMD の定義を書く。

    * _UICMD_DICT は値が tuple なものについて確定する。
    * _UITYPE_TO_UICMD はそのまま利用。
    """
    from ..pyutils import CleanOrderedDict as OrderedDict

    _CONTROL_CMDNAMES = (
        'attrColorSliderGrp',
        'attrControlGrp',
        'attrFieldGrp',
        'attrFieldSliderGrp',
        'attrNavigationControlGrp',
        'button',
        'canvas',
        'channelBox',
        'checkBox',
        'checkBoxGrp',
        'cmdScrollFieldExecuter',
        'cmdScrollFieldReporter',
        'cmdShell',
        'colorIndexSliderGrp',
        'colorSliderButtonGrp',
        'colorSliderGrp',
        'commandLine',
        'componentBox',
        'floatField',
        'floatFieldGrp',
        'floatScrollBar',
        'floatSlider',
        'floatSlider2',
        'floatSliderButtonGrp',
        'floatSliderGrp',
        'gradientControl',
        'gradientControlNoAttr',
        'helpLine',
        ###'hudButton',
        ###'hudSlider',
        ###'hudSliderButton',
        'iconTextButton',
        'iconTextCheckBox',
        'iconTextRadioButton',
        ###'iconTextRadioCollection',
        'iconTextScrollList',
        'iconTextStaticLabel',
        'image',
        'intField',
        'intFieldGrp',
        'intScrollBar',
        'intSlider',
        'intSliderGrp',
        'layerButton',
        'messageLine',
        'nameField',
        'nodeTreeLister',
        'palettePort',
        'picture',
        'progressBar',
        'radioButton',
        'radioButtonGrp',
        ###'radioCollection',
        'rangeControl',
        'scriptTable',
        'scrollField',
        'separator',
        'shelfButton',
        'soundControl',
        'swatchDisplayPort',
        'switchTable',
        'symbolButton',
        'symbolCheckBox',
        'text',
        'textField',
        'textFieldButtonGrp',
        'textFieldGrp',
        'textScrollList',
        'timeControl',
        'timePort',
        'toolButton',
        ###'toolCollection',
        'treeLister',
        'treeView',
    )  #: 調査対象の control 系コマンド。

    _MENU_CMDNAMES = (
        #'artBuildPaintMenu',
        'attrEnumOptionMenu',
        'attrEnumOptionMenuGrp',
        #'attributeMenu',
        ###'hotBox',
        'menu',
        'menuItem',
        'menuSet',
        ###'menuSetPref',
        'popupMenu',
        'optionMenu',
        'optionMenuGrp',
        ###'radioMenuItemCollection',
        ###'saveMenu',
    )  #: 調査対象の menu 系コマンド。

    _WINDOW_CMDNAMES = (
        #'colorEditor',
        #'confirmDialog',
        ###'createEditor',
        ###'defaultNavigation',
        ###'editor',
        ###'editorTemplate',
        #'fontDialog',
        #'layoutDialog',
        ###'minimizeApp',
        #'progressWindow',
        #'promptDialog',
        ###'refreshEditorTemplates',
        ###'scriptEditorInfo',
        ###'showSelectionInTitle',
        ###'showWindow',
        ###'toggleWindowVisibility',
        'window',
        ###'windowPref',
    )  #: 調査対象の window 系コマンド。

    _NO_EX_CMDNAMES = frozenset((
        'attrControlGrp',
        'colorEditor',
        'fontDialog',
        'layoutDialog',
        'progressWindow',
        'promptDialog',
    ))  #: -ex フラグを持たないコマンド。

    layoutcmds = [getattr(cmds, s) for s in _LAYOUT_CMDNAMES]
    layoutcmds_ = [c for c in layoutcmds if not c.__name__ in _NO_EX_CMDNAMES] + [cmds.layout, cmds.control]

    uicmds = layoutcmds + [getattr(cmds, s) for s in (_CONTROL_CMDNAMES + _MENU_CMDNAMES)]
    uicmds_ = [c for c in uicmds if not c.__name__ in _NO_EX_CMDNAMES] + [cmds.layout, cmds.control]

    wincmds = [getattr(cmds, s) for s in _WINDOW_CMDNAMES]
    wincmdSet = frozenset(wincmds)
    wincmds_ = [c for c in wincmds if not c.__name__ in _NO_EX_CMDNAMES] + [cmds.layout, cmds.control]

    _uitypeToUicmd = OrderedDict()
    _uitypeDict = OrderedDict()

    # UIを実際に生成して調べる関数。
    def _checkUI(cmd):
        name = str(cmd.__name__)

        # UIを生成。ものによっては特別な判定。
        if name == 'timeControl':
            ui = 'timeControl1'
        elif name == 'radioButton':
            cmds.radioCollection()
            ui = cmd()
        elif name == 'iconTextRadioButton':
            cmds.iconTextRadioCollection()
            ui = cmd()
        elif name == 'toolButton':
            cmds.toolCollection()
            ui = cmd()
        elif name == 'attrControlGrp':
            ui = cmd(a='persp.tx')
        elif name == 'toolBar':
            ui = cmd(a='top', con=curWnd)
        else:
            ui = cmd()

        # 各コマンドを -ex でチェックして親タイプを判別する。
        parents = []
        if cmd in wincmdSet:
            parents = [c.__name__ for c in wincmds_ if c != cmd and c(ui, ex=True)]
        elif cmd.__name__.endswith('Grp'):
            parents = [c.__name__ for c in layoutcmds_ if c != cmd and c(ui, ex=True)]
        else:
            parents = [c.__name__ for c in uicmds_ if c != cmd and c(ui, ex=True)]

        # objectTypeUI でUIタイプをそのまま得られない場合の辞書を作成。
        try:
            uitype = str(cmds.objectTypeUI(ui))
        except RuntimeError:
            uitype = "<%s>" % uiType(ui)
        else:
            if not name in _NO_EX_CMDNAMES and not hasattr(cmds, uitype):
                elem = _uitypeToUicmd.get(uitype)
                if elem:
                    if isinstance(elem, BASESTR):
                        _uitypeToUicmd[uitype] = [elem, name]
                    else:
                        elem.append(name)
                else:
                    _uitypeToUicmd[uitype] = name

        #if 'control' in parents:
        #    print(name, uitype, uiType(ui), parents)
        #else:
        #    print('####', name, uitype, uiType(ui), parents)
        _uitypeDict[name] = parents

    # 全UIタイプを実際に生成して調べる。
    curWnd = cmds.window()
    cmds.scrollLayout()
    lyt = cmds.columnLayout()
    for cmd in uicmds:
        cmds.setParent(lyt)
        _checkUI(cmd)
    cmds.showWindow(curWnd)

    for cmd in wincmds:
        _checkUI(cmd)
    cmds.showWindow()

    # _UICMD_DICT の雛形を書き出す。
    print('_UICMD_DICT = {')
    _uitypeDict1 = OrderedDict()
    _uitypeDict2 = OrderedDict()
    for k, parents in _uitypeDict.items():
        try:
            del parents[parents.index('menuSet')]
        except:
            pass
        n = len(parents)
        if n == 1:
            _uitypeDict1[k] = parents[0]
        elif n == 2 and 'layout' in parents:
            _uitypeDict1[k] = 'layout'
        elif n == 3:
            for candidate in ('rowLayout', 'tabLayout'):
                if candidate in parents:
                    _uitypeDict1[k] = candidate
        if not k in _uitypeDict1:
            _uitypeDict2[k] = parents
    for k, v in _uitypeDict1.items():
        print("    %r: %r," % (k, v))
    for k, v in _uitypeDict2.items():
        print("    %r: %r," % (k, tuple(v)))
    print('}')

    # _UITYPE_TO_UICMD の雛形を書き出す。
    print('_UITYPE_TO_UICMD = {')
    for k, v in _uitypeToUicmd.items():
        if isinstance(v, BASESTR):
            print("    %r: '%s'," % (k, v))
        else:
            print("    %r: (cmds.%s,)," % (k, ', cmds.'.join(v)))
    print('}')


#------------------------------------------------------------------------------
_UICMD_DICT = {
    'columnLayout': 'layout',
    'flowLayout': 'layout',
    'formLayout': 'layout',
    'frameLayout': 'layout',
    'gridLayout': 'layout',
    'menuBarLayout': 'layout',
    'paneLayout': 'layout',
    'rowColumnLayout': 'layout',
    'rowLayout': 'layout',
    'scrollLayout': 'layout',
    'shelfLayout': 'layout',
    'shelfTabLayout': 'tabLayout',
    'toolBar': 'layout',
    'attrColorSliderGrp': 'rowLayout',
    'attrControlGrp': 'rowLayout',
    'attrFieldGrp': 'rowLayout',
    'attrFieldSliderGrp': 'rowLayout',
    'attrNavigationControlGrp': 'rowLayout',
    'channelBox': 'control',
    'checkBox': 'control',
    'checkBoxGrp': 'rowLayout',
    'cmdShell': 'control',
    'colorIndexSliderGrp': 'rowLayout',
    'colorSliderButtonGrp': 'rowLayout',
    'colorSliderGrp': 'rowLayout',
    'floatField': 'control',
    'floatFieldGrp': 'rowLayout',
    'floatScrollBar': 'control',
    'floatSlider': 'control',
    'floatSlider2': 'control',
    'floatSliderButtonGrp': 'rowLayout',
    'floatSliderGrp': 'rowLayout',
    'gradientControl': 'control',
    'gradientControlNoAttr': 'control',
    'helpLine': 'control',
    'iconTextButton': 'control',
    'iconTextCheckBox': 'control',
    'iconTextRadioButton': 'control',
    'iconTextScrollList': 'control',
    'iconTextStaticLabel': 'control',
    'intField': 'control',
    'intFieldGrp': 'rowLayout',
    'intScrollBar': 'control',
    'intSlider': 'control',
    'intSliderGrp': 'rowLayout',
    'layerButton': 'control',
    'messageLine': 'control',
    'nameField': 'control',
    'palettePort': 'control',
    'progressBar': 'control',
    'radioButton': 'control',
    'radioButtonGrp': 'rowLayout',
    'rangeControl': 'control',
    'scrollField': 'control',
    'separator': 'control',
    'shelfButton': 'control',
    'soundControl': 'control',
    'swatchDisplayPort': 'control',
    'symbolCheckBox': 'control',
    'text': 'control',
    'textField': 'control',
    'textFieldButtonGrp': 'rowLayout',
    'textFieldGrp': 'rowLayout',
    'textScrollList': 'control',
    'timeControl': 'control',
    'timePort': 'control',
    'toolButton': 'control',
    'treeView': 'control',
    'attrEnumOptionMenu': 'control',
    'attrEnumOptionMenuGrp': 'rowLayout',
    'optionMenuGrp': 'rowLayout',
    'window': 'control',

    'tabLayout': 'layout',  # ('shelfTabLayout', 'layout', 'control'),
    'button': 'control',  # ('canvas', 'control'),
    'canvas': 'button',  # ('button', 'control'),
    'cmdScrollFieldExecuter': 'scrollField',  # ('scrollField', 'control'),
    'cmdScrollFieldReporter': 'scrollField',  # ('scrollField', 'control'),
    'commandLine': 'control',  # ('paneLayout', 'control'),  # NOTE: layout を継承していないので微妙。lsUI(type='paneLayout') でも得られない。
    'componentBox': 'control',  # ('scriptTable', 'switchTable', 'control'),
    'image': 'control',  # ('picture', 'control'),
    'nodeTreeLister': 'treeLister',  # ('treeLister', 'control'),
    'picture': 'control',  # ('image', 'control'),
    'scriptTable': 'control',  # ('componentBox', 'switchTable', 'control'),
    'switchTable': 'control',  # ('componentBox', 'scriptTable', 'control'),
    'symbolButton': 'button',  # ('button', 'control'),
    'treeLister': 'control',  # ('nodeTreeLister', 'control'),
    'menu': 'control',  # ('popupMenu', 'control'),
    'menuItem': 'control',  # (),
    #'menuSet': (),
    'popupMenu': 'menu',  # ('menu', 'control'),
    'optionMenu': 'popupMenu',  # ('menu', 'popupMenu', 'control'),

    'dockControl': 'control',
    'layout': 'control',
}  #: UIタイプ名から親タイプ名を得る辞書。_initSimpleClasses では、これらを全てクラス化する。
if MAYA_VERSION >= (2017,):
    _UICMD_DICT['workspacePanel'] = 'control'
    _UICMD_DICT['workspaceControl'] = 'layout'

_UITYPE_TO_UICMD = {
    'rowGroupLayout': (
        cmds.attrColorSliderGrp, cmds.attrFieldGrp, cmds.attrFieldSliderGrp, cmds.attrNavigationControlGrp,
        cmds.checkBoxGrp, cmds.floatFieldGrp, cmds.floatSliderButtonGrp, cmds.floatSliderGrp, cmds.intFieldGrp,
        cmds.intSliderGrp, cmds.radioButtonGrp, cmds.textFieldButtonGrp, cmds.textFieldGrp, cmds.attrEnumOptionMenuGrp,
        cmds.optionMenuGrp,),
    'popupMenu': (cmds.optionMenu, cmds.popupMenu,),
    'TcolorIndexSlider': 'colorIndexSliderGrp',
    'TcolorSlider': (cmds.colorSliderButtonGrp, cmds.colorSliderGrp,),
    'port3D': (cmds.floatSlider2, cmds.gradientControl, cmds.gradientControlNoAttr, cmds.swatchDisplayPort,),
    'ThelpLine': 'helpLine',
    'outlineControl': 'iconTextScrollList',
    'staticImage': 'image',
    'TpalettePort': 'palettePort',
    'staticPicture': 'picture',
    'cmdScrollField': 'scrollField',
    'staticText': 'text',
    'field': 'textField',
    'commandMenuItem': 'menuItem',
    'TmenuSet': 'menuSet',
    'floatingWindow': 'window',
}  #: objectTypeUI の結果のコマンド名へのマップ。
if MAYA_VERSION >= (2017,):
    _UITYPE_TO_UICMD['floatingWindow'] = (cmds.workspaceControl, cmds.window,)

_ELEM_UITYPES = (
    'text',
    'checkBox',
    'floatField',
    'button',
    'floatSlider',
    'intSlider',
    'floatField',
    'textField',
    'intField',
    'optionMenu',
    'radioButton',
    'channelBox',
    'layout',
    'control',
)  #: rowGroupLayout の子など、objectTypeUI に失敗するもののタイプをチェックする為のコマンド群。

_LAYOUT_CMDNAMES = (
    'columnLayout',
    'flowLayout',
    'formLayout',
    'frameLayout',
    'gridLayout',
    'menuBarLayout',
    'paneLayout',
    'rowColumnLayout',
    'rowLayout',
    'scrollLayout',
    'shelfLayout',
    'shelfTabLayout',
    'tabLayout',
    'toolBar',
)  #: 調査対象の layout 系コマンド。

