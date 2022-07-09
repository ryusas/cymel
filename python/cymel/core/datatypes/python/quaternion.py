# -*- coding: utf-8 -*-
u"""
クォータニオンクラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ...pyutils import boundAngle
from ...pyutils.immutables import OPTIONAL_MUTATOR_DICT as _MUTATOR_DICT
from .vector import V
import maya.api.OpenMaya as _api2
from math import sin, cos, tan, acos, atan2, sqrt

__all__ = ['Quaternion', 'Q', 'ImmutableQuaternion']

_MM = _api2.MMatrix
_MQ = _api2.MQuaternion
_MV = _api2.MVector
_MP = _api2.MPoint
_ME = _api2.MEulerRotation
_MX = _api2.MTransformationMatrix
_MQ_Identity = _MQ.kIdentity

_MV_X = _MV.kXaxisVector
_MV_Y = _MV.kYaxisVector
_MV_Z = _MV.kZaxisVector

_2_squadPt = _MQ.squadPt
_TOLERANCE = _MQ.kTolerance

_2PI = PI + PI


#------------------------------------------------------------------------------
class Quaternion(object):
    u"""
    クォータニオンクラス。

    コンストラクタでは以下の値を指定可能。

    - `Quaternion`
    - x, y, z, w
    - 4値のシーケンス
    - 回転軸 (`.Vector`), 角度
    - 角度, 回転軸 (`.Vector`)
    - `.EulerRotation`
    - `.Matrix`
    """
    __slots__ = ('__data',)
    __hash__ = None

    def __new__(cls, *args):
        n = len(args)
        if n == 1:
            v = args[0]
            #if hasattr(v, '_Quaternion__data'):
            #    return _newQ(_MQ(v.__data), cls)
            if hasattr(v, '_EulerRotation__data'):
                return _newQ(v._EulerRotation__data.asQuaternion(), cls)
            if hasattr(v, '_Matrix__data'):
                return _newQ(_MX(v._Matrix__data).rotation(True), cls)
        elif n >= 2:
            v0 = args[0]
            v1 = args[1]
            if hasattr(v0, '_Vector__data'):
                args = list(args)
                if hasattr(v1, '_Vector__data'):
                    # (Vetor, Vector, [t])
                    args[0] = _MV(v0._Vector__data)
                    args[1] = _MV(v1._Vector__data)
                else:
                    # (Axis, Angle)
                    args[1] = _MV(v0._Vector__data)
                    args[0] = v1
            elif hasattr(v1, '_Vector__data'):
                # (Angle, Axis)
                args = list(args)
                args[1] = _MV(v1._Vector__data)
        try:
            return _newQ(_MQ(*args), cls)
        except:
            raise ValueError(cls.__name__ + ' : not matching constructor found.')

    def __reduce__(self):
        return type(self), tuple(self.__data)

    def __repr__(self):
        return type(self).__name__ + str(self.__data)

    def __str__(self):
        return str(self.__data)

    def __len__(self):
        return 4

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
        return _newQ(-self.__data)

    def __add__(self, v):
        try:
            return _newQ(self.__data + v.__data)
        except:
            raise ValueError("%s + %r" % (type(self).__name__, v))

    def __iadd__(self, v):
        try:
            d = self.__data
            s = v.__data
            d[0] += s[0]
            d[1] += s[1]
            d[2] += s[2]
            d[3] += s[3]
        except:
            raise ValueError("%s += %r" % (type(self).__name__, v))
        return self

    def __sub__(self, v):
        try:
            return _newQ(self.__data - v.__data)
        except:
            raise ValueError("%s - %r" % (type(self).__name__, v))

    def __isub__(self, v):
        try:
            d = self.__data
            s = v.__data
            d[0] -= s[0]
            d[1] -= s[1]
            d[2] -= s[2]
            d[3] -= s[3]
        except:
            raise ValueError("%s -= %r" % (type(self).__name__, v))
        return self

    def __mul__(self, v):
        if isinstance(v, Number):
            return _newQ(v * self.__data)  # MQuaternion のスカラー倍は __rmul__ のみ。
        try:
            return _newQ(self.__data * v.__data)
        except:
            raise ValueError("%s * %r" % (type(self).__name__, v))

    def __imul__(self, v):
        if isinstance(v, Number):
            d = self.__data  # MQuaternion のスカラー倍は __rmul__ のみ。
            d[0] *= v
            d[1] *= v
            d[2] *= v
            d[3] *= v
        else:
            try:
                #self.__data *= v.__data
                self.__data.__imul__(v.__data)
            except:
                raise ValueError("%s *= %r" % (type(self).__name__, v))
        return self

    def __rmul__(self, v):
        try:
            return _newQ(v * self.__data)
        except:
            raise ValueError("%r * %s" % (v, type(self).__name__))

    def __truediv__(self, v):
        try:
            return _newQ((1. / v) * self.__data)
        except:
            raise ValueError("%s / %r" % (type(self).__name__, v))

    def __itruediv__(self, v):
        try:
            v = 1. / v
            d = self.__data
            d[0] *= v
            d[1] *= v
            d[2] *= v
            d[3] *= v
        except:
            raise ValueError("%s /= %r" % (type(self).__name__, v))
        return self

    def __rtruediv__(self, v):
        try:
            d = self.__data
            return _newQ(_MQ(v / d[0], v / d[1], v / d[2], v / d[3]))
        except:
            raise ValueError("%r / %s" % (v, type(self).__name__))

    if IS_PYTHON2:
        __div__ = __truediv__
        __idiv__ = __itruediv__
        __rdiv__ = __rtruediv__

    if MAYA_VERSION < (2015,):
        def isEquivalent(self, q, tol=_TOLERANCE):
            u"""
            ほぼ等価かどうか。符号反転は同じ回転姿勢を表すものとして等価とみなす。

            符号反転を等価とみなしたくない場合は
            `isSignedEquivalent` を利用すると良い。

            :type q: `Quaternion`
            :param q: 比較するクォータニオン。
            :param `float` tol: 許容誤差。
            :rtype: `bool`

            .. note::
                :mayaapi2:`MQuaternion` の isEquivalent では、
                2015 未満では符号反転は等価とみなされなかったが、
                2015 以降で等価とみなされるように変更された。

                cymel では現在の API の仕様に合わせ、
                どのバージョンでも一貫して等価とみなすようにしている。
            """
            try:
                if self.__data[3] * q.__data[3] < 0.:
                    return self.__data.isEquivalent(-q.__data, tol)
                else:
                    return self.__data.isEquivalent(q.__data, tol)
            except:
                return False

        def isSignedEquivalent(self, q, tol=_TOLERANCE):
            u"""
            ほぼ同値かどうか。符号反転は同値とみなさない。

            符号反転も等価とみなしたい場合は
            `isEquivalent` を利用すると良い。

            :type q: `Quaternion`
            :param q: 比較するクォータニオン。
            :param `float` tol: 許容誤差。
            :rtype: `bool`
            """
            try:
                return self.__data.isEquivalent(q.__data, tol)
            except:
                return False

        def isIdentity(self, tol=_TOLERANCE):
            u"""
            ほぼ単位クォータニオンかどうか。

            単位クォータニオンと `isSignedEquivalent` で比較することと等しい。

            :param `float` tol: 許容誤差。
            :rtype: `bool`
            """
            return self.__data.isEquivalent(_MQ_Identity, tol)

    else:
        def isEquivalent(self, q, tol=_TOLERANCE):
            u"""
            ほぼ等価かどうか。符号反転は同じ回転姿勢を表すものとして等価とみなす。

            符号反転を等価とみなしたくない場合は
            `isSignedEquivalent` を利用すると良い。

            :type q: `Quaternion`
            :param q: 比較するクォータニオン。
            :param `float` tol: 許容誤差。
            :rtype: `bool`

            .. note::
                :mayaapi2:`MQuaternion` の isEquivalent では、
                2015 未満では符号反転は等価とみなされなかったが、
                2015 以降で等価とみなされるように変更された。

                cymel では現在の API の仕様に合わせ、
                どのバージョンでも一貫して等価とみなすようにしている。
            """
            try:
                return self.__data.isEquivalent(q.__data, tol)
            except:
                return False

        def isSignedEquivalent(self, q, tol=_TOLERANCE):
            u"""
            ほぼ同値かどうか。符号反転は同値とみなさない。

            符号反転も等価とみなしたい場合は
            `isEquivalent` を利用すると良い。

            :type q: `Quaternion`
            :param q: 比較するクォータニオン。
            :param `float` tol: 許容誤差。
            :rtype: `bool`
            """
            try:
                q = self.__data - q.__data
                return abs(q[0]) < tol and abs(q[1]) < tol and abs(q[2]) < tol and abs(q[3]) < tol
            except:
                return False

        def isIdentity(self, tol=_TOLERANCE):
            u"""
            ほぼ単位クォータニオンかどうか。

            単位クォータニオンと `isSignedEquivalent` で比較することと等しい。

            :param `float` tol: 許容誤差。
            :rtype: `bool`
            """
            q = self.__data
            return abs(q[0]) < tol and abs(q[1]) < tol and abs(q[2]) < tol and abs(1. - q[3]) < tol

    def set(self, *args):
        u"""
        他の値をセットする。

        コンストラクタと同様に、以下の値を指定可能。

        - `Quaternion`
        - x, y, z, w
        - 4値までのシーケンス
        - 回転軸 (`.Vector`), 角度
        - 角度, 回転軸 (`.Vector`)
        - `.EulerRotation`
        - `.Matrix`

        :rtype: `Quaternion` (self)
        """
        v0 = args[0]
        n = len(args)
        if n == 1:
            if hasattr(v0, '_Quaternion__data'):
                self.__data.setValue(v0.__data)
                return self
            if hasattr(v0, '_EulerRotation__data'):
                self.__data.setValue(v0._EulerRotation__data)
                return self
            if hasattr(v0, '_Matrix__data'):
                _Q_setdata(self, _MX(v0._Matrix__data).rotation(True))
                return self
        elif n == 2:
            if hasattr(v0, '_Vector__data'):
                _Q_setdata(self, _MQ(args[1], _MV(v0)))
                return self
            v1 = args[1]
            if hasattr(v1, '_Vector__data'):
                _Q_setdata(self, _MQ(v0, _MV(v1)))
                return self
        try:
            for i, v in numerate(args):
                self.__data[i] = v
        except:
            raise ValueError(type(self).__name__ + '.set : unsupported arguments.')
        return self

    setValue = set

    def setToIdentity(self):
        u"""
        単位クォータニオンをセットする。

        :rtype: `self`
        """
        self.__data.setValue(_MQ_Identity)
        return self

    def setToXAxis(self, angle):
        u"""
        X軸回りの回転角度をセットする。

        :param `float` angle: 角度。
        :rtype: `Quaternion` (self)
        """
        self.__data.setToXAxis(angle)
        return self

    def setToYAxis(self, angle):
        u"""
        Y軸回りの回転角度をセットする。

        :param `float` angle: 角度。
        :rtype: `Quaternion` (self)
        """
        self.__data.setToYAxis(angle)
        return self

    def setToZAxis(self, angle):
        u"""
        Z軸回りの回転角度をセットする。

        :param `float` angle: 角度。
        :rtype: `Quaternion` (self)
        """
        self.__data.setToZAxis(angle)
        return self

    def asAxisAngle(self):
        u"""
        軸ベクトルと回転角度として得る。

        :rtype: `.Vector`, `float`
        """
        axis, angle = self.__data.asAxisAngle()
        return _newV(_MP(axis)), angle

    asAA = asAxisAngle  #: `asAxisAngle` の別名。

    def asEulerRotation(self, order=XYZ, correct=False):
        u"""
        オイラー角回転として得る。

        :param `int` order: 得たい回転オーダー。
        :param `bool` correct:
            得られるオイラー角回転値を再度クォータニオン化したときに
            元の符号と一致するように補正する。
            不適切な場合に `.EulerRotation.reverseDirection` することと等しい。
        :rtype: `.EulerRotation`

        .. note::
            `EulerRotation` の単位は弧度法なので、
            度数法で得たい場合は `asDegrees` を使用すると良い。

        .. warning::
            correct に真を指定して得た値を rotateAxis にセットしようとすると
            正常にセットできない場合があるので、その用途では指定すべきではない。
        """
        if order == XYZ:
            r = self.__data.asEulerRotation()
        else:
            r = _ME(0., 0., 0., order)
            r.setValue(self.__data)

        if correct:
            # クォータニオンの符号に忠実な回転に補正する。
            s = self.__data
            d = r.asQuaternion()
            if d[0] * s[0] + d[1] * s[1] + d[2] * s[2] + d[3] * s[3] < 0.:
                _reverseEulerRotationInPlace(r)

        return _newE(r)

    asE = asEulerRotation  #: `asEulerRotation` の別名。

    def asDegrees(self, order=XYZ, correct=False):
        u"""
        オイラー角回転を度数法の `list` として得る。

        :param `int` order: 得たい回転オーダー。
        :param `bool` correct:
            得られるオイラー角回転値を再度クォータニオン化したときに
            元の符号と一致するように補正する。
            不適切な場合に `.EulerRotation.reverseDirection` することと等しい。
        :rtype: `list`

        .. note::
            単位を弧度法で得たい場合は `asEulerRotation` を使用すると良い。

        .. warning::
            correct に真を指定して得た値を rotateAxis にセットしようとすると
            正常にセットできない場合があるので、その用途では指定すべきではない。
        """
        if order == XYZ:
            r = self.__data.asEulerRotation()
        else:
            r = _ME(0., 0., 0., order)
            r.setValue(self.__data)

        if correct:
            s = self.__data
            d = r.asQuaternion()
            if d[0] * s[0] + d[1] * s[1] + d[2] * s[2] + d[3] * s[3] < 0.:
                _reverseEulerRotationInPlace(r)

        return [r[0] * TO_DEG, r[1] * TO_DEG, r[2] * TO_DEG]

    asD = asDegrees  #: `asDegrees` の別名。

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
        return _newX(dict(q=_newQ(_MQ(self.__data), ImmutableQuaternion)))

    asX = asTransformation  #: `asTransformation` の別名。

    def asAngle(self, naxis=None, bound=False):
        u"""
        クォータニオンの持つ回転角度を得る。

        `asAxisAngle` では 0 になるような微小な角度も取得出来るが、
        その場合は `asAxisAngle` で得られる軸
        （おそらく 0 度扱いの場合は常に (0,0,1) となる）
        には対応しない。

        また、回転軸があらかじめ分かっている場合は
        指定した方が精度の良い値を得られる。

        :type naxis: `.Vector`
        :param naxis:
            回転軸が分かっている場合はそれを指定する。
            `asAxisAngle` で得られるベクトルと平行でなければならない。
            反転した軸も指定可能で、その場合、反転した角度が得られる。
        :param `bool` bound:
            ±π の範囲に収めた角度を得るかどうか。
        :rtype: `float`
        """
        if naxis:
            ax = abs(naxis[0])
            ay = abs(naxis[1])
            az = abs(naxis[2])
            if ax > ay:
                s = (self.__data[0] / naxis[0]) if ax > az else (self.__data[2] / naxis[2])
            else:
                s = (self.__data[1] / naxis[1]) if ay > az else (self.__data[2] / naxis[2])
            ang = atan2(s, self.__data[3]) * 2.
        else:
            ang = (acos(self.__data[3]) * 2.) if (-1. < self.__data[3] < 1.) else 0.
        if bound:
            if ang < -PI:
                ang += _2PI
            elif PI < ang:
                ang -= _2PI
        return ang

    def setAngle(self, theta, correctAxis=False):
        u"""
        クォータニオンの持つ回転角度を書き換える。

        :param `float` theta: 角度。
        :param `bool` correctAxis:
            現在の w が負
            （πより大きい回転角度を持っている）
            なら、軸を反転補正させた上での角度をセットする。
        :rtype: `Quaternion` (self)
        """
        data = self.__data
        w = data[3]
        if 1. - abs(w) >= _TOLERANCE:
            half = theta * .5
            w = min(1., max(-1., w))
            if correctAxis and w < 0.:
                w = -sin(half) / sqrt(1. - w * w)
            else:
                w = sin(half) / sqrt(1. - w * w)  # sin(acos(w))
            data[0] *= w
            data[1] *= w
            data[2] *= w
            data[3] = cos(half)
        return self

    def conjugate(self):
        u"""
        共役クォータニオンを得る。

        :rtype: `Quaternion`
        """
        return _newQ(self.__data.conjugate())

    def conjugateIt(self):
        u"""
        共役クォータニオンをセットする。

        :rtype: `Quaternion` (self)
        """
        self.__data.conjugateIt()
        return self

    def inverse(self):
        u"""
        逆クォータニオンを得る。

        :rtype: `Quaternion`
        """
        return _newQ(self.__data.inverse())

    def invertIt(self):
        u"""
        逆クォータニオンをセットする。

        :rtype: `Quaternion` (self)
        """
        self.__data.invertIt()
        return self

    def normal(self):
        u"""
        正規化クォータニオンを得る。

        :rtype: `Quaternion`
        """
        return _newQ(self.__data.normal())

    def normalize(self):
        u"""
        正規化クォータニオンをセットする。

        :rtype: `Quaternion` (self)
        """
        self.__data.normalizeIt()
        return self

    normalizeIt = normalize

    def negateIt(self):
        u"""
        符号反転クォータニオンをセットする。

        :rtype: `Quaternion` (self)
        """
        self.__data.negateIt()
        return self

    def log(self):
        u"""
        対数クォータニオンを得る。

        :rtype: `Quaternion`
        """
        return _newQ(self.__data.log())

    def exp(self):
        u"""
        対数クォータニオンからクォータニオンを得る。。

        :rtype: `Quaternion`
        """
        return _newQ(self.__data.exp())

    def dot(self, q):
        u"""
        クォータニオンの内積を得る。

        :type q: `Quaternion`
        :param q: もう一方のクォータニオン。
        :rtype: `float`
        """
        d = self.__data
        s = q.__data
        return d[0] * s[0] + d[1] * s[1] + d[2] * s[2] + d[3] * s[3]

    @staticmethod
    def slerp(p, q, t, spin=0):
        u"""
        クォータニオンを球面線形補間する。

        :type p: `Quaternion`
        :param p: 始点クォータニオン。
        :type q: `Quaternion`
        :param q: 終点クォータニオン。
        :param `float` t: 0.0～1.0の補間係数。範囲外も指定可。
        :param `int` spin:
            スピン値。
            デフォルトの0は正方向、-1は逆方向、
            さらに+1や-1すると余分に周回する。
        :rtype: `Quaternion`
        """
        p = p.__data
        q = q.__data
        dt = p[0] * q[0] + p[1] * q[1] + p[2] * q[2] + p[3] * q[3]
        if dt < 0.:
            dt = -dt
            flip = -1.
        else:
            flip = 1.

        if 1. - dt < _TOLERANCE:  # 限りなく同じ姿勢を表すもの同士の場合。
            # 符号反転を考慮して線形補間する（微妙な差もあるので、全要素が反転していない場合も有り得る）。
            return _newQ(((1. - t) * p + (t * flip) * q).normalizeIt())

        else:
            angle = acos(dt)
            s = 1. / sin(angle)  # 1. / sqrt(1. - dt * dt)
            t *= angle + spin * PI
            return _newQ((sin(angle - t) * s) * p + (sin(t) * s * flip) * q)

    def slerp0(self, t, spin=0):
        u"""
        単位クォータニオンと球面線形補間する。

        :param `float` t: 0.0～1.0の補間係数。範囲外も指定可。
        :param `int` spin:
            スピン値。
            デフォルトの0は正方向、-1は逆方向、
            さらに+1や-1すると余分に周回する。
        :rtype: `Quaternion`
        """
        q = self.__data
        dt = q[3]
        if dt < 0.:
            dt = -dt
            flip = -1.
        else:
            flip = 1.

        if 1. - dt < _TOLERANCE:  # 限りなく同じ姿勢を表すもの同士の場合。
            # 符号反転を考慮して線形補間する（微妙な差もあるので、全要素が反転していない場合も有り得る）。
            return _newQ(((1. - t) * _MQ_Identity + (t * flip) * q).normalizeIt())

        else:
            angle = acos(dt)
            s = 1. / sin(angle)  # 1. / sqrt(1. - dt * dt)
            t *= angle + spin * PI
            return _newQ((sin(angle - t) * s) * _MQ_Identity + (sin(t) * s * flip) * q)

    @staticmethod
    def squad(p, a, b, q, t, spin=0):
        u"""
        クォータニオンを球面曲線補間する。

        :type p: `Quaternion`
        :param p: 始点クォータニオン。
        :type a: `Quaternion`
        :param a: 始点側の制御点。
        :type b: `Quaternion`
        :param b: 終点側の制御点。
        :type q: `Quaternion`
        :param q: 終点クォータニオン。
        :param `float` t: 0.0～1.0の補間係数。範囲外も指定可。
        :param `int` spin:
            スピン値。
            デフォルトの0は正方向、-1は逆方向、
            さらに+1や-1すると余分に周回する。
        :rtype: `Quaternion`
        """
        return _slerp(_slerp(p, q, t), _slerp(a, b, t), 2. * (1. - t) * t, spin)

    @staticmethod
    def squadPt(q0, q1, q2):
        u"""
        `squad` 用の制御点を計算する。

        :type q0: `Quaternion`
        :param q0: 1つめのクォータニオン。
        :type q1: `Quaternion`
        :param q1: 2つめのクォータニオン。
        :type q2: `Quaternion`
        :param q2: 3つめのクォータニオン。
        :rtype: `Quaternion`
        """
        return _newQ(_2_squadPt(q0.__data, q1.__data, q2.__data))

    def asBend(self, reverse=False, aim=V.XAxis):
        u"""
        ボーン回転とした場合の曲げ成分を得る。

        :param `bool` reverse:
            曲げ・捻りの順番を反転するかどうか。
            デフォルトでは、階層上位から見て曲げてから捻るが、
            True を指定すると捻ってから曲げる分解になる。
        :type aim: `.Vector`
        :param aim: ボーン方向ベクトル。
        :rtype: `Quaternion`
        """
        aim = _MV(aim._Vector__data)
        if reverse:
            return _newQ(_MQ(aim.rotateBy(self.__data.conjugate()), aim))
        else:
            return _newQ(_MQ(aim, aim.rotateBy(self.__data)))

    def asRoll(self, aim=V.XAxis):
        u"""
        ボーン回転とした場合の捻り成分を得る。

        分解の考え方として、曲げてから捻っても、捻ってから曲げても、
        同じ値が得られるため `asBend` や `asRollBendHV` のような
        reverse オプションはない。

        :type aim: `.Vector`
        :param aim: ボーン方向ベクトル。
        :rtype: `Quaternion`
        """
        aim = _MV(aim._Vector__data)
        return _newQ(self.__data * _MQ(aim.rotateBy(self.__data), aim))

    def asRollBendHV(self, reverse=False, aim=V.XAxis, upv=V.YAxis):
        u"""
        ボーン回転とした場合の、捻り、横曲げ、縦曲げの3つの角度に分離する。

        :param `bool` reverse:
            曲げ・捻りの順番を反転するかどうか。
            デフォルトでは、階層上位から見て曲げてから捻るが、
            True を指定すると捻ってから曲げる分解になる。
        :type aim: `.Vector`
        :param aim: ボーン方向ベクトル。
        :type upv: `.Vector`
        :param upv: ボーンアップベクトル。
        :returns: [roll, bendH, bendV]
        """
        aim = _MV(aim._Vector__data).normalize()
        upv = _MV(upv._Vector__data)
        dep = (aim ^ upv).normalize()
        upv = (dep ^ aim).normalize()

        if reverse:
            q = self.__data.conjugate()
            sign = -1.
            f = -2.
        else:
            q = self.__data
            sign = 1.
            f = 2.

        vec = aim.rotateBy(q)
        rollQ = q * _MQ(vec, aim)

        #vec *= _MM([
        #    aim[0], aim[1], aim[2], 0.,
        #    upv[0], upv[1], upv[2], 0.,
        #    dep[0], dep[1], dep[2], 0.,
        #    0., 0., 0., 1.,
        #])

        if rollQ.w < 0.:
            rollQ = -rollQ
        ax = abs(aim[0])
        ay = abs(aim[1])
        az = abs(aim[2])
        if ax > ay:
            rs = (rollQ[0] / aim[0]) if ax > az else (rollQ[2] / aim[2])
        else:
            rs = (rollQ[1] / aim[1]) if ay > az else (rollQ[2] / aim[2])

        #b = vec.x + 1.
        #return [
        #    atan2(rs, rollQ[3]) * f,
        #    atan2(vec.z, b) * -f,
        #    atan2(vec.y, b) * f,
        #]
        b = (vec * aim) + 1.
        return [
            atan2(rs, rollQ[3]) * f,
            atan2(vec * dep, b) * -f,
            atan2(vec * upv, b) * f,
        ]

    asRHV = asRollBendHV  #: `asRollBendHV` の別名。

    def asRollBendHV2(self, axisOri=None, reverse=False):
        u"""
        ボーン回転とした場合の、捻り、横曲げ、縦曲げの3つの角度に分離する。

        :param axisOri:
            基準軸を回転（クォータニオン）で指定する。
            その空間のX軸がボーン方向、Y軸がアップ方向に相当する。
            デフォルトの None は単位クォータニオンと同じである。
        :param `bool` reverse:
            曲げ・捻りの順番を反転するかどうか。
            デフォルトでは、階層上位から見て曲げてから捻るが、
            True を指定すると捻ってから曲げる分解になる。
        :returns: [roll, bendH, bendV]
        """
        if axisOri:
            axisOri = axisOri.__data
            q = axisOri * self.__data
            q *= axisOri.conjugate()
        else:
            q = self.__data

        if reverse:
            q = q.conjugate()
            f = -2.
        else:
            f = 2.

        vec = _MV_X.rotateBy(q)
        rollQ = q * _MQ(vec, _MV_X)

        b = vec.x + 1.
        return [
            (atan2(-rollQ.x, -rollQ.w) if rollQ.w < 0. else atan2(rollQ.x, rollQ.w)) * f,
            atan2(vec.z, b) * -f,
            atan2(vec.y, b) * f,
        ]

    asRHV2 = asRollBendHV2  #: `asRollBendHV2` の別名。

    @classmethod
    def makeRollBendHV(cls, rhv, reverse=False, aim=V.XAxis, upv=V.YAxis):
        u"""
        ボーンの捻り、横曲げ、縦曲げの3つの角度からクォータニオンを合成する。

        :param rhv: [roll, bendH, bendV]
        :param `bool` reverse:
            曲げ・捻りの順番を反転するかどうか。
            デフォルトでは、階層上位から見て曲げてから捻るが、
            True を指定すると捻ってから曲げる合成になる。
        :type aim: `.Vector`
        :param aim: ボーン方向ベクトル。
        :type upv: `.Vector`
        :param upv: ボーンアップベクトル。
        :rtype: `Quaternion`
        """
        aim = _MV(aim._Vector__data).normalize()
        upv = _MV(upv._Vector__data)
        dep = (aim ^ upv).normalize()
        upv = (dep ^ aim).normalize()

        f = -.5 if reverse else .5
        r = rhv[0] * f
        vec = _MV(1., tan(rhv[2] * f), -tan(rhv[1] * f))

        saim = aim * sin(r)
        c = cos(r)
        vec *= 2. / (vec * vec)
        vec.x -= 1.
        #vec *= _MM([
        #    aim[0], aim[1], aim[2], 0.,
        #    upv[0], upv[1], upv[2], 0.,
        #    dep[0], dep[1], dep[2], 0.,
        #    0., 0., 0., 1.,
        #])
        vec = _MV(vec * aim, vec * upv, vec * dep)

        #if reverse:
        #    q = _MQ(vec, aim)
        #    q *= _MQ(saim[0], saim[1], saim[2], -c)  # こうすると -w になるので良くない。
        #else:
        q = _MQ(saim[0], saim[1], saim[2], c)
        q *= _MQ(aim, vec)
        if reverse:
            q.conjugateIt()

        return _newQ(q, cls)

    makeRHV = makeRollBendHV  #: `makeRollBendHV` の別名。

    @classmethod
    def makeRollBendHV2(cls, rhv, axisOri=None, reverse=False):
        u"""
        ボーンの捻り、横曲げ、縦曲げの3つの角度からクォータニオンを合成する。

        :param rhv: [roll, bendH, bendV]
        :param axisOri:
            基準軸を回転（クォータニオン）で指定する。
            その空間のX軸がボーン方向、Y軸がアップ方向に相当する。
            デフォルトの None は単位クォータニオンと同じである。
        :param `bool` reverse:
            曲げ・捻りの順番を反転するかどうか。
            デフォルトでは、階層上位から見て曲げてから捻るが、
            True を指定すると捻ってから曲げる合成になる。
        :rtype: `Quaternion`
        """
        f = -.5 if reverse else .5
        r = rhv[0] * f
        vec = _MV(1., tan(rhv[2] * f), -tan(rhv[1] * f))

        s = sin(r)
        c = cos(r)
        vec *= 2. / (vec * vec)
        vec.x -= 1.

        #if reverse:
        #    q = _MQ(vec, _MV_X)
        #    q *= _MQ(s, 0., 0., -c)  # こうすると -w になるので良くない。
        #else:
        q = _MQ(s, 0., 0., c)
        q *= _MQ(_MV_X, vec)
        if reverse:
            q.conjugateIt()

        if axisOri:
            axisOri = axisOri.__data
            q = axisOri.conjugate() * q
            q *= axisOri

        return _newQ(q, cls)

    makeRHV2 = makeRollBendHV2  #: `makeRollBendHV2` の別名。

Q = Quaternion  #: `Quaternion` の別名。

_MUTATOR_DICT[Q] = (
    'set',
    'setValue',
    'setToIdentity',
    'setToXAxis',
    'setToYAxis',
    'setToZAxis',
    'setAngle',
    'conjugateIt',
    'invertIt',
    'normalize',
    'normalizeIt',
    'negateIt',
)
ImmutableQuaternion = immutableType(Q)  #: `Quaternion` の `immutable` ラッパー。


def _newQ(data, cls=Q):
    obj = _object_new(cls)
    _Q_setdata(obj, data)
    return obj
_object_new = object.__new__

_Q_setdata = Q._Quaternion__data.__set__

Q.Tolerance = _TOLERANCE  #: 同値とみなす許容誤差。
Q.Identity = ImmutableQuaternion()  #: 単位クォータニオン。
Q.Zero = ImmutableQuaternion(0., 0., 0., 0.)  #: ゼロ。

_slerp = Q.slerp

