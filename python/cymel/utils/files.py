# -*- coding: utf-8 -*-
u"""
Mayaファイル関連。
"""
from ..common import *
from .operation import (
    nonUndoable as _nonUndoable,
    PreserveSelection as _PreserveSelection,
)
import os
import maya.mel as mel

__all__ = [
    'openSceneFile',
    'importSceneFile',
    'referenceSceneFile',
    'saveSceneFile',
    'exportSceneFile',
]

_makedirs = os.makedirs
_path_basename = os.path.basename
_path_dirname = os.path.dirname
_path_exists = os.path.exists
_path_splitext = os.path.splitext

_mel_eval = mel.eval
_file = cmds.file
_select = cmds.select


#------------------------------------------------------------------------------
def openSceneFile(fname, addRecent=False, **kwargs):
    u"""
    シーンファイルをオープンする。

    :param `str` fname:
        シーンファイル名。
    :param `bool` addRecent:
        Recent Files に追加するかどうか。
    :rtype: `str`
    """
    try:
        res = _file(fname, f=True, o=True, **kwargs)
    except:
        raise

    if addRecent:
        _mel_eval('addRecentFile("%s", "%s")' % (res, _file(q=True, type=True)[0]))
    return res


def importSceneFile(fname, namespace=None, prefix=None, **kwargs):
    u"""
    シーンファイルをインポートする。

    :param `str` fname:
        シーンファイル名。
    :param `str` namespace:
        インポートしたノードにネームスペースを付加する場合に指定する。
        文字列ではない真値を指定すると、ファイル名から自動決定される。
    :param `str` prefix:
        インポートしたノードにプレフィックスを付加する場合に指定する。
        文字列ではない真値を指定すると、ファイル名から自動決定される。
    :rtype: `str`
    """
    if not _path_exists(fname):
        # ファイルが無い場合、カレントプロジェクトから読まれるので、厳密にチェックする。
        raise RuntimeError('File not found.')

    if namespace:
        if isinstance(namespace, BASESTR):
            kwargs['ns'] = namespace
        else:
            kwargs['ns'] = _path_splitext(_path_basename(fname))[0]
    elif prefix:
        if isinstance(namespace, BASESTR):
            kwargs['rpr'] = prefix
        else:
            kwargs['rpr'] = _path_splitext(_path_basename(fname))[0]
        if 'ra' not in kwargs and 'renameAll' not in kwargs:
            kwargs['ra'] = True

    return _file(fname, f=True, i=True, **kwargs)


def referenceSceneFile(fname, namespace=None, prefix=None, **kwargs):
    u"""
    シーンファイルをリファレンスする。

    :param `str` fname:
        シーンファイル名。
    :param `str` namespace:
        リファレンスしたノードにネームスペースを付加する場合に指定する。
        文字列ではない真値を指定すると、ファイル名から自動決定される。
    :param `str` prefix:
        リファレンスしたノードにプレフィックスを付加する場合に指定する。
        文字列ではない真値を指定すると、ファイル名から自動決定される。
    :rtype: `str`
    """
    if not _path_exists(fname):
        # ファイルが無い場合、カレントプロジェクトから読まれるので、厳密にチェックする。
        raise RuntimeError('File not found.')

    if namespace:
        if isinstance(namespace, BASESTR):
            kwargs['ns'] = namespace
        else:
            kwargs['ns'] = _path_splitext(_path_basename(fname))[0]
    elif prefix:
        if isinstance(namespace, BASESTR):
            kwargs['rpr'] = prefix
        else:
            kwargs['rpr'] = _path_splitext(_path_basename(fname))[0]

    return _file(fname, f=True, r=True, **kwargs)


def saveSceneFile(fname=None, ftype=None, addRecent=False, **kwargs):
    u"""
    シーンファイルをセーブする。

    :param `str` fname:
        シーンファイル名。新規やリネームでなければ省略可能。
        ディレクトリが存在しない場合は自動的に生成される。
    :param `str` ftype:
        ファイルタイプ名。拡張子から推測できる場合は省略可能。
    :param `bool` addRecent:
        Recent Files に追加するかどうか。
    :rtype: `str`
    """
    if fname:
        dname = _path_dirname(fname)
        if dname and not _path_exists(dname):
            _makedirs(dname)

        if not ftype:
            ext = _path_splitext(fname)[1].lower()
            if ext == '.mb':
                ftype = 'mayaBinary'
            elif ext == '.ma':
                ftype = 'mayaAscii'
            else:
                raise RuntimeError('Unable to guess file type from the extension.')

        _file(rn=fname)
        _file(type=ftype)

    else:
        fname = _file(q=True, sn=True)
        if not fname:
            raise RuntimeError('filename is not specified yet.')

    try:
        res = _file(f=True, s=True, **kwargs)
    except:
        raise

    if addRecent:
        _mel_eval('addRecentFile("%s", "%s")' % (res, _file(q=True, type=True)[0]))
    return res


def exportSceneFile(fname, sel=None, all=False, ftype=None, **kwargs):
    u"""
    シーンファイルをエクスポートする。

    :param `str` fname:
        シーンファイル名。
        ディレクトリが存在しない場合は自動的に生成される。
    :param sel:
        all=False の場合に出力するノードの名前やリスト。
        省略すると選択されているものがエクスポートされる。
    :param `bool` all:
        シーン全体をエクスポートするかどうか。
    :param `str` ftype:
        ファイルタイプ名。拡張子から推測できる場合は省略可能。
    :rtype: `str`
    """
    dname = _path_dirname(fname)
    if dname and not _path_exists(dname):
        _makedirs(dname)

    if not ftype:
        ext = _path_splitext(fname)[1].lower()
        if ext == '.mb':
            ftype = 'mayaBinary'
        elif ext == '.ma':
            ftype = 'mayaAscii'
        else:
            raise RuntimeError('Unable to guess file type from the extension.')

    if all:
        return _file(fname, ea=True, typ=ftype, f=True, **kwargs)
    elif sel:
        with _PreserveSelection(True):
            with _nonUndoable:
                _select(sel)
                return _file(fname, es=True, typ=ftype, f=True, **kwargs)
    else:
        return _file(fname, es=True, typ=ftype, f=True, **kwargs)

