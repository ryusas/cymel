# -*- coding: utf-8 -*-
u"""
3Dバウンディングボックスクラス。
"""
from ...common import *
from ...pyutils.immutable import OPTIONAL_MUTATOR_DICT as _MUTATOR_DICT
from .vector import _newV
import maya.api.OpenMaya as _api2
from math import sqrt

__all__ = ['BoundingBox', 'BB', 'ImmutableBoundingBox']

_MBB = _api2.MBoundingBox
_MP = _api2.MPoint


#------------------------------------------------------------------------------
class BoundingBox(object):
    u"""
    3Dバウンディングボックスクラス。
    """
    __slots__ = ('__data',)
    __hash__ = None

    def __new__(cls, *args):
        try:
            n = len(args)
            if n is 1:
                v = args[0]
                if hasattr(v, '_BoundingBox__data'):
                    return _newBB(_MBB(v.__data), cls)
                else:
                    p = getattr(v, '_Vector__data', None) or _MP(v)
                    return _newBB(_MBB(p, p), cls)
            elif n is 2:
                p0 = args[0]
                p0 = getattr(p0, '_Vector__data', None) or _MP(p0)
                p1 = args[1]
                p1 = getattr(p1, '_Vector__data', None) or _MP(p1)
                return _newBB(_MBB(p0, p1), cls)
            return _newBB(_MBB(*args), cls)
        except:
            raise ValueError(cls.__name__ + ' : not matching constructor found.')

    def __reduce__(self):
        return type(self), (self.min(), self.max())

    def __repr__(self):
        return type(self).__name__ + str(self)

    def __str__(self):
        return '(%s), %s))' % (str(self.__data.min)[:-4], str(self.__data.max)[:-4])

    def __eq__(self, v):
        try:
            return self.__data == v.__data
        except:
            return False

    def __ne__(self, v):
        try:
            return self.__data != v.__data
        except:
            return True

    def clear(self):
        self.__data.clear()
        return self

    def transformUsing(self, m):
        self.__data.transformUsing(m._Matrix__data)
        return self

    def expand(self, v):
        if hasattr(v, '_BoundingBox__data'):
            self.__data.expand(v.__data)
        else:
            self.__data.expand(v._Vector__data)
        return self

    def contains(self, p):
        return self.__data.contains(p._Vector__data)

    def intersects(self, bb, tol=0.):
        return self.__data.intersects(bb.__data, tol)

    def width(self):
        return self.__data.width

    def height(self):
        return self.__data.height

    def depth(self):
        return self.__data.depth

    def min(self):
        return _newV(self.__data.min)

    def max(self):
        return _newV(self.__data.max)

    def distanceToPoint(self, pnt):
        u"""
        点との距離を得る。

        ボックス内に位置する場合は 0. が返される。

        :type pnt: `.Vector`
        :param pnt: 参照する点。
        :rtype: `float`
        """
        bmin = self.__data.min
        bmax = self.__data.max

        x = max(bmin[0], pnt[0]) - min(bmax[0], pnt[0])
        y = max(bmin[1], pnt[1]) - min(bmax[1], pnt[1])
        z = max(bmin[2], pnt[2]) - min(bmax[2], pnt[2])
        return sqrt(x * x + y * y + z * z)

    def intersectedBox(self, bb):
        u"""
        別のボックスとの交差領域を新しいボックスとして得る。

        交差していなければ None となる。

        :type bb: `BoundingBox`
        :param bb: 別のバウンディングボックス。
        :rtype: `BoundingBox`
        """
        min0 = self.__data.min
        max0 = self.__data.max
        min1 = bb.__data.min
        max1 = bb.__data.max

        minx = max(min0[0], min1[0])
        miny = max(min0[1], min1[1])
        minz = max(min0[2], min1[2])
        maxx = min(max0[0], max1[0])
        maxy = min(max0[1], max1[1])
        maxz = min(max0[2], max1[2])

        if 0. <= maxx - minx and 0. <= maxy - miny and 0. <= maxz - minz:
            return _newBB(
                _MBB(_MP(minx, miny, minz), _MP(maxx, maxy, maxz)),
                type(self))

    def intersectedVolume(self, bb):
        u"""
        別のボックスとの交差領域の体積を得る。

        :type bb: `BoundingBox`
        :param bb: 別のバウンディングボックス。
        :rtype: `float`
        """
        min0 = self.__data.min
        max0 = self.__data.max
        min1 = bb.__data.min
        max1 = bb.__data.max

        dx = min(max0[0], max1[0]) - max(min0[0], min1[0])
        dy = min(max0[1], max1[1]) - max(min0[1], min1[1])
        dz = min(max0[2], max1[2]) - max(min0[2], min1[2])

        if dx < 0. or dy < 0. or dz < 0.:
            return 0.
        return dx * dy * dz

    def intersectedVolumeOrDistance(self, bb):
        u"""
        別のボックスとの交差領域の体積、又は距離の反転を得る。

        交差していればその領域の体積が返され、
        していなければ距離が負数で返される。

        :type bb: `BoundingBox`
        :param bb: 別のバウンディングボックス。
        :rtype: `float`
        """
        min0 = self.__data.min
        max0 = self.__data.max
        min1 = bb.__data.min
        max1 = bb.__data.max

        dx = min(max0[0], max1[0]) - max(min0[0], min1[0])
        dy = min(max0[1], max1[1]) - max(min0[1], min1[1])
        dz = min(max0[2], max1[2]) - max(min0[2], min1[2])

        sd = 0.
        if dx < 0.:
            sd = dx * dx
        if dy < 0.:
            sd += dy * dy
        if dz < 0.:
            sd += dz * dz
        if sd:
            return -sqrt(sd)
        return dx * dy * dz

    def distanceBetween(self, bb):
        u"""
        別のボックスとの距離を得る。

        :type bb: `BoundingBox`
        :param bb: 別のバウンディングボックス。
        :rtype: `float`
        """
        min0 = self.__data.min
        max0 = self.__data.max
        min1 = bb.__data.min
        max1 = bb.__data.max

        dx = min(max0[0], max1[0]) - max(min0[0], min1[0])
        dy = min(max0[1], max1[1]) - max(min0[1], min1[1])
        dz = min(max0[2], max1[2]) - max(min0[2], min1[2])

        sd = 0.
        if dx < 0.:
            sd = dx * dx
        if dy < 0.:
            sd += dy * dy
        if dz < 0.:
            sd += dz * dz
        return sqrt(sd)

    def cornerPoints(self):
        u"""
        コーナーの8点を得る。

        :rtype: `list`
        """
        p0 = self.__data.min
        p1 = self.__data.max
        return [
            _newV(p0),
            _newV(_MP(p0[0], p0[1], p1[2])),
            _newV(_MP(p0[0], p1[1], p0[2])),
            _newV(_MP(p0[0], p1[1], p1[2])),
            _newV(_MP(p1[0], p0[1], p0[2])),
            _newV(_MP(p1[0], p0[1], p1[2])),
            _newV(_MP(p1[0], p1[1], p0[2])),
            _newV(p1),
        ]

BB = BoundingBox  #: `BoundingBox` の別名。

_MUTATOR_DICT[BB] = (
    'clear',
    'transformUsing',
    'expand',
)
ImmutableBoundingBox = immutableType(BB)  #: `BoundingBox` の `immutable` ラッパー。


def _newBB(data, cls=BB):
    obj = _object_new(cls)
    _BB_setdata(obj, data)
    return obj
_object_new = object.__new__

_BB_setdata = BB._BoundingBox__data.__set__

