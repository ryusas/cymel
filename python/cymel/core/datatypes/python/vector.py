# -*- coding: utf-8 -*-
u"""
3Dベクトルクラス。
"""
from ...common import *
from ...pyutils.immutable import OPTIONAL_MUTATOR_DICT as _MUTATOR_DICT
import maya.api.OpenMaya as _api2
from math import sqrt

__all__ = ['Vector', 'V', 'ImmutableVector']

_MP = _api2.MPoint
_MV = _api2.MVector
_MQ = _api2.MQuaternion
_MM = _api2.MMatrix

_XYZ_AXES = (AXIS_X, AXIS_Y, AXIS_Z)
_TOLERANCE = _MV.kTolerance
_MP_Zero = _MP.kOrigin


#------------------------------------------------------------------------------
class Vector(object):
    u"""
    3Dベクトルクラス。

    座標と方向ベクトルを
    Maya API の :mayaapi2:`MPoint` と :mayaapi2:`MVector`
    のように使い分ける必要はなく、同じように扱うことができる。

    :mayaapi2:`MPoint` と同様に、
    同次座標を表現可能な w を持つが、
    w が 1 の場合は、長さ 3 のシーケンスとして振る舞う。
    その場合、w はインデックス指定では参照できず、
    属性としてのみ参照できる。

    w が 1 以外の場合は、長さ 4 のシーケンスとして振る舞う。
    また、その場合のみ `str` や `repr` で確認できる。

    `.Matrix` を乗じると、
    :mayaapi2:`MPoint` のように平行移動が可能だが、
    :mayaapi2:`MVector` のように平行移動無しの変換をするには
    w を 0 に設定せずとも `xform3` メソッドを利用できる。

    つまり、同次座標表現をしない限り、w は常に 1 で使用すると良い。

    コンストラクタでは以下の値を指定可能。

    - `Vector`
    - x, y, z, w
    - x, y, z
    - x, y
    - 4値までのシーケンス

    .. note::
        w がこのような特殊な振る舞いをするのは、
        API 等の他のオブジェクトとの可換性を確保するため。

        w に 1 以外を明示しない限り、
        :mayaapi2:`MVector` コンストラクタのように長さ 4 の
        シーケンスを受け付けないものにも渡すことができる。

        また、w に 1 以外を明示した場合は、:mayaapi2:`MPoint` や
        `list` などと交換した際にも、きちんとその情報が継承される。
    """
    __slots__ = ('__data',)
    __hash__ = None

    def __new__(cls, *args):
        if len(args) is 1:
            v = args[0]
            if hasattr(v, '_Vector__data'):
                return _newV(_MP(v.__data), cls)
        try:
            return _newV(_MP(*args), cls)
        except:
            raise ValueError(cls.__name__ + ' : not matching constructor found.')

    def __reduce__(self):
        return type(self), tuple(self.__data)

    def __repr__(self):
        if self.__data[3] == 1.:
            return '%s(%f, %f, %f)' % (type(self).__name__, self.__data[0], self.__data[1], self.__data[2])
        return '%s(%f, %f, %f, %f)' % ((type(self).__name__,) + tuple(self.__data))

    def __str__(self):
        if self.__data[3] == 1.:
            return '(%f, %f, %f)' % (self.__data[0], self.__data[1], self.__data[2])
        return '(%f, %f, %f, %f)' % tuple(self.__data)

    def __len__(self):
        return 3 if self.__data[3] == 1. else 4

    def __getitem__(self, i):
        if 0 <= i < 3 or (i == 3 and self.__data[3] != 1.):
            return self.__data[i]
        raise IndexError('Vector index out of range.')

    def __setitem__(self, i, v):
        if 0 <= i < 4:
            self.__data[i] = v
        raise IndexError('Vector index out of range.')

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
        d = self.__data
        return _newV(_MP(-d[0], -d[1], -d[2], d[3]))

    def __add__(self, v):
        try:
            d = self.__data
            s = v.__data
            return _newV(_MP(d[0] + s[0], d[1] + s[1], d[2] + s[2], d[3]))
        except:
            raise ValueError("%s + %r" % (type(self).__name__, v))

    def __iadd__(self, v):
        try:
            d = self.__data
            s = v.__data
            d[0] += s[0]
            d[1] += s[1]
            d[2] += s[2]
        except:
            raise ValueError("%s += %r" % (type(self).__name__, v))
        return self

    def __sub__(self, v):
        try:
            d = self.__data
            s = v.__data
            return _newV(_MP(d[0] - s[0], d[1] - s[1], d[2] - s[2], d[3]))
        except:
            raise ValueError("%s - %r" % (type(self).__name__, v))

    def __isub__(self, v):
        try:
            d = self.__data
            s = v.__data
            d[0] -= s[0]
            d[1] -= s[1]
            d[2] -= s[2]
        except:
            raise ValueError("%s -= %r" % (type(self).__name__, v))
        return self

    def __mul__(self, v):
        if hasattr(v, '_Matrix__data'):
            return _newV(self.__data * v._Matrix__data)
        elif hasattr(v, '_Quaternion__data'):
            v = _MV(self.__data).rotateBy(v._Quaternion__data)
            return _newV(_MP(v[0], v[1], v[2], self.__data[3]))
        elif isinstance(v, Number):
            return _newV(self.__data * v)
        else:
            try:
                d = self.__data
                s = v.__data
                return d[0] * s[0] + d[1] * s[1] + d[2] * s[2]
            except:
                raise ValueError("%s * %r" % (type(self).__name__, v))

    def __imul__(self, v):
        if hasattr(v, '_Matrix__data'):
            self.__data *= v._Matrix__data
        elif hasattr(v, '_Quaternion__data'):
            d = self.__data
            v = _MV(d).rotateBy(v._Quaternion__data)
            d[0] = v[0]
            d[1] = v[1]
            d[2] = v[2]
        else:
            try:
                self.__data *= v
            except:
                raise ValueError("%s *= %r" % (type(self).__name__, v))
        return self

    def __rmul__(self, v):
        try:
            return _newV(self.__data * v)  # MPoint のスカラー倍は __mul__ のみ。
        except:
            raise ValueError("%r * %s" % (v, type(self).__name__))

    def __div__(self, v):
        try:
            return _newV(self.__data / v)
        except:
            raise ValueError("%s / %r" % (type(self).__name__, v))

    def __idiv__(self, v):
        try:
            self.__data /= v
        except:
            raise ValueError("%s /= %r" % (type(self).__name__, v))
        return self

    def __rdiv__(self, v):
        try:
            d = self.__data
            return _newV(_MP(v / d[0], v / d[1], v / d[2], d[3]))
        except:
            raise ValueError("%r / %s" % (v, type(self).__name__))

    def __xor__(self, v):
        try:
            v = _MV(self.__data) ^ _MV(v.__data)
            return _newV(_MP(v[0], v[1], v[2], self.__data[3]))
        except:
            raise ValueError("%s ^ %r" % (type(self).__name__, v))

    def __ixor__(self, v):
        try:
            d = self.__data
            v = _MV(d) ^ _MV(v.__data)
            d[0] = v[0]
            d[1] = v[1]
            d[2] = v[2]
        except:
            raise ValueError("%s ^= %r" % (type(self).__name__, v))
        return self

    def __abs__(self):
        v = self.__data
        return _newV(_MP(abs(v[0]), abs(v[1]), abs(v[2]), abs(v[3])))

    def isEquivalent(self, v, tol=_TOLERANCE):
        u"""
        ほぼ同値かどうか。

        :type v: `Vector`
        :param v: 比較するベクトル。
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
        return self.__data.isEquivalent(_MP_Zero, tol)

    def isParallel(self, v, tol=_TOLERANCE):
        u"""
        2つの3次元ベクトルが平行かどうか。

        :type v: `Vector`
        :param v: 比較するベクトル。
        :param `float` tol: 許容誤差。
        :rtype: `bool`
        """
        return _MV(self.__data).isParallel(_MV(v.__data), tol)

    def set(self, *args):
        u"""
        他の値をセットする。

        コンストラクタと同様に、以下の値を指定可能。

        - `Vector`
        - x, y, z, w
        - x, y, z
        - x, y
        - 4値までのシーケンス

        :rtype: `Vector` (self)
        """
        if len(args) is 1:
            args = args[0]
            if hasattr(args, '_Vector__data'):
                args = args.__data
        try:
            for i, v in enumerate(args):
                self.__data[i] = v
        except:
            raise ValueError(type(self).__name__ + '.set : unsupported arguments.')
        return self

    def angle(self, v):
        u"""
        2つの3次元ベクトルの成す角を得る。

        :type v: `Vector`
        :param v: もう1方のベクトル。
        :rtype: `float`
        """
        return _MV(self.__data).angle(_MV(v.__data))

    def length(self):
        u"""
        3次元ベクトルの長さを得る。

        :rtype: `float`
        """
        d = self.__data
        return sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2])

    def lengthSq(self):
        u"""
        3次元ベクトルの長さの2乗を得る。

        :rtype: `float`
        """
        d = self.__data
        return d[0] * d[0] + d[1] * d[1] + d[2] * d[2]

    def normal(self):
        u"""
        正規化3次元ベクトルを得る。

        :rtype: `Vector`
        """
        v = _MV(self.__data).normalize()
        return _newV(_MP(v[0], v[1], v[2], self.__data[3]))

    def normalize(self):
        u"""
        正規化3次元ベクトルをセットする。

        :rtype: `Vector` (self)
        """
        d = self.__data
        v = _MV(d).normalize()
        d[0] = v[0]
        d[1] = v[1]
        d[2] = v[2]
        return self

    normalizeIt = normalize

    def rotateBy(self, q):
        u"""
        クォータニオンで回転したベクトルを得る。

        演算子 * でクォータニオンを乗じることと同じ。

        :type q: `.Quaternion`
        :param q: クォータニオン。
        :rtype: `Vector`
        """
        v = _MV(self.__data).rotateBy(q._Quaternion__data)
        return _newV(_MP(v[0], v[1], v[2], self.__data[3]))

    def rotateTo(self, v, factor=1.):
        u"""
        ベクトルを指定方向に向ける最小弧回転を得る。

        `.Quaternion`
        に2つのベクトルを渡して生成することと同じ。

        :type v: `Vector`
        :param v: 向ける方向。
        :param `float` factor: 完全に向ける量を 1.0 とする回転量。
        :rtype: `.Quaternion`
        """
        return _newQ(_MQ(_MV(self.__data), _MV(v.__data), factor))

    def transformAsNormal(self, m):
        u"""
        法線ベクトルとしてトランスフォームしたベクトルを得る。

        :type m: `.Matrix`
        :param m: 変換マトリックス。
        :rtype: `Vector`
        """
        src = self.__data
        w = src[3]
        src[3] = 0.
        dst = src * m._Matrix__data.inverse().transpose()
        src[3] = w
        dst[3] = w
        return _newV(dst)

    def distanceTo(self, v):
        u"""
        2つの位置ベクトル間の距離を得る。

        :type v: `Vector`
        :param v: もう1方の位置。
        :rtype: `float`
        """
        return self.__data.distanceTo(v.__data)

    def distanceSqTo(self, v):
        u"""
        2つの位置ベクトル間の2乗距離を得る。

        :type v: `Vector`
        :param v: もう1方の位置。
        :rtype: `float`
        """
        v = self.__data.distanceTo(v.__data)
        return v * v

    def cartesianize(self):
        u"""
        同次座標を直交座標(W=1)に変換する。

        (W*x, W*y, W*z, W) が (x, y, z, 1) に変換される。

        :rtype: `Vector` (self)
        """
        self.__data.cartesianize()
        return self

    def rationalize(self):
        u"""
        同次座標を有利形式に変換する。

        (W*x, W*y, W*z, W) が (x, y, z, W) に変換される。

        :rtype: `Vector` (self)
        """
        self.__data.rationalize()
        return self

    def homogenize(self):
        u"""
        有理形式の座標を同次座標に変換する。

        (x, y, z, W) が (W*x, W*y, W*z, W) に変換される。

        :rtype: `Vector` (self)
        """
        self.__data.homogenize()
        return self

    def cross(self, v):
        u"""
        3次元ベクトルの外積を得る。

        演算子 ^ と同じ。

        :type v: `Vector`
        :param v: もう1方のベクトル。
        :rtype: `Vector`
        """
        v = _MV(self.__data).__xor__(_MV(v.__data))
        return _newV(_MP(v[0], v[1], v[2], self.__data[3]))

    def dot(self, v):
        u"""
        3次元ベクトルの内積を得る。

        1x3 と 3x1 の行列としての乗算ともいえる。

        演算子 * と同じ。

        :type v: `Vector`
        :param v: もう1方のベクトル。
        :rtype: `float`
        """
        d = self.__data
        s = v.__data
        return d[0] * s[0] + d[1] * s[1] + d[2] * s[2]

    def dot4(self, v):
        u"""
        4次元ベクトルの内積を得る。

        1x4 と 4x1 の行列としての乗算ともいえる。

        :type v: `Vector`
        :param v: もう1方のベクトル。
        :rtype: `float`
        """
        d = self.__data
        s = v.__data
        return d[0] * s[0] + d[1] * s[1] + d[2] * s[2] + d[3] * s[3]

    def dot4r(self, v):
        u"""
        4次元ベクトルを 4x1 と 1x4 の行列として乗算する。

        :type v: `Vector`
        :param v: もう1方のベクトル。
        :rtype: `.Matrix`
        """
        a = self.__data
        b = v.__data
        return _newM(_MM([
            a[0] * b[0], a[0] * b[1], a[0] * b[2], a[0] * b[3],
            a[1] * b[0], a[1] * b[1], a[1] * b[2], a[1] * b[3],
            a[2] * b[0], a[2] * b[1], a[2] * b[2], a[2] * b[3],
            a[3] * b[0], a[3] * b[1], a[3] * b[2], a[3] * b[3],
        ]))

    def xform3(self, m):
        u"""
        3次元ベクトル（方向ベクトル）をトランスフォームする。
        """
        src = self.__data
        w = src[3]
        src[3] = 0.
        dst = src * m._Matrix__data
        src[3] = w
        dst[3] = w
        return _newV(dst)

    def xform4(self, m):
        u"""
        4次元ベクトル（3次元同次座標）をトランスフォームする。

        演算子 * で行列を乗じることと同じ。

        :type m: `.Matrix`
        :param m: 変換マトリックス。
        :rtype: `Vector`
        """
        return _newV(self.__data * m._Matrix__data)

    def abs(self):
        u"""
        4次元ベクトルの各要素を絶対値にしたベクトルを得る。

        abs 組み込み関数を使用する場合と等価。

        :rtype: `Vector`
        """
        v = self.__data
        return _newV(_MP(abs(v[0]), abs(v[1]), abs(v[2]), abs(v[3])))

    def iabs(self):
        u"""
        4次元ベクトルの各要素を絶対値にする。

        :rtype: `Vector` (self)
        """
        v = self.__data
        v[0] = abs(v[0])
        v[1] = abs(v[1])
        v[2] = abs(v[2])
        v[3] = abs(v[3])
        return self

    def mul(self, v):
        u"""
        4次元ベクトルの各要素を乗算したベクトルを得る。

        :type v: `Vector`
        :param v: もう1方のベクトル。
        :rtype: `Vector`
        """
        a = self.__data
        b = v.__data
        return _newV(_MP(a[0] * b[0], a[1] * b[1], a[2] * b[2], a[3] * b[3]))

    def imul(self, v):
        u"""
        4次元ベクトルの各要素を乗算したベクトルをセットする。

        :type v: `Vector`
        :param v: もう1方のベクトル。
        :rtype: `Vector` (self)
        """
        a = self.__data
        b = v.__data
        a[0] *= b[0]
        a[1] *= b[1]
        a[2] *= b[2]
        a[3] *= b[3]
        return self

    def div(self, v, pre=AVOID_ZERO_DIV_PRECISION):
        u"""
        4次元ベクトルの各要素を除算したベクトルを得る。

        :type v: `Vector`
        :param v: 分母のベクトル。
        :param `float` pre: ゼロ除算を避ける為の許容誤差。
        :rtype: `Vector`
        """
        a = self.__data
        b = v.__data
        return _newV(_MP(
            a[0] / avoidZeroDiv(b[0], pre),
            a[1] / avoidZeroDiv(b[1], pre),
            a[2] / avoidZeroDiv(b[2], pre),
            a[3] / avoidZeroDiv(b[3], pre),
        ))

    def idiv(self, v, pre=AVOID_ZERO_DIV_PRECISION):
        u"""
        4次元ベクトルの各要素を除算したベクトルをセットする。

        :type v: `Vector`
        :param v: 分母のベクトル。
        :param `float` pre: ゼロ除算を避ける為の許容誤差。
        :rtype: `Vector` (self)
        """
        a = self.__data
        b = v.__data
        a[0] /= avoidZeroDiv(b[0], pre)
        a[1] /= avoidZeroDiv(b[1], pre)
        a[2] /= avoidZeroDiv(b[2], pre)
        a[3] /= avoidZeroDiv(b[3], pre)
        return self

    def orthogonal(self, vec):
        u"""
        指定ベクトルに直交化したベクトルを得る。

        :type vec: `Vector`
        :param vec: 軸ベクトル。
        :rtype: `Vector`
        """
        a = self.__data
        b = _MV(vec.__data).normalize()
        v = a - b * (a[0] * b[0] + a[1] * b[1] + a[2] * b[2])
        return _newV(_MP(v[0], v[1], v[2], a[3]))

    def orthogonalize(self, vec):
        u"""
        指定ベクトルに直交化したベクトルをセットする。

        :type vec: `Vector`
        :param vec: 軸ベクトル。
        :rtype: `Vector` (self)
        """
        a = self.__data
        b = _MV(vec.__data).normalize()
        a -= b * (a[0] * b[0] + a[1] * b[1] + a[2] * b[2])
        return self

    def maxAxis(self, noSign=False):
        u"""
        絶対値が最大の要素の軸IDを得る。

        :param `bool` noSign: 符号ビットを含まない軸ID (0～2) を得る。
        :rtype: `int`
        """
        dt = self.__data
        ax = abs(dt[0])
        ay = abs(dt[1])
        az = abs(dt[2])
        if ax > ay:
            if ax > az:
                return AXIS_X if (noSign or dt[0] >= 0.) else AXIS_NEG_X
        elif ay > az:
            return AXIS_Y if (noSign or dt[1] >= 0.) else AXIS_NEG_Y
        return AXIS_Z if (noSign or dt[2] >= 0.) else AXIS_NEG_Z

    def minAxis(self, noSign=False):
        u"""
        絶対値が最小の要素の軸IDを得る。

        :param `bool` noSign: 符号ビットを含まない軸ID (0～2) を得る。
        :rtype: `int`
        """
        dt = self.__data
        ax = abs(dt[0])
        ay = abs(dt[1])
        az = abs(dt[2])
        if ax < ay:
            if ax < az:
                return AXIS_X if (noSign or dt[0] >= 0.) else AXIS_NEG_X
        elif ay < az:
            return AXIS_Y if (noSign or dt[1] >= 0.) else AXIS_NEG_Y
        return AXIS_Z if (noSign or dt[2] >= 0.) else AXIS_NEG_Z

    def findNearestAxis(self, asId=False):
        u"""
        方向ベクトルに最も近い X,Y,Z,-X,-Y,-Z 軸方向を得る。

        殆どゼロベクトルで判定できない場合は None となる。

        :param `bool` asId: 結果をIDで得る。
        :rtype: `Vector`, `int` or None
        """
        dt = self.__data
        max_a = 0.
        axis = None
        for key in _XYZ_AXES:
            v = dt[key]
            a = abs(v)
            if a > max_a:
                max_a = a
                axis = key
                if v < 0.:
                    axis += AXIS_NEG
        return axis if asId else _AXIS_VECTOR_DICT.get(axis)

V = Vector  #: `Vector` の別名。

_MUTATOR_DICT[V] = (
    'set',
    'normalize',
    'normalizeIt',
    'cartesianize',
    'rationalize',
    'homogenize',
    'iabs',
    'imul',
    'idiv',
    'orthogonalize',
)
ImmutableVector = immutableType(V)  #: `Vector` の `immutable` ラッパー。


def _newV(data, cls=V):
    obj = _object_new(cls)
    _V_setdata(obj, data)
    return obj
_object_new = object.__new__

_V_setdata = V._Vector__data.__set__

V.Tolerance = _TOLERANCE  #: 同値とみなす許容誤差。

V.Zero4 = ImmutableVector(0., 0., 0., 0.)  #: 4次元ゼロベクトル。
V.Zero = ImmutableVector()  #: ゼロベクトル。
V.Origin = V.Zero  #: `Zero` と同じ。
V.One = ImmutableVector(1., 1., 1.)  #: 各要素が 1.0 のベクトル。
V.XAxis = ImmutableVector(1., 0., 0.)  #: X軸ベクトル。
V.YAxis = ImmutableVector(0., 1., 0.)  #: Y軸ベクトル。
V.ZAxis = ImmutableVector(0., 0., 1.)  #: Z軸ベクトル。
V.XNegAxis = ImmutableVector(-1., 0., 0.)  #: -X軸ベクトル。
V.YNegAxis = ImmutableVector(0., -1., 0.)  #: -Y軸ベクトル。
V.ZNegAxis = ImmutableVector(0., 0., -1.)  #: -Z軸ベクトル。

_AXIS_VECTOR_DICT = ImmutableDict({
    AXIS_X: V.XAxis,
    AXIS_Y: V.YAxis,
    AXIS_Z: V.ZAxis,
    AXIS_NEG_X: V.XNegAxis,
    AXIS_NEG_Y: V.YNegAxis,
    AXIS_NEG_Z: V.ZNegAxis,
})
V.AXIS_VECTOR_DICT = _AXIS_VECTOR_DICT  #: 軸 ID からベクトルを得る辞書。

