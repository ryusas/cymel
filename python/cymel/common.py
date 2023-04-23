# -*- coding: utf-8 -*-
u"""
Maya依存部分の全体で使用する共通定義。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from . import initmaya
initmaya.initialize()

import sys
import re
from numbers import Number
from functools import partial
try:
    from collections.abc import Sequence, Iterable, Callable
except ImportError:
    from collections import Sequence, Iterable, Callable

import maya.cmds as cmds

from .constants import *
from .pyutils.pyutils import *
from .pyutils import (
    immutable, immutableType, ImmutableDict,
    trackDestruction,
)
from .initmaya import (
    MAYA_VERSION, IS_UIMODE, warning,
)

ZERO = 0

