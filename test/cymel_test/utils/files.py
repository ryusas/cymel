# -*- coding: utf-8 -*-
u"""
Test of cymel.utils.files
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import os
import unittest

import maya.cmds as cmds

from cymel.pyutils.pyutils import getTempFilename
from cymel.utils import files


#------------------------------------------------------------------------------
class TestFiles(unittest.TestCase):
    u"""
    Test of cymel.utils.files
    """
    def test_scene_files(self):
        asset = getTempFilename('.ma', 'tmp_asset_')
        scene = getTempFilename('.ma', 'tmp_scene_')

        try:
            cmds.file(f=True, new=True)
            cube = cmds.polyCube()[0]
            files.saveSceneFile(scene)

            cmds.file(f=True, new=True)
            files.openSceneFile(scene)
            self.assertEqual(1, len(cmds.ls(type='mesh')))
            self.assertTrue(cmds.objExists(cube))

            cmds.select(cube)
            files.exportSceneFile(asset)

            cmds.file(f=True, new=True)
            origNum = len(cmds.ls(type='mesh'))
            files.importSceneFile(asset, namespace='tmp1')
            files.importSceneFile(asset, namespace='tmp2')
            self.assertEqual(2, len(cmds.ls(type='mesh')))
            self.assertTrue(cmds.objExists('tmp1:' + cube))
            self.assertTrue(cmds.objExists('tmp2:' + cube))
            files.referenceSceneFile(asset, namespace='tmp3')
            files.referenceSceneFile(asset, namespace='tmp4')
            self.assertEqual(4, len(cmds.ls(type='mesh')))
            self.assertEqual(2, len(cmds.ls(type='reference')))
            self.assertTrue(cmds.objExists('tmp3:' + cube))
            self.assertTrue(cmds.objExists('tmp4:' + cube))
            files.saveSceneFile(scene)

            cmds.file(f=True, new=True)
            files.openSceneFile(scene)
            self.assertEqual(4, len(cmds.ls(type='mesh')))
            self.assertEqual(2, len(cmds.ls(type='reference')))
            self.assertTrue(cmds.objExists('tmp1:' + cube))
            self.assertTrue(cmds.objExists('tmp2:' + cube))
            self.assertTrue(cmds.objExists('tmp3:' + cube))
            self.assertTrue(cmds.objExists('tmp4:' + cube))

        finally:
            if os.path.exists(scene):
                os.remove(scene)
            if os.path.exists(asset):
                os.remove(asset)


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
