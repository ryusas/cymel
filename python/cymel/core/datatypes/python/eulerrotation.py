# -*- coding: utf-8 -*-
u"""
オイラー角回転クラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ...pyutils.immutables import OPTIONAL_MUTATOR_DICT as _MUTATOR_DICT
import maya.api.OpenMaya as _api2
from math import sqrt, atan2

__all__ = ['EulerRotation', 'E', 'ImmutableEulerRotation', 'degrot']

_ME = _api2.MEulerRotation
_MV = _api2.MVector
_MP = _api2.MPoint
_MX = _api2.MTransformationMatrix
_2_computeAlternateSolution = _ME.computeAlternateSolution
_2_computeBound = _ME.computeBound
_2_computeClosestCut = _ME.computeClosestCut
_2_computeClosestSolution = _ME.computeClosestSolution
_2_decompose = _ME.decompose

_TOLERANCE = _ME.kTolerance

_PI_2 = PI * .5
_2PI = PI + PI


#------------------------------------------------------------------------------
def degrot(x, y, z, order=XYZ):
    u"""
    Degrees で `EulerRotation` を生成するショートカット。
    """
    return E(x * TO_RAD, y * TO_RAD, z * TO_RAD, order)


#------------------------------------------------------------------------------
class EulerRotation(object):
    u"""
    オイラー角回転クラス。

    - `EulerRotation`
    - x, y, z, order=XYZ
    - 3値のシーケンス, order=XYZ
    - `.Quaternion`
    - `.Matrix`
    """
    __slots__ = ('__data',)
    __hash__ = None

    def __new__(cls, *args):
        if len(args) == 1:
            v = args[0]
            if hasattr(v, '_EulerRotation__data'):
                return _newE(_ME(v.__data), cls)
            if hasattr(v, '_Quaternion__data'):
                return _newE(v._Quaternion__data.asEulerRotation(), cls)
            if hasattr(v, '_Matrix__data'):
                return _newE(_MX(v._Matrix__data).rotation(False), cls)
            args = v  # 一般シーケンスとして。
        try:
            return _newE(_ME(*args), cls)
        except:
            raise ValueError(cls.__name__ + ' : not matching constructor found.')

    def __reduce__(self):
        d = self.__data
        return type(self), (d[0], d[1], d[2], d.order)

    def __repr__(self):
        return type(self).__name__ + str(self)

    def __str__(self):
        s = str(self.__data)
        i = s.index('k')
        return s[:i] + s[i + 1:]

    def __len__(self):
        return 3

    def __getitem__(self, i):
        return self.__data[i]

    def __setitem__(self, i, v):
        self.__data[i] = v

    def __getattr__(self, k):
        try:
            return getattr(self.__data, k)
        except:
            raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, k))

    def __setattr__(self, k, v):
        try:
            return setattr(self.__data, k, v)
        except:
            raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, k))

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

    def __neg__(self):
        return _newE(-self.__data)

    def __add__(self, v):
        try:
            return _newE(self.__data + v.__data)
        except:
            try:
                d = self.__data
                return _newE(_ME(d[0] + v[0], d[1] + v[1], d[2] + v[2], d.order))
            except:
                raise ValueError("%s + %r" % (type(self).__name__, v))

    def __iadd__(self, v):
        d = self.__data
        try:
            s = v.__data
            if d.order != s.order:
                s = s.reorder(d.order)
            d[0] += s[0]
            d[1] += s[1]
            d[2] += s[2]
        except:
            try:
                d[0] += v[0]
                d[1] += v[1]
                d[2] += v[2]
            except:
                raise ValueError("%s += %r" % (type(self).__name__, v))
        return self

    def __sub__(self, v):
        try:
            return _newE(self.__data - v.__data)
        except:
            try:
                d = self.__data
                return _newE(_ME(d[0] - v[0], d[1] - v[1], d[2] - v[2], d.order))
            except:
                raise ValueError("%s - %r" % (type(self).__name__, v))

    def __isub__(self, v):
        try:
            d = self.__data
            s = v.__data
            if d.order != s.order:
                s = s.reorder(d.order)
            d[0] -= s[0]
            d[1] -= s[1]
            d[2] -= s[2]
        except:
            try:
                d[0] -= v[0]
                d[1] -= v[1]
                d[2] -= v[2]
            except:
                raise ValueError("%s -= %r" % (type(self).__name__, v))
        return self

    def __mul__(self, v):
        if isinstance(v, Number):
            return _newE(self.__data * v)
        try:
            return _newE(self.__data * v.__data)  # 回転の合成。
        except:
            raise ValueError("%s * %r" % (type(self).__name__, v))

    def __imul__(self, v):
        if isinstance(v, Number):
            #self.__data *= v
            self.__data.__imul__(v)
        else:
            try:
                #self.__data *= v.__data
                self.__data.__imul__(v.__data)  # 回転の合成。
            except:
                raise ValueError("%s *= %r" % (type(self).__name__, v))
        return self

    def __rmul__(self, v):
        try:
            return _newE(self.__data * v)  # MEulerRotation のスカラー倍は __mul__ のみ。
        except:
            raise ValueError("%r * %s" % (v, type(self).__name__))

    def __truediv__(self, v):
        try:
            return _newE(self.__data * (1. / v))
        except:
            raise ValueError("%s / %r" % (type(self).__name__, v))

    def __itruediv__(self, v):
        try:
            #self.__data *= 1. / v
            self.__data.__imul__(1. / v)
        except:
            raise ValueError("%s /= %r" % (type(self).__name__, v))
        return self

    def __rtruediv__(self, v):
        try:
            d = self.__data
            return _newE(_ME(v / d[0], v / d[1], v / d[2], d.order))
        except:
            raise ValueError("%r / %s" % (v, type(self).__name__))

    if IS_PYTHON2:
        __div__ = __truediv__
        __idiv__ = __itruediv__
        __rdiv__ = __rtruediv__

    def isEquivalent(self, v, tol=_TOLERANCE):
        u"""
        ほぼ同値かどうか。

        :type v: `EulerRotation`
        :param v: 比較する値。
        :param `float` tol: 許容誤差。
        :rtype: `bool`
        """
        try:
            return self.__data.isEquivalent(v.__data, tol)
        except:
            return False

    def isZero(self, tol=_TOLERANCE):
        u"""
        ほぼゼロかどうか。

        :param `float` tol: 許容誤差。
        :rtype: `bool`
        """
        return self.__data.isZero(tol)

    def set(self, *args):
        u"""
        他の値をセットする。

        コンストラクタと同様に、以下の値を指定可能。

        - `EulerRotation`
        - x, y, z, order=XYZ
        - 3値のシーケンス, order=XYZ
        - `.Quaternion` (現状のorder維持)
        - `.Matrix` (現状のorder維持)

        :rtype: `EulerRotation` (self)
        """
        if len(args) == 1:
            v = args[0]
            if hasattr(v, '_EulerRotation__data'):
                self.__data.setValue(v.__data)
                return self
            if hasattr(v, '_Quaternion__data'):
                self.__data.setValue(v._Quaternion__data)
                return self
            if hasattr(v, '_Matrix__data'):
                if self.__data.order is XYZ:
                    _E_setdata(self, _MX(v._Matrix__data).rotation(False))
                else:
                    _E_setdata(self, _MX(v._Matrix__data).reorderRotation(self.__data.order + 1).rotation(False))
                return self
            if isinstance(v, _ME):  # 一般シーケンスとしてorder無視。
                self.__data.setValue(v[0], v[1], v[2])
                return self
        try:
            self.__data.setValue(*args)
        except:
            raise ValueError(type(self).__name__ + '.set : unsupported arguments.')
        return self

    setValue = set

    def asVector(self):
        u"""
        X, Y, Z をそのままセットした3次元ベクトルを得る。

        :rtype: `.Vector`
        """
        return _newV(_MP(self.__data))

    asV = asVector  #: `asVector` の別名。

    def asDegrees(self):
        u"""
        X, Y, Z を度数法の `list` として得る。

        :rtype: `list`
        """
        return [self.__data[0] * TO_DEG, self.__data[1] * TO_DEG, self.__data[2] * TO_DEG]

    asD = asDegrees  #: `asDegrees` の別名。

    def asQuaternion(self):
        u"""
        クォータニオンとして得る。

        :rtype: `.Quaternion`
        """
        return _newQ(self.__data.asQuaternion())

    asQ = asQuaternion  #: `asQuaternion` の別名。

    def asMatrix(self):
        u"""
        回転行列として得る。

        :rtype: `.Matrix`
        """
        return _newM(self.__data.asMatrix())

    asM = asMatrix  #: `asMatrix` の別名。

    def asTransformation(self):
        u"""
        トランスフォーメーションとして得る。

        :rtype: `.Transformation`
        """
        return _newX(dict(r=_newE(_ME(self.__data), ImmutableEulerRotation)))

    asX = asTransformation  #: `asTransformation` の別名。

    def incrementalRotateBy(self, axis, angle):
        u"""
        Perform an incremental rotation by the specified axis and angle.
        The rotation is broken down and performed in smaller steps so that the angles update properly.
        """
        self.__data.incrementalRotateBy(_MV(axis._Vector__data), angle)
        return self

    def inverse(self):
        u"""
        逆回転を得る。

        :rtype: `EulerRotation`
        """
        return _newE(self.__data.inverse())

    def invertIt(self):
        u"""
        逆回転をセットする。

        :rtype: `EulerRotation` (self)
        """
        self.__data.invertIt()
        return self

    def reorder(self, order):
        u"""
        回転結果を維持しつつ、オーダーを変更した値を得る。

        :param `int` order: 回転オーダー。
        :rtype: `EulerRotation`
        """
        return _newE(self.__data.reorder(order))

    def reorderIt(self, order):
        u"""
        回転結果を維持しつつ、オーダーを変更した値をセットする。

        :param `int` order: 回転オーダー。
        :rtype: `EulerRotation` (self)
        """
        self.__data.reorderIt(order)
        return self

    def bound(self):
        u"""
        回転結果を維持しつつ、各軸の角度を±πの範囲におさめた値を得る。

        :rtype: `EulerRotation`
        """
        return _newE(self.__data.bound())

    def boundIt(self, src=None):
        u"""
        回転結果を維持しつつ、各軸の角度を±πの範囲におさめた値をセットする。

        :type src: `EulerRotation`
        :param src: ソース回転。省略時は現在の回転。
        :rtype: `EulerRotation` (self)
        """
        if src:
            self.__data.boundIt(src.__data)
        else:
            self.__data.boundIt()
        return self

    def alternateSolution(self):
        u"""
        Returns a new `EulerRotation` with a different rotation which is
        equivalent to this one and has the same rotation order.
        Each rotation component will lie within +/- PI.
        """
        return _newE(self.__data.alternateSolution())

    def setToAlternateSolution(self, src):
        if src:
            self.__data.setToAlternateSolution(src.__data)
        else:
            self.__data.setToAlternateSolution()
        return self

    def closestSolution(self, dst):
        u"""
        Returns a new `EulerRotation` containing the rotation equivalent to
        this one which comes closest to target.
        """
        return _newE(self.__data.closestSolution(dst.__data))

    def setToClosestSolution(self, srcOrDst, dst=None):
        if dst:
            self.__data.setToClosestSolution(srcOrDst.__data, dst.__data)
        else:
            self.__data.setToClosestSolution(srcOrDst.__data)
        return self

    def closestCut(self, dst):
        u"""
        Returns a new `EulerRotation` containing the rotation which is full
        spin multiples of this one and comes closest to target.
        """
        return _newE(self.__data.closestCut(dst.__data))

    def setToClosestCut(self, srcOrDst, dst=None):
        if dst:
            self.__data.setToClosestCut(srcOrDst.__data, dst.__data)
        else:
            self.__data.setToClosestCut(srcOrDst.__data)
        return self

    @staticmethod
    def computeAlternateSolution(src):
        u"""
        Returns a rotation equivalent to rot which is not simply a multiple
        of it.
        """
        return _newE(_2_computeAlternateSolution(src.__data))

    @staticmethod
    def computeBound(src):
        u"""
        Returns a rotation equivalent to rot but bound within +/- PI.
        """
        return _newE(_2_computeBound(src.__data))

    @staticmethod
    def computeClosestCut(src, dst):
        u"""
        Returns the rotation which is full spin multiples of src and comes
        closest to target.
        """
        return _newE(_2_computeClosestCut(src.__data, dst.__data))

    @staticmethod
    def computeClosestSolution(src, dst):
        u"""
        Returns the rotation equivalent to src which comes closest to target.
        """
        return _newE(_2_computeClosestSolution(src.__data, dst.__data))

    @staticmethod
    def decompose(m, order):
        u"""
        Extracts from matrix a valid rotation having the specified rotation
        order. Note that this may be just one of several different rotations
        which could each give rise to the same matrix.
        """
        return _newE(_2_decompose(m._Matrix__data, order))

    def orderStr(self):
        u"""
        回転オーダーを文字列で得る。

        :rtype: `str`
        """
        return _ORDER_TO_STR[self.__data.order]

    def isGimbalLocked(self, tol=_TOLERANCE):
        u"""
        ジンバルロック状態かどうかを得る。

        ピッチ回転が±π/2の状態
        （ロール軸とヨー軸が重なった状態）
        をジンバルロックとする。

        :param `float` tolerance: 許容誤差。
        :rtype: `bool`
        """
        return -tol < abs(boundAngle(self.__data[_ORDER_TO_AXES[self.__data.order][1]])) - _PI_2 < tol

    def reverseDirection(self):
        u"""
        同じ姿勢の逆周り回転を得る。

        `asQuaternion` で得られるクォータニオンが反転する。

        :rtype: `EulerRotation`
        """
        #return _newE(_reverseRotation(_ME(self.__data), self.__data.asQuaternion().w))
        r = _ME(self.__data)
        _reverseEulerRotationInPlace(r)
        return _newE(r)

    def setToReverseDirection(self):
        u"""
        同じ姿勢の逆周り回転をセットする。

        `asQuaternion` で得られるクォータニオンが反転する。

        :rtype: `EulerRotation` (self)
        """
        #self.__data = _reverseRotation(self.__data, self.__data.asQuaternion().w)
        _reverseEulerRotationInPlace(self.__data)
        return self

    @classmethod
    def makeYawPitch(cls, vec, order=XYZ):
        u"""
        球面上のベクトルからヨーとピッチの2軸回転を得る。

        基準軸を指定方向へ向けるヨー、ピッチの回転が得られる。

        回転オーダーは、そのまま
        初期方向を表す基準軸、ピッチ回転軸、ヨー回転軸
        を表す。

        :type vec: `.Vector`
        :param vec: 球面上の位置を表す単位ベクトル。
        :param `int` order: 回転オーダー。
        :rtype: `EulerRotation`
        """
        return cls(_MAKE_YAW_PITCH[order](vec), order)

E = EulerRotation  #: `EulerRotation` の別名。

_MUTATOR_DICT[E] = (
    'set',
    'setValue',
    'incrementalRotateBy',
    'invertIt',
    'reorderIt',
    'boundIt',
    'setToAlternateSolution',
    'setToClosestSolution',
    'setToClosestCut',
    'setToReverseDirection',
)
ImmutableEulerRotation = immutableType(E)  #: `EulerRotation` の `immutable` ラッパー。


def _newE(data, cls=E):
    obj = _object_new(cls)
    _E_setdata(obj, data)
    return obj
_object_new = object.__new__

_E_setdata = E._EulerRotation__data.__set__

E.Zero = ImmutableEulerRotation()  #: ゼロ。

E.Tolerance = _TOLERANCE  #: 同値とみなす許容誤差。

E.REVERSE_ORDER = (ZYX, XZY, YXZ, YZX, ZXY, XYZ)  #: 逆順の回転オーダーを得られるテーブル。

_ORDER_TO_STR = ('XYZ', 'YZX', 'ZXY', 'XZY', 'YXZ', 'ZYX',)
_STR_TO_ORDER = ImmutableDict([(v, i) for i, v in enumerate(_ORDER_TO_STR)])

E.ORDER_TO_STR = _ORDER_TO_STR  #: 回転オーダーから文字列を得るテーブル。
E.STR_TO_ORDER = _STR_TO_ORDER  #: 文字列から回転オーダーを得る辞書。

_ORDER_TO_AXES = (
    (AXIS_X, AXIS_Y, AXIS_Z),
    (AXIS_Y, AXIS_Z, AXIS_X),
    (AXIS_Z, AXIS_X, AXIS_Y),
    (AXIS_X, AXIS_Z, AXIS_Y),
    (AXIS_Y, AXIS_X, AXIS_Z),
    (AXIS_Z, AXIS_Y, AXIS_X),
)
_AXES_TO_ORDER = ImmutableDict([(v, i) for i, v in enumerate(_ORDER_TO_AXES)])

E.ORDER_TO_AXES = _ORDER_TO_AXES  #: 回転オーダーから軸IDが3つ並んだtupleを得るテーブル。
E.AXES_TO_ORDER = _AXES_TO_ORDER  #: 軸IDが3つ並んだtupleから回転オーダーを得る辞書。

#_ROLL_AXES, _PITCH_AXES, YAW_AXES = zip(*_ORDER_TO_AXES)

if IS_PYTHON2:
    del i, v


#------------------------------------------------------------------------------
def _init_make_yaw_pitch():
    def _pch_yaw(d, h, v):
        return atan2(v, sqrt(d * d + h * h)), atan2(h, d)

    def _yawpitch_XYZ(vec):
        pch, yaw = _pch_yaw(vec[0], vec[1], -vec[2])
        return 0., pch, yaw

    def _yawpitch_YZX(vec):
        pch, yaw = _pch_yaw(vec[1], vec[2], -vec[0])
        return yaw, 0., pch

    def _yawpitch_ZXY(vec):
        pch, yaw = _pch_yaw(vec[2], vec[0], -vec[1])
        return pch, yaw, 0.

    def _yawpitch_XZY(vec):
        pch, yaw = _pch_yaw(vec[0], -vec[2], vec[1])
        return 0., yaw, pch

    def _yawpitch_YXZ(vec):
        pch, yaw = _pch_yaw(vec[1], -vec[0], vec[2])
        return pch, 0., yaw

    def _yawpitch_ZYX(vec):
        pch, yaw = _pch_yaw(vec[2], -vec[1], vec[0])
        return yaw, pch, 0.

    return (
        _yawpitch_XYZ,
        _yawpitch_YZX,
        _yawpitch_ZXY,
        _yawpitch_XZY,
        _yawpitch_YXZ,
        _yawpitch_ZYX,
    )
_MAKE_YAW_PITCH = _init_make_yaw_pitch()  #: 球面上の指定方向を表すヨーピッチ回転を得る関数辞書。


#------------------------------------------------------------------------------
def _reverseEulerRotationInPlace(rot):
    # 全てを反転しても良い。
    #rot.x += _2PI if rot.x < 0. else -_2PI
    #rot.y += _2PI if rot.y < 0. else -_2PI
    #rot.z += _2PI if rot.z < 0. else -_2PI

    # 角度の絶対値が最大の軸だけ反転する。
    ax = abs(rot[0])
    ay = abs(rot[1])
    az = abs(rot[2])
    i = (0 if ax > az else 2) if ax > ay else (1 if ay > az else 2)
    rot[i] += _2PI if rot[i] < 0. else -_2PI


u"""
def _reverseRotation(r0, q0):
    # なるべく alternateSolution に頼りたいが、それで良いのか内積を確認しないといけない？
    r1 = r0.alternateSolution()
    q1 = r1.asQuaternion()
    if q0.x * q1.x + q0.y * q1.y + q0.z * q1.z + q0.w * q1.w < 0.:
        s1 = abs(r1.x) + abs(r1.y) + abs(r1.z)
    else:
        s1 = _reverse(r1)
    return r1 if s1 < _reverse(r0) else r0


def _reverse(rot):
    ax = abs(rot.x)
    ay = abs(rot.y)
    az = abs(rot.z)
    if ax > ay:
        if ax > az:
            rot.x += _2PI if rot.x < 0. else -_2PI
            return abs(rot.x) + ay + az
        else:
            rot.z += _2PI if rot.z < 0. else -_2PI
            return abs(rot.z) + ax + ay
    elif ay > az:
        rot.y += _2PI if rot.y < 0. else -_2PI
        return abs(rot.y) + ax + az
    else:
        rot.z += _2PI if rot.z < 0. else -_2PI
        return abs(rot.z) + ax + ay
"""
