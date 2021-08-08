# -*- coding: utf-8 -*-
u"""
全機能をインポートするための推奨処理。

以下のようにすることで、全機能を簡単にインポートできる。

.. code-block:: python

    from cymel.all import *

これによって以下が行われる。

.. code-block:: python

    from .constants import *
    from . import main as cm
    from . import ui as cmu

    import maya.cmds as cmds
    import maya.mel as mel
    import maya.api.OpenMaya as api
    import maya.api.OpenMayaAnim as apia

    import maya.utils
    import pprint
    maya.utils.formatGuiResult = pprint.pformat
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .constants import *
from . import main as cm
from . import ui as cmu

import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as api
import maya.api.OpenMayaAnim as apia
#import maya.OpenMaya as api1
#import maya.OpenMayaAnim as api1a

import maya.utils
import pprint
maya.utils.formatGuiResult = pprint.pformat

