# -*- coding: utf-8 -*-
u"""
Maya依存部分の全体で使用する共通定義。
"""
from . import initmaya
initmaya.initialize()

import sys
import re
from numbers import Number
from collections import Sequence, Iterable, Callable
#from collections import Container, Hashable, Iterable, Sequence, Mapping, Callable
from functools import partial

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

