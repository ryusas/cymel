# -*- coding: utf-8 -*-
u"""
Test of cymel.utils.operation
"""
import sys
import unittest

import maya.cmds as cmds

from cymel.utils.operation import (
    docmd, undoChunk, undoTransaction, nonUndoable,
    PreserveSelection,
)


#------------------------------------------------------------------------------
class TestOperation(unittest.TestCase):
    u"""
    Test of cymel.utils.operation
    """
    def assertSuccessful(self, proc, *args, **kwargs):
        try:
            return proc(*args, **kwargs)
        except Exception as e:
            self.fail('%s() raised %r' % (proc.__name__, e))

    def test_docmd(self):
        r = [0, False]
        def do():
            r[0] += 1
        def undo():
            r[0] -= 1
            r[1] = False
        def redo():
            r[0] += 1
            r[1] = True
        self.assertSuccessful(docmd, do, undo)
        self.assertEqual(r[0], 1)
        cmds.undo()
        self.assertEqual(r[0], 0)
        cmds.redo()
        self.assertEqual(r[0], 1)
        cmds.undo()
        self.assertEqual(r[0], 0)

        self.assertSuccessful(docmd, do, undo, redo)
        self.assertEqual(r[0], 1)
        cmds.undo()
        self.assertEqual(r[0], 0)
        cmds.redo()
        self.assertEqual(r[0], 1)
        self.assertTrue(r[1])
        cmds.undo()
        self.assertEqual(r[0], 0)
        self.assertFalse(r[1])

    def test_UndoChunk(self):
        cmds.file(f=True, new=True)
        cmds.createNode('transform')
        with undoChunk:
            cmds.createNode('transform')
            cmds.createNode('transform')
        cmds.undo()
        self.assertEqual(cmds.ls('transform*'), ['transform1'])

    def test_UndoTransaction(self):
        num = len(cmds.ls(type='transform'))
        try:
            with undoTransaction():
                for i in range(5):
                    cmds.createNode('transform')
                raise RuntimeError()
        except:
            pass
        self.assertEqual(num, len(cmds.ls(type='transform')))

    def test_NonUndoable(self):
        num = len(cmds.ls(type='transform'))
        with undoChunk:
            cmds.createNode('transform')
            with nonUndoable:
                cmds.createNode('transform')
                cmds.createNode('transform')
            cmds.createNode('transform')
        self.assertEqual(num + 4, len(cmds.ls(type='transform')))
        cmds.undo()
        self.assertEqual(num + 2, len(cmds.ls(type='transform')))

    def test_PreserveSelection(self):
        cmds.select('persp')

        with PreserveSelection():
            cmds.select('side')
            with PreserveSelection():
                cmds.select('top')
            self.assertEqual(cmds.ls(sl=True), ['side'])
        self.assertEqual(cmds.ls(sl=True), ['persp'])

        with PreserveSelection(True):
            cmds.select('side')
            with PreserveSelection(True):
                cmds.select('top')
            self.assertEqual(cmds.ls(sl=True), ['side'])
        self.assertEqual(cmds.ls(sl=True), ['persp'])


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
