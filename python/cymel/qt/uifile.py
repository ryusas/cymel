# -*- coding: utf-8 -*-
u"""
Qt Designer の .ui ファイルヘルパー。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import subprocess
import sys
from xml.etree.ElementTree import parse as _xml_parse

try:
    from cStringIO import StringIO as _StringIO
except ImportError:
    from io import StringIO as _StringIO

if sys.version_info[0] < 3:
    _UiBuffer = _StringIO
else:
    from io import BytesIO as _UiBuffer

from ..pyutils import BASESTR, IS_WINDOWS, execfile, getTempFilename
from .binding import QT_MAJOR_VERSION, QtWidgets, uic

__all__ = [
    'loadUiType',
]


if sys.version_info[0] < 3:
    def _execCode(code, globals=None, locals=None):
        if globals is None:
            globals = {}
        if locals is None:
            locals = globals
        exec('exec code in globals, locals')
else:
    def _execCode(code, globals=None, locals=None):
        if globals is None:
            globals = {}
        if locals is None:
            locals = globals
        exec(code, globals, locals)


def loadUiType(ui_file_name, translator=None):
    u"""
    Qt Designer の .ui ファイルを読み込み、``(form_class, base_class)`` を返す。
    """
    doc = _xml_parse(ui_file_name)
    widget_class_name = doc.find('widget').get('class')
    form_class_name = doc.find('class').text

    if translator:
        translator(doc)
        ui_source = _treeToUiBuffer(doc)
    else:
        ui_source = ui_file_name

    namespace = {}
    _execUi(ui_source, namespace)
    return namespace['Ui_' + form_class_name], getattr(QtWidgets, widget_class_name)


if uic:
    _compileUi = uic.compileUi

    def _uiToCode(xml_or_file_name):
        out = _StringIO()
        if isinstance(xml_or_file_name, BASESTR):
            with open(xml_or_file_name, 'rb') as f:
                _compileUi(f, out, indent=4)
        else:
            _compileUi(xml_or_file_name, out, indent=4)
        return out.getvalue()

    def _execUi(xml_or_file_name, globals=None, locals=None):
        code = _uiToCode(xml_or_file_name)
        _execCode(compile(code, '<ui>', 'exec'), globals, locals)

else:
    def _execUi(xml_or_file_name, globals=None, locals=None):
        pyfile = getTempFilename('.py', 'uic_')
        uifile = None
        try:
            if isinstance(xml_or_file_name, BASESTR):
                source = xml_or_file_name
            else:
                uifile = getTempFilename('.ui', 'uic_')
                _writeUiBuffer(xml_or_file_name, uifile)
                source = uifile
            subprocess.check_call([_findUic(), '-g', 'python', '-o', pyfile, source])
            execfile(pyfile, globals, locals)
        finally:
            for name in (pyfile, uifile):
                if name and os.path.exists(name):
                    try:
                        os.remove(name)
                    except OSError:
                        pass


def _treeToUiBuffer(tree):
    f = _UiBuffer()
    tree.write(f)
    f.seek(0)
    return f


def _writeUiBuffer(buf, file_name):
    if hasattr(buf, 'seek'):
        buf.seek(0)
        data = buf.read()
    else:
        data = buf
    mode = 'wb' if isinstance(data, bytes) else 'w'
    with open(file_name, mode) as f:
        f.write(data)


def _findUic():
    exe_name = 'uic.exe' if IS_WINDOWS else 'uic'
    exe_dir = os.path.normpath(os.path.dirname(sys.executable))
    parent, leaf = os.path.split(exe_dir)
    candidates = [os.path.join(exe_dir, exe_name)]
    if leaf == 'bin2':
        candidates.append(os.path.join(parent, 'bin', exe_name))
    if QT_MAJOR_VERSION >= 6:
        candidates.append(os.path.join(parent, 'libexec', exe_name))

    for path in candidates:
        if os.path.exists(path):
            return path
    raise ImportError('Qt uic is not found: ' + candidates[0])
