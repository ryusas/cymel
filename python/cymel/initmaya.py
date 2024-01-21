# -*- coding: utf-8 -*-
u"""
スタンドアロン python (mayapy) からの Maya の初期化。

cymel 内の Maya に依存するモジュールがインポートされる際に
`initialize` がデフォルト設定で呼び出されるため、
このモジュールを明示的に使用する必要はほとんどないが、
初期化プロセスをカスタマイズしたい場合などに利用できる。
"""
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import sys
import os
import os.path as _os_path
import re
from .pyutils import (
    IS_WINDOWS as _IS_WINDOWS,
    USER_DOC_PATH as _USER_DOC_PATH,
    insertEnvPath as _insertEnvPath,
    #execfile as _execfile,
)

__all__ = [
    'MAYA_PRODUCT_VERSION',
    'MAYA_VERSION',
    'MAYA_VERSION_STR',
    'IS_UIMODE',
    'warning',

    'initialize',
    'initCymelPluginsPath',
    'isMayaInitialized',
    'getUserPrefsDir',
    'initMaya',
    'initMels',
    'callUserSetupMel',
    'initAutoPlugins',
    'initApiImmutables',
]

_os_path_join = _os_path.join
#_os_path_split = _os_path.split
_os_path_isdir = _os_path.isdir
_os_path_isfile = _os_path.isfile
_os_path_isabs = os.path.isabs
_os_path_normpath = _os_path.normpath
_os_path_dirname = _os_path.dirname


#------------------------------------------------------------------------------
def initialize(mels=False, plugins=False, userSetup=True):
    u"""
    必要な初期化を全て行う。

    以下が行われる。

    - `initCymelPluginsPath`

    - `initMaya` (既に初期化済みなら False となり何もされない)

      初期化されたら、さらに

      - mels=True なら `initMels` (plugins=plugins)
      - mels=False で plugins=True なら `initAutoPlugins`
      - userSetup=True なら `callUserSetupMel`

    - `initApiImmutables`

    初期化済みなら何もされないので、
    繰り返し呼び出しても問題はない。

    :param `bool` mels:
        `initMaya` が True のときに `initMels` を呼び出すかどうか。
        Maya の設定に依存する処理をしないなら、呼び出さなくても問題はないため、
        デフォルトでは False としている。

    :param `bool` plugins
        プラグインをオートロードするかどうか。

        プラグインは、シーンの requires で動的に解決されるし、
        バッチ処理で必要な場合は明示的にロードするようにすべきであり、
        処理負荷も大きいので、デフォルトでは False としている。

    :param `bool` userSetup
        `initMaya` が True のときに `callUserSetupMel` を呼び出すかどうか。
    """
    global _NOT_INITIALIZED
    if _NOT_INITIALIZED:
        _NOT_INITIALIZED = False
        initCymelPluginsPath()
        if initMaya():
            if mels:
                initMels(plugins=plugins)
            elif plugins:
                initAutoPlugins()
            userSetup and callUserSetupMel()
        initApiImmutables()
_NOT_INITIALIZED = True


def initCymelPluginsPath():
    u"""
    cymel が同梱する Maya プラグインのパスを設定する。

    繰り返し呼び出しても重複して設定されることはない。
    """
    path = _os_path_join(_os_path_dirname(__file__), 'plugins')
    _insertEnvPath(path, 'MAYA_PLUG_IN_PATH', noCheck=True, noUpdate=True)


def isMayaInitialized():
    u"""
    Maya が初期化済みかどうか。

    :rtype: `bool`
    """
    try:
        import maya.cmds as cmds
        cmds.about
    except:
        return False
    return True


if _IS_WINDOWS:
    def getUserPrefsDir():
        u"""
        ユーザープリファレンスディレクトリのパスを得る。

        :rtype: `str`
        """
        return _os_path_join(_initMayaAppDir(), MAYA_PRODUCT_VERSION, 'prefs').replace('\\', '/')

else:
    def getUserPrefsDir():
        u"""
        ユーザープリファレンスディレクトリのパスを得る。

        :rtype: `str`
        """
        return _os_path_join(_initMayaAppDir(), MAYA_PRODUCT_VERSION, 'prefs')


def initMaya():
    u"""
    Maya が初期化済みなら False を、未初期化なら初期化して True を返す。

    いずれにせよ、
    `MAYA_VERSION` などの cymel の定数は初期化される。

    初期化時に、パス上の全ての ``userSetup.py`` が呼び出されるが、
    ``userSetup.mel`` は呼び出されない。

    繰り返し呼び出しても問題はない。

    :rtype: `bool`
    """
    ret = not isMayaInitialized()
    if ret:
        _initMayaAppDir()
        _initMayaLocation()
        _initMayaStandalone()
    _initCymelConstants()
    return ret


def initMels(userPrefs=True, startup=True, plugins=False, namedCommand=True):
    u"""
    各種初期化MELを呼び出す（source する）。

    Maya の設定に依存する処理をしないなら、呼び出さなくても問題はない。

    一度呼び出したMELは繰り返し呼び出さないので、
    この関数を繰り返し呼び出しても問題はない。

    :param `bool` userPrefs:
        ユーザープリファレンスに関連するMELを呼び出すかどうか。
        plugins=True のときは True になる。

    :param `bool` startup:
        initStartup.mel を呼び出すかどうか。
        plugins=True のときは True になる。

    :param `bool` plugins:
        プラグインをオートロードするかどうか。

        プラグインは、シーンの requires で動的に解決されるし、
        バッチ処理で必要な場合は明示的にロードするようにすべきであり、
        処理負荷も大きいので、デフォルトでは False としている。

    :param `bool` namedCommand:
        ネームドコマンドを生成するかどうか。
        ホットキーに mel コードを結びつけるための概念であるため、
        UI が無ければ通常は不要なはずだが、処理負荷は大きくはないため、
        pymelに倣いデフォルトは True としてる。
    """
    #plugins = plugins and ('plugins' not in _initializedMels)
    if plugins:
        userPrefs = True
        startup = True
    userPrefs = userPrefs and ('userPrefs' not in _initializedMels)
    startup = startup and ('startup' not in _initializedMels)
    namedCommand = namedCommand and ('namedCommand' not in _initializedMels)

    try:
        # 呼び出す MEL リスト。
        upAxis = None
        prefs = getUserPrefsDir()
        mels = [
            #### 'defaultRunTimeCommands.mel',  # sourced automatically
            #### prefs + '/userRunTimeCommands.mel',  # sourced automatically

            userPrefs and 'createPreferencesOptVars.mel',
            userPrefs and 'createGlobalOptVars.mel',
            userPrefs and (prefs + '/userPrefs.mel'),

            startup and 'initialStartup.mel',

            #### $HOME/Documents/maya/projects/default/workspace.mel

            plugins and 'initialPlugins.mel',
            plugins and (prefs + '/pluginPrefs.mel'),

            #### 'initialGUI.mel',  # GUI
            #### 'initialLayout.mel',  # GUI
            #### prefs + '/windowPrefs.mel',  # GUI
            #### prefs + '/menuSetPrefs.mel',  # GUI
            #### 'hotkeySetup.mel',  # GUI

            namedCommand and 'namedCommandSetup.mel',
            namedCommand and (prefs + '/userNamedCommands.mel'),

            ####'initAfter.mel',  # GUI
        ]

        # 各 MEL の呼び出し。
        import maya.cmds as cmds
        from maya.mel import eval as mel_eval
        for f in mels:
            if f and (not _os_path_isabs(f) or _os_path_isfile(f)):
                # initialStartup.mel の実行で upAxis の変更が無いセットの warning が出るのを防ぐ。
                if f == 'initialStartup.mel':
                    upAxis = cmds.optionVar(q='upAxisDirection')
                    if upAxis == 'y':
                        cmds.upAxis(axis='z', rv=True)

                try:
                    #print('# ' + f)
                    mel_eval('source "' + f + '"')
                except:
                    pass

    finally:
        # upAxis のセットがうまくいかなかった場合の修復。
        if upAxis and upAxis != cmds.upAxis(q=True, axis=True):
            cmds.upAxis(axis=upAxis, rv=True)

        # 呼び出し済みのやつを記録。
        if plugins:
            _initializedMels.add('plugins')
        if userPrefs:
            _initializedMels.add('userPrefs')
        if startup:
            _initializedMels.add('startup')
        if namedCommand:
            _initializedMels.add('namedCommand')

_initializedMels = set()


def callUserSetupMel():
    u"""
    ``userSetup.mel`` を呼び出す。

    Mayaの仕様に合わせ、バージョンによって挙動が異なる。

    2020までは、MELパス上に存在する ``userSetup.mel`` のうち最優先の1つのみが呼び出されるが、
    それより後のバージョンでは全てがパス順に呼び出される。
    """
    from maya.mel import eval as mel_eval

    if _is2021orLater():
        num = 0
        for path in os.environ.get('MAYA_SCRIPT_PATH').split(os.pathsep):
            file = _os_path_join(path, 'userSetup.mel')
            if _os_path_isfile(file):
                try:
                    mel_eval('source "%s"' % (file.replace('\\', '/'),))
                    num += 1
                except:
                    pass
        if num:
            print('# userSetup.mel is done. (%s file%s)' % (num, ('' if num == 1 else 's')))

    elif mel_eval('exists userSetup'):
        try:
            mel_eval('source userSetup')
            print('# userSetup.mel is done.')
        except:
            pass


def initAutoPlugins():
    u"""
    オートロード設定のされたプラグインをロードする。

    以下を呼び出すことと同じ。::

      initMels(userPrefs=True, startup=True, plugins=True, namedCommand=False)
    """
    initMels(userPrefs=True, startup=True, plugins=True, namedCommand=False)


def initApiImmutables():
    u"""
    Maya API の数学クラスを `.immutable` ラップのための定義をする。
    """
    from .pyutils.immutables import OPTIONAL_MUTATOR_DICT
    import maya.api.OpenMaya as api2
    import maya.OpenMaya as api1

    def setApiNames(name, attrs, api1ignores=None):
        cls = getattr(api2, name)
        #for x in attrs:
        #    if not hasattr(cls, x):
        #        warning("API2 %s does not have '%s'" % (name, x))
        OPTIONAL_MUTATOR_DICT[cls] = attrs

        cls = getattr(api1, name)
        if api1ignores:
            attrs = [x for x in attrs if x not in api1ignores]
        #for x in attrs:
        #    if not hasattr(cls, x):
        #        warning("API1 %s does not have '%s'" % (name, x))
        OPTIONAL_MUTATOR_DICT[cls] = attrs

    setApiNames('MVector', (
        'normalize',
    ))
    setApiNames('MPoint', (
        'cartesianize',
        'rationalize',
        'homogenize',
    ))
    setApiNames('MEulerRotation', (
        'boundIt',
        'incrementalRotateBy',
        'invertIt',
        'reorderIt',
        'setToAlternateSolution',
        'setToClosestCut',
        'setToClosestSolution',
        'setValue',
    ))
    setApiNames('MQuaternion', (
        'conjugateIt',
        'invertIt',
        'negateIt',
        'normalizeIt',
        'setToXAxis',
        'setToYAxis',
        'setToZAxis',
        'setValue',
    ), ('setValue',))
    setApiNames('MMatrix', (
        'setElement',
        'setToIdentity',
        'setToProduct',
    ), ('setElement',))


#------------------------------------------------------------------------------
def _initMayaAppDir():
    u"""
    環境変数 MAYA_APP_DIR を設定する。
    """
    path = os.environ.get('MAYA_APP_DIR')
    if path:
        return path

    path = _os_path_join(_USER_DOC_PATH, 'maya')
    print('# Set MAYA_APP_DIR: ' + path)
    os.environ['MAYA_APP_DIR'] = path
    return path


def _initMayaLocation():
    u"""
    環境変数 MAYA_LOCATION を設定する。
    """
    # mayapy であれば MAYA_LOCATION は設定されている。
    path = os.environ.get('MAYA_LOCATION')
    if path and _os_path_isdir(_os_path_join(path, 'scripts/AETemplates')):
        # mayapy だけ抜き出した無効な環境でないかも調べている。
        return path

    # maya モジュールのパスは通っているものとして、そこから MAYA_LOCATION を推定。
    import maya
    path = _os_path_normpath(_os_path_join(_os_path_dirname(maya.__file__), '../../../..'))
    print('# Set MAYA_LOCATION: ' + path)
    os.environ['MAYA_LOCATION'] = path
    return path


def _initMayaStandalone():
    u"""
    Maya standalone を初期化する。
    """
    # 初期化と同時に sys.path に在る userSetup.py が先頭から順に _execfile される。
    # 呼び出されないバージョンもあったような記憶があるが現在は見当たらない。
    print('# Initializing Maya...')
    import maya.standalone as _maya_standalone
    _maya_standalone.initialize(name='cymel')

    # Python終了時の uninitialize の呼び出しを設定。
    uninitialize = getattr(_maya_standalone, 'uninitialize', None)
    if uninitialize:
        def _uninitialize():
            try:
                uninitialize()
            except:
                pass
            finally:
                if sys:
                    sys.stdout.flush()
                    sys.stderr.flush()
                    sys.__stdout__.flush()
                    sys.__stderr__.flush()
        import atexit
        atexit.register(_uninitialize)

    # 初期化で userSetup.py が呼び出されない場合はここで呼び出す（不明）。
    #if _is2021orLater():
    #    _call_userSetup_pys()

    print('# OK, done.')


def _is2021orLater():
    try:
        import maya.cmds as cmds
        return int(cmds.about(mjv=True)) >= 2021
    except:
        return False


#def _call_userSetup_pys():
#    u"""
#    userSetup.py を全てコールする。
#    """
#    for path in list(sys.path):
#        file = _os_path_join(path, 'userSetup.py')
#        if _os_path_isfile(file):
#            try:
#                _execfile(file)
#            except:
#                pass


def _initCymelConstants():
    u"""
    Mayaの状態を表す cymel の定数を初期化する。
    """
    global MAYA_PRODUCT_VERSION, MAYA_VERSION, MAYA_VERSION_STR, IS_UIMODE, warning
    if MAYA_VERSION:
        return

    import maya.cmds as cmds
    _about = cmds.about

    from maya.OpenMaya import MAYA_API_VERSION
    if MAYA_API_VERSION >= 20180000:
        # 2018 以降は .5 を想定しない。
        MAYA_PRODUCT_VERSION = str(MAYA_API_VERSION // 10000)
    else:
        # .5 があるバージョンは次の通り:
        #   2016.5 = 2016 Ext2
        #   2013.5 = 2013 Ext
        #   2011.5 = 2011 SAP
        v = MAYA_API_VERSION // 10
        if v == 20165:
            MAYA_PRODUCT_VERSION = '2016.5'
        elif v == 20135:
            MAYA_PRODUCT_VERSION = '2013.5'
        else:
            v //= 10
            # 2011.5 は MAYA_API_VERSION でも about(v=True) でも判別できないが非サポートなので問題ない。
            #if v == 2011:
            #    try:
            #        if re.search(r'.+/(\d+(?:\.\d+)?)', str(cmds.internalVar(upd=True))).group(1) == '2011.5':
            #            v = '2011.5'
            #    except:
            #        pass
            MAYA_PRODUCT_VERSION = str(v)

    try:
        # 2019.1 以降で利用できるオプション。
        v = (int(_about(mjv=True)), int(_about(mnv=True)), int(_about(pv=True)))
    except:
        v = float(MAYA_PRODUCT_VERSION)
        if v >= 2018.:
            # 2018nnpp: 2018.n.p
            v = _about(api=True)
            v = (v // 10000, (v - v // 10000 * 10000) // 100, v - v // 100 * 100)
        elif v == 2017.:
            # 2017xx: 2017.?
            v = _about(api=True) - 201700
            if v < 1:
                # 201700: 2017
                v = (2017, 0, 0)
            elif v < 20:
                # 201701: 2017update1
                v = (2017, 1, v - 1)
            else:
                # 201720: 2017update2
                # 201740: 2017update3
                # 201760: 2017update4
                # 201780: 2017update5
                v -= 20
                x = v // 20
                v = (2017, x + 2, v - x * 20)
                del x
        else:
            v = tuple([int(x) for x in MAYA_PRODUCT_VERSION.split('.')])
            v += (0,) * (3 - len(v))
    MAYA_VERSION = v  #: Mayaバージョンを表すタプル。アップデートを判別できるのは2017以降。 (majorVersion, minorVersion, patchVersion)
    v = 2
    while not MAYA_VERSION[v]:
        v -= 1
    MAYA_VERSION_STR = '.'.join([str(v) for v in MAYA_VERSION[:v + 1]]) #: Mayaバージョンの表記。
    del v

    IS_UIMODE = not _about(b=True)  #: MayaがUIモードかどうか。

    import maya.OpenMaya as _api1
    warning = _api1.MGlobal.displayWarning

MAYA_VERSION = None  #: Mayaバージョンを表すタプル。アップデートを判別できるのは2017以降。 (majorVersion, minorVersion, patchVersion)
MAYA_VERSION_STR = ''  #: Mayaバージョンの表記。
MAYA_PRODUCT_VERSION = None  #: 別々に存在できるMayaバージョン名（ '2020' や '2016.5' など）。
IS_UIMODE = False  #: MayaがUIモードかどうか。

if isMayaInitialized():
    _initCymelConstants()

