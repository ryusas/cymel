# -*- coding: utf-8 -*-
u"""
A tiny Maya plug-in for executing any python callable object as command that can be undo and redo.

References:
    https://medium.com/@k_serguei/maya-python-api-2-0-and-the-undo-stack-80b84de70551

The above is an API story, but I have generalized it to be usable with python callable object.

Usage:
    import maya.cmds as cmds
    cmds.loadPlugin('dopycmd')

    def docmd(do, undo):
        cmds.dopycmd(hex(id(do)), hex(id(undo)))

    def doapi(mod):
        #cmds.dopycmd(hex(id(mod.doIt)), hex(id(mod.undoIt)))  # cause crash
        docmd(lambda: mod.doIt(), lambda: mod.undoIt())

    val = cmds.jointDisplayScale(q=True)
    docmd(lambda: cmds.jointDisplayScale(10), lambda: cmds.jointDisplayScale(val))

    import maya.api.OpenMaya as api
    mod = api.MDagModifier()
    mod.createNode('transform')
    doapi(mod)
    del mod

    cmds.undo()
    cmds.undo()
"""

from _ctypes import PyObj_FromPtr as _fromptr
import maya.OpenMayaMPx as api
_creator = lambda c: lambda: api.asMPxPtr(c())


class dopycmd(api.MPxCommand):
    name = 'dopycmd'

    def isUndoable(self):
        return True

    def doIt(self, args):
        do = _fromptr(long(args.asString(0), 0))
        self._undoit = _fromptr(long(args.asString(1), 0))
        if args.length() < 3:
            self._redoit = do
        else:
            self._redoit = _fromptr(long(args.asString(2), 0)) or do
        do()

    def redoIt(self):
        self._redoit()

    def undoIt(self):
        self._undoit()


def initializePlugin(mobj):
    def registerCmd(cls):
        try:
            pl.registerCommand(cls.name, _creator(cls))
        except:
            raise RuntimeError('Failed to register command: ' + cls.name)

    pl = api.MFnPlugin(mobj, 'Ryusuke Sasaki', '1.0.1')
    registerCmd(dopycmd)


def uninitializePlugin(mobj):
    def deregisterCmd(cls):
        try:
            pl.deregisterCommand(cls.name)
        except:
            raise RuntimeError('Failed to deregister command: ' + cls.name)

    pl = api.MFnPlugin(mobj)
    deregisterCmd(dopycmd)

