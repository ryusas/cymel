from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os.path as _os_path
__path__.append(_os_path.join(__path__[0], 'python'))
del _os_path

from .boundingbox import *
from .eulerrotation import *
from .matrix import *
from .quaternion import *
from .vector import *
from .transformation import *

eulerrotation._newM = matrix._newM
eulerrotation._newQ = quaternion._newQ
eulerrotation._newV = vector._newV
eulerrotation._newX = transformation._newX

matrix._newE = eulerrotation._newE
matrix._newQ = quaternion._newQ
matrix._newV = vector._newV
matrix._newX = transformation._newX

quaternion._newE = eulerrotation._newE
quaternion._newM = matrix._newM
quaternion._newV = vector._newV
quaternion._newX = transformation._newX
quaternion._reverseEulerRotationInPlace = eulerrotation._reverseEulerRotationInPlace

vector._newE = eulerrotation._newE
vector._newM = matrix._newM
vector._newQ = quaternion._newQ
vector._newX = transformation._newX

def _all():
    from types import ModuleType
    return [k for k, v in globals().items()
        if not k.startswith('_') and not isinstance(v, ModuleType)]
__all__ = _all()
del _all
