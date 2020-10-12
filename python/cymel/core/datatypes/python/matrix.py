# -*- coding: utf-8 -*-
u"""
4x4 マトリックスクラス。
"""
from ...common import *
import maya.api.OpenMaya as _api2

__all__ = ['Matrix', 'M']

_MM = _api2.MMatrix
_MQ = _api2.MQuaternion
_ME = _api2.MEulerRotation
_MP = _api2.MPoint
_MV = _api2.MVector
_MX = _api2.MTransformationMatrix
_MSpace_kTransform = _api2.MSpace.kTransform
_MV_Zero = _MV.kZeroVector
_MQ_Identity = _MQ.kIdentity

_TOLERANCE = _MM.kTolerance


#------------------------------------------------------------------------------
class Matrix(object):
    u"""
    4x4 マトリックスクラス。

    コンストラクタでは以下の値を指定可能。

    - `Matrix`
    - 16値のシーケンス
    """
    __slots__ = ('__data',)
    __hash__ = None

    def __new__(cls, *args):
        return _newM(_MM(*args), cls)

    def __reduce__(self):
        return type(self), (tuple(self.__data),)

    def __repr__(self):
        return type(self).__name__ + str(self.__data)

    def __str__(self):
        return str(self.__data)

    def __len__(self):
        return 16

    def __getitem__(self, i):
        return self.__data[i]

    u'''
    def __contains__(self, v):
        return v in self.__data

    def __iter__(self):
        d = self.__data
        for i in _RANGE16:
            yield d[i]

    def __reversed__(self):
        d = self.__data
        for i in _REVERSED_RANGE16:
            yield d[i]

    def index(self, v):
        d = self.__data
        for i in _RANGE16:
            if d[i] == v:
                return i
        raise ValueError(repr(v) + ' is not in matrix')

    def count(self, v):
        c = 0
        for x in self.__data:
            if x == v:
                c += 1
        return c
    '''

    def __setitem__(self, i, v):
        # Fix DoubleAccessorBug
        vals = [
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            0., 0., 0., 0.,
        ]
        vals[i] = v - self[i]
        self.__data += _MM(vals)

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
        return _newM(self.__data.__mul__(-1.))

    def __add__(self, v):
        try:
            return _newM(self.__data.__add__(v.__data))
        except:
            raise ValueError("%s + %r" % (type(self).__name__, v))

    def __sub__(self, v):
        try:
            return _newM(self.__data.__sub__(v.__data))
        except:
            raise ValueError("%s - %r" % (type(self).__name__, v))

    def __mul__(self, v):
        if isinstance(v, Number):
            return _newM(self.__data.__mul__(v))
        elif hasattr(v, '_Transformation__data'):
            v = v._Transformation__copy()
            v.m = self * v.m
            return v
        try:
            return _newM(self.__data.__mul__(v.__data))
        except:
            raise ValueError("%s * %r" % (type(self).__name__, v))

    def __rmul__(self, v):
        try:
            return _newM(self.__data.__rmul__(v))
        except:
            raise ValueError("%r * %s" % (v, type(self).__name__))

    def __div__(self, v):
        try:
            return _newM(self.__data.__mul__(1. / v))
        except:
            raise ValueError("%s / %r" % (type(self).__name__, v))

    def __rdiv__(self, v):
        try:
            return _newM(_MM([v / x for x in self]))
        except:
            raise ValueError("%r / %s" % (v, type(self).__name__))

    def isEquivalent(self, m, tol=_TOLERANCE):
        u"""
        ほぼ同値かどうか。

        :type m: `Matrix`
        :param m: 比較するマトリックス。
        :param `float` tol: 許容誤差。
        :rtype: `bool`
        """
        try:
            return self.__data.isEquivalent(m.__data, tol)
        except:
            return False

    def isSingular(self):
        u"""
        特異行列かどうか。

        :rtype: `bool`
        """
        return self.__data.isSingular()

    def set(self, v):
        u"""
        他の値をセットする。

        コンストラクタと同様に、以下の値を指定可能。

        - `Matrix`
        - 16値のシーケンス

        :rtype: `Matrix` (self)
        """
        # Fix DoubleAccessorBug
        self.__data += _MM([s - d for s, d in zip(v, self.__data)])
        return self

    def getelem(self, row, col):
        u"""
        指定位置の要素を得る。

        :param `int` row: 行インデックス (0-3)
        :param `int` col: 列インデックス (0-3)
        :rtype: `float`
        """
        return self[row * 4 + col]

    def setelem(self, row, col, val):
        u"""
        指定位置の要素をセットする。

        :param `int` row: 行を 0 ～ 3 で指定。
        :param `int` col: 列を 0 ～ 3 で指定。
        :param `float` val: セットする値。
        """
        self[row * 4 + col] = val

    def asTransformation(self):
        u"""
        トランスフォーメーションとして得る。

        :rtype: `.Transformation`
        """
        return _newX(dict(m=_newM(_MM(self.__data))))

    asX = asTransformation  #: `asTransformation` の別名。

    def asQuaternion(self):
        u"""
        クォータニオンを得る。

        :rtype: `.Quaternion`
        """
        #return _newQ(_MX(self.__data).rotation(True))
        # MQuaternion の場合 MTransformationMatrix より直接の方が速い。
        return _newQ(_MQ().setValue(self.__data.homogenize()))

    asQ = asQuaternion  #: `asQuaternion` の別名。

    def asEulerRotation(self, order=XYZ):
        u"""
        オイラー角回転を得る。

        :param `int` order: 得たい回転オーダー。
        :rtype: `.EulerRotation`

        .. note::
            `EulerRotation` の単位は弧度法なので、
            度数法で得たい場合は `asDegrees` を使用すると良い。
        """
        #return _newE(_ME(0., 0., 0., order).setValue(self.__data.homogenize()))
        # MEulerRotation の場合 MTransformationMatrix の方が直接よりやや速い。
        if order is XYZ:
            return _newE(_MX(self.__data).rotation(False))
        else:
            return _newE(_MX(self.__data).reorderRotation(order + 1).rotation(False))

    asE = asEulerRotation  #: `asEulerRotation` の別名。

    def asDegrees(self, order=XYZ):
        u"""
        オイラー角回転を度数法の `list` として得る。

        :param `int` order: 得たい回転オーダー。
        :rtype: `list`

        .. note::
            単位を弧度法で得たい場合は `asEulerRotation` を使用すると良い。
        """
        if order is XYZ:
            e = _MX(self.__data).rotation(False)
        else:
            e = _MX(self.__data).reorderRotation(order + 1).rotation(False)
        return [e[0] * TO_DEG, e[1] * TO_DEG, e[2] * TO_DEG]

    asD = asDegrees  #: `asDegrees` の別名。

    def asTranslation(self):
        u"""
        平行移動成分を得る。

        :rtype: `.Vector`
        """
        return _newV(_MP(self.__data[12], self.__data[13], self.__data[14]))

    asT = asTranslation  #: `asTranslation` の別名。

    def asScaling(self):
        u"""
        スケール成分を得る。

        :rtype: `.Vector`
        """
        return _newV(_MP(_MX(self.__data).scale(_MSpace_kTransform)))

    asS = asScaling  #: `asScaling` の別名。

    def asShearing(self):
        u"""
        せん断成分を得る。

        :rtype: `.Vector`
        """
        return _newV(_MP(_MX(self.__data).shear(_MSpace_kTransform)))

    asSh = asShearing  #: `asShearing` の別名。

    def asTranslationMatrix(self):
        u"""
        平行移動のみの行列を得る。

        :rtype: `Matrix`
        """
        return _newM(_MM([
            1., 0., 0., 0.,
            0., 1., 0., 0.,
            0., 0., 1., 0.,
            self.__data[12], self.__data[13], self.__data[14], 1.,
        ]))

    asTM = asTranslationMatrix  #: `asTranslationMatrix` の別名。

    def asRotationMatrix(self):
        u"""
        回転のみの行列を得る。

        :rtype: `Matrix`
        """
        m = self.__data.homogenize()
        return _newM(_MM([
            m[0], m[1], m[2], 0.,
            m[4], m[5], m[6], 0.,
            m[8], m[9], m[10], 0.,
            0., 0., 0., 1.,
        ]))

    asRM = asRotationMatrix  #: `asRotationMatrix` の別名。

    def asScalingMatrix(self):
        u"""
        スケーリング成分(scale+shear)のみの行列を得る。

        :rtype: `Matrix`:
        """
        xm = _MX(self.__data)
        xm.setTranslation(_MV_Zero, _MSpace_kTransform)
        xm.setRotation(_MQ_Identity)
        return _newM(xm.asMatrix())

    asSM = asScalingMatrix  #: `asScalingMatrix` の別名。

    def as3x3(self):
        u"""
        3x3部分以外を初期化した行列を得る。

        :rtype: `Matrix`
        """
        m = self.__data
        return _newM(_MM([
            m[0], m[1], m[2], 0.,
            m[4], m[5], m[6], 0.,
            m[8], m[9], m[10], 0.,
            0., 0., 0., 1.,
        ]))

    def asTransposed3x3(self):
        u"""
        3x3部分は転置、それ以外の部分は初期化した行列を得る。

        :rtype: `Matrix`
        """
        m = self.__data
        return _newM(_MM([
            m[0], m[4], m[8], 0.,
            m[1], m[5], m[9], 0.,
            m[2], m[6], m[10], 0.,
            0., 0., 0., 1.,
        ]))

    def transpose(self):
        u"""
        転置行列を得る。

        :rtype: `Matrix`
        """
        return _newM(self.__data.transpose())

    def transposeIt(self):
        u"""
        転置行列をセットする。

        :rtype: `Matrix` (self)
        """
        _M_setdata(self, self.__data.transpose())
        return self

    def inverse(self):
        u"""
        逆行列を得る。

        :rtype: `Matrix`
        """
        return _newM(self.__data.inverse())

    def invertIt(self):
        u"""
        逆行列をセットする。

        :rtype: `Matrix` (self)
        """
        _M_setdata(self, self.__data.inverse())
        return self

    def adjoint(self):
        u"""
        余因子行列を得る。

        :rtype: `Matrix`
        """
        return _newM(self.__data.adjoint())

    def adjointIt(self):
        u"""
        余因子行列をセットする。

        :rtype: `Matrix` (self)
        """
        _M_setdata(self, self.__data.adjoint())
        return self

    def homogenize(self):
        u"""
        3x3部分を正規直交化した行列を得る。

        :rtype: `Matrix`
        """
        return _newM(self.__data.homogenize())

    def homogenizeIt(self):
        u"""
        3x3部分を正規直交化した行列をセットする。

        :rtype: `Matrix` (self)
        """
        _M_setdata(self, self.__data.homogenize())
        return self

    def det4x4(self):
        u"""
        行列式を得る。

        :rtype: `float`
        """
        return self.__data.det4x4()

    def det3x3(self):
        u"""
        3x3部分の行列式を得る。

        :rtype: `float`
        """
        return self.__data.det3x3()

    def row(self, i):
        u"""
        行ベクトルを得る。

        :param `int` i: 行インデックス（0～3）。
        :rtype: `.Vector`
        """
        d = self.__data
        i *= 4
        return _newV(_MP(d[i], d[i + 1], d[i + 2], d[i + 3]))

    def rows(self):
        u"""
        行ベクトルを4つ全て得る。

        :rtype: `tuple`
        """
        d = self.__data
        return (
            _newV(_MP(d[0], d[1], d[2], d[3])),
            _newV(_MP(d[4], d[5], d[6], d[7])),
            _newV(_MP(d[8], d[9], d[10], d[11])),
            _newV(_MP(d[12], d[13], d[14], d[15])),
        )

    def column(self, i):
        u"""
        列ベクトルを得る。

        :param `int` i: 列インデックス（0～3）。
        :rtype: `.Vector`
        """
        d = self.__data
        return _newV(_MP(d[i], d[i + 4], d[i + 8], d[i + 12]))

    def columns(self):
        u"""
        列ベクトルを4つ全て得る。

        :rtype: `tuple`
        """
        d = self.__data
        return (
            _newV(_MP(d[0], d[4], d[8], d[12])),
            _newV(_MP(d[1], d[5], d[9], d[13])),
            _newV(_MP(d[2], d[6], d[10], d[14])),
            _newV(_MP(d[3], d[7], d[11], d[15])),
        )

    def axis(self, i, transpose=False):
        u"""
        3x3部分の行や列を軸ベクトルとして得る。

        `.Vector` の w は 1.0 となる。

        :param `int` i: 軸指定(0=X, 1=Y, 2=Z)。
        :param `bool` transpose:
            転置行列の軸ベクトルを得る。
            言い換えると False では行ベクトルを
            True では列ベクトルを得ることになる。
        :rtype: `.Vector`
        """
        if transpose:
            return _newV(_MP(self.__data[i], self.__data[i + 4], self.__data[i + 8]))
        i *= 4
        return _newV(_MP(self.__data[i], self.__data[i + 1], self.__data[i + 2]))

    def axes(self, transpose=False):
        u"""
        3x3部分の行や列の軸ベクトルを3つ得る。

        各 `.Vector` の w は 1.0 となる。

        :param `bool` transpose:
            転置行列の軸ベクトルを得る。
            言い換えると False では行ベクトルを
            True では列ベクトルを得ることになる。
        :rtype: `tuple`
        """
        m = self.__data
        if transpose:
            return (
                _newV(_MP(m[0], m[4], m[8])),
                _newV(_MP(m[1], m[5], m[9])),
                _newV(_MP(m[2], m[6], m[10])),
            )
        return (
            _newV(_MP(m[0], m[1], m[2])),
            _newV(_MP(m[4], m[5], m[6])),
            _newV(_MP(m[8], m[9], m[10])),
        )

    def hasNonUniformScaling(self, tol=_TOLERANCE):
        u"""
        非一様スケーリングが含まれているかどうか。

        :param `float` tol: 許容誤差。
        :rtype: `bool`
        """
        xm = _MX(self.__data)
        v = xm.shear(_MSpace_kTransform)
        if abs(v[0]) > tol or abs(v[1]) > tol or abs(v[2]) > tol:
            return True
        v = xm.scale(_MSpace_kTransform)
        return abs(v[0] - v[1]) > tol or abs(v[0] - v[2]) > tol

    def setT(self, v):
        u"""
        平行移動値をセットする。

        :param v: 平行移動ベクトル。
        """
        # Fix DoubleAccessorBug
        self.__data += _MM((
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            v[0] - self.__data[12], v[1] - self.__data[13], v[2] - self.__data[14], 0.,
        ))

    def addT(self, v):
        u"""
        平行移動値を加算する。

        :param v: 平行移動ベクトル。
        """
        # Fix DoubleAccessorBug
        self.__data += _MM((
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            v[0], v[1], v[2], 0.,
        ))

    def subT(self, v):
        u"""
        平行移動値を減算する。

        :param v: 平行移動ベクトル。
        """
        # Fix DoubleAccessorBug
        self.__data -= _MM((
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            0., 0., 0., 0.,
            v[0], v[1], v[2], 0.,
        ))

    @classmethod
    def makeT(cls, v):
        u"""
        平行移動行列を作成する。

        :param v: translate値 (x, y, z)
        :rtype: `Matrix`
        """
        return cls([
            1., 0., 0., 0.,
            0., 1., 0., 0.,
            0., 0., 1., 0.,
            v[0], v[1], v[2], 1.,
        ])

    @classmethod
    def makeInvT(cls, v):
        u"""
        平行移動の逆行列を作成する。

        :param v: translate値 (x, y, z)
        :rtype: `Matrix`
        """
        return cls([
            1., 0., 0., 0.,
            0., 1., 0., 0.,
            0., 0., 1., 0.,
            -v[0], -v[1], -v[2], 1.,
        ])

    @classmethod
    def makeS(cls, v):
        u"""
        スケール行列を作成する。

        :param v: scale値 (x, y, z)
        :rtype: `Matrix`
        """
        return cls([
            v[0], 0., 0., 0.,
            0., v[1], 0., 0.,
            0., 0., v[2], 0.,
            0., 0., 0., 1.,
        ])

    @classmethod
    def makeInvS(cls, v, pre=AVOID_ZERO_DIV_PRECISION):
        u"""
        スケールの逆行列を作成する。

        :param v: scale値 (x, y, z)
        :param `float` pre: ゼロ除算を避ける為の許容誤差。
        :rtype: `Matrix`
        """
        return cls([
            1. / avoidZeroDiv(v[0], pre), 0., 0., 0.,
            0., 1. / avoidZeroDiv(v[1], pre), 0., 0.,
            0., 0., 1. / avoidZeroDiv(v[2], pre), 0.,
            0., 0., 0., 1.,
        ])

    @classmethod
    def makeSh(cls, v):
        u"""
        せん断行列を作成する。

        :param v: Shear値 (xy, yz, yx)
        :rtype: `Matrix`
        """
        return cls([
            1., 0., 0., 0.,
            v[0], 1., 0., 0.,
            v[1], v[2], 1., 0.,
            0., 0., 0., 1.,
        ])

    @classmethod
    def makeInvSh(cls, v):
        u"""
        せん断の逆行列を作成する。

        :param v: Shear値 (xy, yz, yx)
        :rtype: `Matrix`
        """
        return cls([
            1., 0., 0., 0.,
            -v[0], 1., 0., 0.,
            v[0] * v[2] - v[1], -v[2], 1., 0.,
            0., 0., 0., 1.,
        ])

M = Matrix  #: `Matrix` の別名。


def _newM(data, cls=M):
    obj = _object_new(cls)
    _M_setdata(obj, data)
    return obj
_object_new = object.__new__

_M_setdata = M._Matrix__data.__set__

M.Tolerance = _TOLERANCE  #: 同値とみなす許容誤差。

M.Identity = immutable(M())  #: 単位行列。
M.Zero = immutable(M([0] * 16))  #: ゼロ。

