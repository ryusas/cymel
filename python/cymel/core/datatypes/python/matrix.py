# -*- coding: utf-8 -*-
u"""
4x4 マトリックスクラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ...pyutils.immutables import OPTIONAL_MUTATOR_DICT as _MUTATOR_DICT
from .vector import V
import maya.api.OpenMaya as _api2

__all__ = ['Matrix', 'M', 'ImmutableMatrix']

_MM = _api2.MMatrix
_MQ = _api2.MQuaternion
_ME = _api2.MEulerRotation
_MP = _api2.MPoint
_MV = _api2.MVector
_MX = _api2.MTransformationMatrix
_MSpace_kTransform = _api2.MSpace.kTransform
_MV_Zero = _MV.kZeroVector
_MQ_Identity = _MQ.kIdentity
_MM_Identity = _MM.kIdentity

_TOLERANCE = _MM.kTolerance

_ZERO3 = (0., 0., 0.)


#------------------------------------------------------------------------------
class Matrix(object):
    u"""
    4x4 マトリックスクラス。

    コンストラクタでは以下の値を指定可能。

    * `Matrix`
    * 16値のシーケンス

    * 3つの `.Vector` による 3x3 部分の行ベクトル指定。

      - 追加で4つめの `.Vector` で translate 値の指定。
      - transpose=True オプションの指定で 3x3 部分の転置。
    """
    __slots__ = ('__data',)
    __hash__ = None

    def __new__(cls, *args, **kwargs):
        n = len(args)
        if n >= 3:
            vx = args[0]._Vector__data
            vy = args[1]._Vector__data
            vz = args[2]._Vector__data
            vt = args[3]._Vector__data if n >= 4 else _ZERO3
            if kwargs.get('transpose'):
                return _newM(_MM([
                    vx[0], vy[0], vz[0], 0.,
                    vx[1], vy[1], vz[1], 0.,
                    vx[2], vy[2], vz[2], 0.,
                    vt[0], vt[1], vt[2], 1.,
                ]), cls)
            else:
                return _newM(_MM([
                    vx[0], vx[1], vx[2], 0.,
                    vy[0], vy[1], vy[2], 0.,
                    vz[0], vz[1], vz[2], 0.,
                    vt[0], vt[1], vt[2], 1.,
                ]), cls)
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
        return _newM(self.__data * -1.)

    def __add__(self, v):
        try:
            return _newM(self.__data + v.__data)
        except:
            raise ValueError("%s + %r" % (type(self).__name__, v))

    def __iadd__(self, v):
        try:
            self.__data += v.__data
        except:
            raise ValueError("%s += %r" % (type(self).__name__, v))
        return self

    def __sub__(self, v):
        try:
            return _newM(self.__data - v.__data)
        except:
            raise ValueError("%s - %r" % (type(self).__name__, v))

    def __isub__(self, v):
        try:
            self.__data -= v.__data
        except:
            raise ValueError("%s -= %r" % (type(self).__name__, v))
        return self

    def __mul__(self, v):
        if isinstance(v, Number):
            return _newM(self.__data * v)
        elif hasattr(v, '_Transformation__data'):
            return _newM(self.__data * v.m.__data)
        else:
            try:
                return _newM(self.__data * v.__data)
            except:
                raise ValueError("%s * %r" % (type(self).__name__, v))

    def __imul__(self, v):
        if isinstance(v, Number):
            self.__data *= v
        elif hasattr(v, '_Transformation__data'):
            self.__data *= v.m.__data
        else:
            try:
                self.__data *= v.__data
            except:
                raise ValueError("%s *= %r" % (type(self).__name__, v))
        return self

    def __rmul__(self, v):
        try:
            return _newM(self.__data.__rmul__(v))
        except:
            raise ValueError("%r * %s" % (v, type(self).__name__))

    def __truediv__(self, v):
        try:
            return _newM(self.__data * (1. / v))
        except:
            raise ValueError("%s / %r" % (type(self).__name__, v))

    def __itruediv__(self, v):
        try:
            self.__data *= (1. / v)
        except:
            raise ValueError("%s /= %r" % (type(self).__name__, v))
        return self

    def __rtruediv__(self, v):
        try:
            return _newM(_MM([v / x for x in self]))
        except:
            raise ValueError("%r / %s" % (v, type(self).__name__))

    if IS_PYTHON2:
        __div__ = __truediv__
        __idiv__ = __itruediv__
        __rdiv__ = __rtruediv__

    #--------------------------------------------------
    # Fix DoubleAccessorBug
    if MAYA_VERSION < (2023,):
        def __setitem__(self, i, v):
            # 非公開なのでこのように済ませても良いが、若干遅い。
            #vals = list(self.__data)
            #vals[i] = v
            #self.__data = _MM(vals)

            vals = [
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
            ]
            ### NOTE: 基本的に全体の加算によって対策するが、少し大きめの値が入っていると事前にセロ初期化する必要がある。
            ###vals[i] = v - self[i]  # 事前に 10 などの大きめの値が入っていると、これではダメ。
            vals[i] = v
            self.__data[i] = 0.
            self.__data += _MM(vals)

        def set(self, v):
            u"""
            他の値をセットする。

            コンストラクタと同様に、以下の値を指定可能。

            - `Matrix`
            - 16値のシーケンス

            :rtype: `Matrix` (self)
            """
            # 非公開なのでこのように済ませても良いが、若干遅い。
            #try:
            #    self.__data = _MM(v.__data)  # ケースを分けた方が速い。
            #except:
            #    self.__data = _MM(v)

            self.__data -= self.__data
            try:
                self.__data += v.__data  # ケースを分けた方が速い。
            except:
                self.__data += _MM(v)
            return self

        def setRow(self, i, v):
            u"""
            行ベクトルをセットする。

            :param `int` i: 行インデックス（0～3）。
            :type v: `.Vector`
            :param v: セットする4次元ベクトル。
            """
            vals = [
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
            ]
            i *= 4

            # 非公開なのでこのように済ませても良いが、さして変わらない。
            #vals[i] = v[0]
            #vals[i + 1] = v[1]
            #vals[i + 2] = v[2]
            #vals[i + 3] = v[3]
            #self.__data = _MM(vals)

            self.__data[i] = 0.
            vals[i] = v[0]
            i += 1
            self.__data[i] = 0.
            vals[i] = v[1]
            i += 1
            self.__data[i] = 0.
            vals[i] = v[2]
            i += 1
            self.__data[i] = 0.
            vals[i] = v[3]
            self.__data += _MM(vals)

        def setRows(self, v0, v1, v2, v3):
            u"""
            行ベクトルを4つ全てセットする。

            :type v0: `.Vector`
            :param v0: 1行目の4次元ベクトル。
            :type v1: `.Vector`
            :param v1: 2行目の4次元ベクトル。
            :type v2: `.Vector`
            :param v2: 3行目の4次元ベクトル。
            :type v3: `.Vector`
            :param v3: 4行目の4次元ベクトル。
            """
            # 非公開なので丸ごと置き換えで済ませても良いが、さして変わらない。負荷の殆どは __new__ のようだ。
            self.__data -= self.__data
            self.__data += _MM([
                v0[0], v0[1], v0[2], v0[3],
                v1[0], v1[1], v1[2], v1[3],
                v2[0], v2[1], v2[2], v2[3],
                v3[0], v3[1], v3[2], v3[3],
            ])

        def setColumn(self, i, v):
            u"""
            列ベクトルをセットする。

            :param `int` i: 列インデックス（0～3）。
            :type v: `.Vector`
            :param v: セットする4次元ベクトル。
            """
            vals = [
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
            ]
            self.__data[i] = 0.
            vals[i] = v[0]
            i += 4
            self.__data[i] = 0.
            vals[i] = v[1]
            i += 4
            self.__data[i] = 0.
            vals[i] = v[2]
            i += 4
            self.__data[i] = 0.
            vals[i] = v[3]
            self.__data += _MM(vals)

        def setColumns(self, v0, v1, v2, v3):
            u"""
            列ベクトルを4つ全てセットする。

            :type v0: `.Vector`
            :param v0: 1列目の4次元ベクトル。
            :type v1: `.Vector`
            :param v1: 2列目の4次元ベクトル。
            :type v2: `.Vector`
            :param v2: 3列目の4次元ベクトル。
            :type v3: `.Vector`
            :param v3: 4列目の4次元ベクトル。
            """
            self.__data -= self.__data
            self.__data += _MM([
                v0[0], v1[0], v2[0], v3[0],
                v0[1], v1[1], v2[1], v3[1],
                v0[2], v1[2], v2[2], v3[2],
                v0[3], v1[3], v2[3], v3[3],
            ])

        def setAxis(self, i, v, transpose=False):
            u"""
            3x3部分の行や列のベクトルをセットする。

            :param `int` i: 軸指定(0=X, 1=Y, 2=Z)。
            :type v: `.Vector`
            :param v:
                セットする軸ベクトル。
            :param `bool` transpose:
                転置行列の軸ベクトルをセットする。
                言い換えると False では行ベクトルを
                True では列ベクトルをセットすることになる。
            """
            vals = [
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
            ]
            if transpose:
                self.__data[i] = 0.
                vals[i] = v[0]
                i += 4
                self.__data[i] = 0.
                vals[i] = v[1]
                i += 4
                self.__data[i] = 0.
                vals[i] = v[2]
            else:
                i *= 4
                self.__data[i] = 0.
                vals[i] = v[0]
                i += 1
                self.__data[i] = 0.
                vals[i] = v[1]
                i += 1
                self.__data[i] = 0.
                vals[i] = v[2]
            self.__data += _MM(vals)

        def setAxes(self, vx, vy, vz, vt=V.Zero, transpose=False):
            u"""
            3x3部分の行や列と4行目の平行移動ベクトルをセットする。

            :type vx: `.Vector`
            :param vx: セットするX軸ベクトル。
            :type vy: `.Vector`
            :param vy: セットするY軸ベクトル。
            :type vz: `.Vector`
            :param vz: セットするZ軸ベクトル。
            :type vt: `.Vector`
            :param vt:
                セットする平行移動ベクトル。
                これだけは transpose オプションの影響を受けない。
            :param `bool` transpose:
                3x3部分には転置行列の軸ベクトルをセットする。
                言い換えると False では行ベクトルを
                True では列ベクトルをセットすることになる。
            """
            if transpose:
                m = _MM([
                    vx[0], vy[0], vz[0], 0.,
                    vx[1], vy[1], vz[1], 0.,
                    vx[2], vy[2], vz[2], 0.,
                    vt[0], vt[1], vt[2], 1.,
                ])
            else:
                m = _MM([
                    vx[0], vx[1], vx[2], 0.,
                    vy[0], vy[1], vy[2], 0.,
                    vz[0], vz[1], vz[2], 0.,
                    vt[0], vt[1], vt[2], 1.,
                ])
            self.__data -= self.__data
            self.__data += m

        def imul(self, m):
            u"""
            マトリックス要素同士を乗算してセットする。

            :type m: `Matrix`
            :param m: 乗じるマトリックス。
            :rtype: `Matrix` (self)
            """
            a = self.__data
            b = m.__data
            b = _MM([
                a[0] * b[0],
                a[1] * b[1],
                a[2] * b[2],
                a[3] * b[3],
                a[4] * b[4],
                a[5] * b[5],
                a[6] * b[6],
                a[7] * b[7],
                a[8] * b[8],
                a[9] * b[9],
                a[10] * b[10],
                a[11] * b[11],
                a[12] * b[12],
                a[13] * b[13],
                a[14] * b[14],
                a[15] * b[15],
            ])
            a -= a
            a += b
            return self

        def idiv(self, m, pre=AVOID_ZERO_DIV_PRECISION):
            u"""
            各要素同士を除算し自身を更新する。

            ゼロ除算を避ける為、分母が `~.avoidZeroDiv`
            でフィルタされてから実行される。

            :param iterable v: 要素数16個以上のシーケンス。
            :param `float` pre: ゼロ除算を避ける為の許容誤差。
            """
            a = self.__data
            b = m.__data
            b = _MM([
                a[0] / avoidZeroDiv(b[0], pre),
                a[1] / avoidZeroDiv(b[1], pre),
                a[2] / avoidZeroDiv(b[2], pre),
                a[3] / avoidZeroDiv(b[3], pre),
                a[4] / avoidZeroDiv(b[4], pre),
                a[5] / avoidZeroDiv(b[5], pre),
                a[6] / avoidZeroDiv(b[6], pre),
                a[7] / avoidZeroDiv(b[7], pre),
                a[8] / avoidZeroDiv(b[8], pre),
                a[9] / avoidZeroDiv(b[9], pre),
                a[10] / avoidZeroDiv(b[10], pre),
                a[11] / avoidZeroDiv(b[11], pre),
                a[12] / avoidZeroDiv(b[12], pre),
                a[13] / avoidZeroDiv(b[13], pre),
                a[14] / avoidZeroDiv(b[14], pre),
                a[15] / avoidZeroDiv(b[15], pre),
            ])
            a -= a
            a += b
            return self

        def setTranslation(self, v):
            u"""
            平行移動値をセットする。

            :type v: `.Vector`
            :param v: 平行移動の3次元ベクトル。
            """
            self.__data[12] = 0.
            self.__data[13] = 0.
            self.__data[14] = 0.
            self.__data += _MM([
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                v[0], v[1], v[2], 0.,
            ])

        def addTranslation(self, v):
            u"""
            平行移動値を加算する。

            :type v: `.Vector`
            :param v: 平行移動の3次元ベクトル。
            """
            self.__data += _MM([
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                v[0], v[1], v[2], 0.,
            ])

        def subTranslation(self, v):
            u"""
            平行移動値を減算する。

            :type v: `.Vector`
            :param v: 平行移動の3次元ベクトル。
            """
            self.__data -= _MM([
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                0., 0., 0., 0.,
                v[0], v[1], v[2], 0.,
            ])

        def mirror(self, mirrorAxis=AXIS_X, negAxis=True, t=True):
            u"""
            指定軸方向でミラーしたマトリックスを得る。

            :param `int` mirrorAxis:
                ミラーする基準軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` のいずれかを指定する。
            :param `int` negAxis:
                行列式（スケール）が反転しないように、
                ミラー結果の逆を向けるローカル軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` の他に、
                None 、 False 、 True を指定可能。

                省略時(True)はミラー基準軸と同じになる。
                False では 3x3 部は反転しない。
                None ではミラー結果から全軸を逆に向ける。
            :param `bool` t:
                平行移動値（4行目）も反転するかどうか。
            :rtype: `Matrix`
            """
            return _newM(_mirror(self.__data, mirrorAxis, negAxis, t))

        def mirrorIt(self, mirrorAxis=AXIS_X, negAxis=True, t=True):
            u"""
            指定軸方向でミラーしたマトリックスをセットする。

            :param `int` mirrorAxis:
                ミラーする基準軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` のいずれかを指定する。
            :param `int` negAxis:
                行列式（スケール）が反転しないように、
                ミラー結果の逆を向けるローカル軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` の他に、
                None 、 False 、 True を指定可能。

                省略時(True)はミラー基準軸と同じになる。
                False では 3x3 部は反転しない。
                None ではミラー結果から全軸を逆に向ける。
            :param `bool` t:
                平行移動値（4行目）も反転するかどうか。
            :rtype: `Matrix` (self)
            """
            self.__data = _mirror(self.__data, mirrorAxis, negAxis, t)
            return self

    #--------------------------------------------------
    else:
        def __setitem__(self, i, v):
            self.__data[i] = v

        def set(self, v):
            u"""
            他の値をセットする。

            コンストラクタと同様に、以下の値を指定可能。

            - `Matrix`
            - 16値のシーケンス

            :rtype: `Matrix` (self)
            """
            try:
                v = v.__data
            except:
                pass
            dt = self.__data
            dt[0] = v[0]
            dt[1] = v[1]
            dt[2] = v[2]
            dt[3] = v[3]
            dt[4] = v[4]
            dt[5] = v[5]
            dt[6] = v[6]
            dt[7] = v[7]
            dt[8] = v[8]
            dt[9] = v[9]
            dt[10] = v[10]
            dt[11] = v[11]
            dt[12] = v[12]
            dt[13] = v[13]
            dt[14] = v[14]
            dt[15] = v[15]

        def setRow(self, i, v):
            u"""
            行ベクトルをセットする。

            :param `int` i: 行インデックス（0～3）。
            :type v: `.Vector`
            :param v: セットする4次元ベクトル。
            """
            i *= 4
            self.__data[i] = v[0]
            self.__data[i + 1] = v[1]
            self.__data[i + 2] = v[2]
            self.__data[i + 3] = v[3]

        def setRows(self, v0, v1, v2, v3):
            u"""
            行ベクトルを4つ全てセットする。

            :type v0: `.Vector`
            :param v0: 1行目の4次元ベクトル。
            :type v1: `.Vector`
            :param v1: 2行目の4次元ベクトル。
            :type v2: `.Vector`
            :param v2: 3行目の4次元ベクトル。
            :type v3: `.Vector`
            :param v3: 4行目の4次元ベクトル。
            """
            dt = self.__data
            dt[0] = v0[0]
            dt[1] = v0[1]
            dt[2] = v0[2]
            dt[3] = v0[3]
            dt[4] = v1[0]
            dt[5] = v1[1]
            dt[6] = v1[2]
            dt[7] = v1[3]
            dt[8] = v2[0]
            dt[9] = v2[1]
            dt[10] = v2[2]
            dt[11] = v2[3]
            dt[12] = v3[0]
            dt[13] = v3[1]
            dt[14] = v3[2]
            dt[15] = v3[3]

        def setColumn(self, i, v):
            u"""
            列ベクトルをセットする。

            :param `int` i: 列インデックス（0～3）。
            :type v: `.Vector`
            :param v: セットする4次元ベクトル。
            """
            self.__data[i] = v[0]
            self.__data[i + 4] = v[1]
            self.__data[i + 8] = v[2]
            self.__data[i + 12] = v[3]

        def setColumns(self, v0, v1, v2, v3):
            u"""
            列ベクトルを4つ全てセットする。

            :type v0: `.Vector`
            :param v0: 1列目の4次元ベクトル。
            :type v1: `.Vector`
            :param v1: 2列目の4次元ベクトル。
            :type v2: `.Vector`
            :param v2: 3列目の4次元ベクトル。
            :type v3: `.Vector`
            :param v3: 4列目の4次元ベクトル。
            """
            dt = self.__data
            dt[0] = v0[0]
            dt[1] = v1[0]
            dt[2] = v2[0]
            dt[3] = v3[0]
            dt[4] = v0[1]
            dt[5] = v1[1]
            dt[6] = v2[1]
            dt[7] = v3[1]
            dt[8] = v0[2]
            dt[9] = v1[2]
            dt[10] = v2[2]
            dt[11] = v3[2]
            dt[12] = v0[3]
            dt[13] = v1[3]
            dt[14] = v2[3]
            dt[15] = v3[3]

        def setAxis(self, i, v, transpose=False):
            u"""
            3x3部分の行や列のベクトルをセットする。

            :param `int` i: 軸指定(0=X, 1=Y, 2=Z)。
            :type v: `.Vector`
            :param v:
                セットする軸ベクトル。
            :param `bool` transpose:
                転置行列の軸ベクトルをセットする。
                言い換えると False では行ベクトルを
                True では列ベクトルをセットすることになる。
            """
            if transpose:
                self.__data[i] = v[0]
                self.__data[i + 4] = v[1]
                self.__data[i + 8] = v[2]
            else:
                i *= 4
                self.__data[i] = v[0]
                self.__data[i + 1] = v[1]
                self.__data[i + 2] = v[2]

        def setAxes(self, vx, vy, vz, vt=V.Zero, transpose=False):
            u"""
            3x3部分の行や列と4行目の平行移動ベクトルをセットする。

            :type vx: `.Vector`
            :param vx: セットするX軸ベクトル。
            :type vy: `.Vector`
            :param vy: セットするY軸ベクトル。
            :type vz: `.Vector`
            :param vz: セットするZ軸ベクトル。
            :type vt: `.Vector`
            :param vt:
                セットする平行移動ベクトル。
                これだけは transpose オプションの影響を受けない。
            :param `bool` transpose:
                3x3部分には転置行列の軸ベクトルをセットする。
                言い換えると False では行ベクトルを
                True では列ベクトルをセットすることになる。
            """
            dt = self.__data
            if transpose:
                dt[0] = vx[0]
                dt[1] = vy[0]
                dt[2] = vz[0]
                dt[3] = 0.
                dt[4] = vx[1]
                dt[5] = vy[1]
                dt[6] = vz[1]
                dt[7] = 0.
                dt[8] = vx[2]
                dt[9] = vy[2]
                dt[10] = vz[2]
                dt[11] = 0.
                dt[12] = vt[0]
                dt[13] = vt[1]
                dt[14] = vt[2]
                dt[15] = 1.
            else:
                dt[0] = vx[0]
                dt[1] = vx[1]
                dt[2] = vx[2]
                dt[3] = 0.
                dt[4] = vy[0]
                dt[5] = vy[1]
                dt[6] = vy[2]
                dt[7] = 0.
                dt[8] = vz[0]
                dt[9] = vz[1]
                dt[10] = vz[2]
                dt[11] = 0.
                dt[12] = vt[0]
                dt[13] = vt[1]
                dt[14] = vt[2]
                dt[15] = 1.

        def imul(self, m):
            u"""
            マトリックス要素同士を乗算してセットする。

            :type m: `Matrix`
            :param m: 乗じるマトリックス。
            :rtype: `Matrix` (self)
            """
            a = self.__data
            b = m.__data
            a[0] *= b[0]
            a[1] *= b[1]
            a[2] *= b[2]
            a[3] *= b[3]
            a[4] *= b[4]
            a[5] *= b[5]
            a[6] *= b[6]
            a[7] *= b[7]
            a[8] *= b[8]
            a[9] *= b[9]
            a[10] *= b[10]
            a[11] *= b[11]
            a[12] *= b[12]
            a[13] *= b[13]
            a[14] *= b[14]
            a[15] *= b[15]
            return self

        def idiv(self, m, pre=AVOID_ZERO_DIV_PRECISION):
            u"""
            各要素同士を除算し自身を更新する。

            ゼロ除算を避ける為、分母が `~.avoidZeroDiv`
            でフィルタされてから実行される。

            :param iterable v: 要素数16個以上のシーケンス。
            :param `float` pre: ゼロ除算を避ける為の許容誤差。
            """
            a = self.__data
            b = m.__data
            a[0] /= avoidZeroDiv(b[0], pre)
            a[1] /= avoidZeroDiv(b[1], pre)
            a[2] /= avoidZeroDiv(b[2], pre)
            a[3] /= avoidZeroDiv(b[3], pre)
            a[4] /= avoidZeroDiv(b[4], pre)
            a[5] /= avoidZeroDiv(b[5], pre)
            a[6] /= avoidZeroDiv(b[6], pre)
            a[7] /= avoidZeroDiv(b[7], pre)
            a[8] /= avoidZeroDiv(b[8], pre)
            a[9] /= avoidZeroDiv(b[9], pre)
            a[10] /= avoidZeroDiv(b[10], pre)
            a[11] /= avoidZeroDiv(b[11], pre)
            a[12] /= avoidZeroDiv(b[12], pre)
            a[13] /= avoidZeroDiv(b[13], pre)
            a[14] /= avoidZeroDiv(b[14], pre)
            a[15] /= avoidZeroDiv(b[15], pre)
            return self

        def setTranslation(self, v):
            u"""
            平行移動値をセットする。

            :type v: `.Vector`
            :param v: 平行移動の3次元ベクトル。
            """
            self.__data[12] = v[0]
            self.__data[13] = v[1]
            self.__data[14] = v[2]

        def addTranslation(self, v):
            u"""
            平行移動値を加算する。

            :type v: `.Vector`
            :param v: 平行移動の3次元ベクトル。
            """
            self.__data[12] += v[0]
            self.__data[13] += v[1]
            self.__data[14] += v[2]

        def subTranslation(self, v):
            u"""
            平行移動値を減算する。

            :type v: `.Vector`
            :param v: 平行移動の3次元ベクトル。
            """
            self.__data[12] -= v[0]
            self.__data[13] -= v[1]
            self.__data[14] -= v[2]

        def mirror(self, mirrorAxis=AXIS_X, negAxis=True, t=True):
            u"""
            指定軸方向でミラーしたマトリックスを得る。

            :param `int` mirrorAxis:
                ミラーする基準軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` のいずれかを指定する。
            :param `int` negAxis:
                行列式（スケール）が反転しないように、
                ミラー結果の逆を向けるローカル軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` の他に、
                None 、 False 、 True を指定可能。

                省略時(True)はミラー基準軸と同じになる。
                False では 3x3 部は反転しない。
                None ではミラー結果から全軸を逆に向ける。
            :param `bool` t:
                平行移動値（4行目）も反転するかどうか。
            :rtype: `Matrix`
            """
            m = _MM(self.__data)
            _mirror(m, mirrorAxis, negAxis, t)
            return _newM(m)

        def mirrorIt(self, mirrorAxis=AXIS_X, negAxis=True, t=True):
            u"""
            指定軸方向でミラーしたマトリックスをセットする。

            :param `int` mirrorAxis:
                ミラーする基準軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` のいずれかを指定する。
            :param `int` negAxis:
                行列式（スケール）が反転しないように、
                ミラー結果の逆を向けるローカル軸。
                `.AXIS_X` 、 `.AXIS_Y` 、 `.AXIS_Z` の他に、
                None 、 False 、 True を指定可能。

                省略時(True)はミラー基準軸と同じになる。
                False では 3x3 部は反転しない。
                None ではミラー結果から全軸を逆に向ける。
            :param `bool` t:
                平行移動値（4行目）も反転するかどうか。
            :rtype: `Matrix` (self)
            """
            _mirror(self.__data, mirrorAxis, negAxis, t)
            return self

    #--------------------------------------------------
    setT = setTranslation  #: `setTranslation` の別名。
    addT = addTranslation  #: `addTranslation` の別名。
    subT = subTranslation  #: `subTranslation` の別名。

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

    def isIdentity(self, tol=_TOLERANCE):
        u"""
        ほぼ単位行列かどうか。

        :param `float` tol: 許容誤差。
        :rtype: `bool`
        """
        return self.__data.isEquivalent(_MM_Identity, tol)

    def isSingular(self):
        u"""
        特異行列かどうか。

        :rtype: `bool`
        """
        return self.__data.isSingular()

    def setToIdentity(self):
        u"""
        単位行列をセットする。

        :rtype: `self`
        """
        self.__data.setToIdentity()
        return self

    def init3x3(self):
        u"""
        3x3 部分を初期化する。

        4x4 全て初期化する場合は `setToIdentity` が利用できる。

        平行移動成分のみの行列を新規に得たい場合は
        `asTranslationMatrix` が利用できる。

        :rtype: `Matrix` (self)
        """
        # 0 や 1 のセットは精度の問題はない。
        dt = self.__data
        dt[0] = 1.
        dt[1] = 0.
        dt[2] = 0.
        dt[4] = 0.
        dt[5] = 1.
        dt[6] = 0.
        dt[8] = 0.
        dt[9] = 0.
        dt[10] = 1.
        return self

    def initTranslation(self):
        u"""
        4行目の平行移動成分をクリアする。

        3x3 以外を初期化したマトリクスを新規に得たい場合は
        `as3x3` が利用できる。

        :rtype: `Matrix` (self)
        """
        dt = self.__data
        dt[12] = 0.
        dt[13] = 0.
        dt[14] = 0.
        return self

    initT = initTranslation  #: `initTranslation` の別名。

    def getElem(self, row, col):
        u"""
        指定位置の要素を得る。

        :param `int` row: 行インデックス (0-3)
        :param `int` col: 列インデックス (0-3)
        :rtype: `float`
        """
        return self[row * 4 + col]

    def setElem(self, row, col, val):
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
        return _newX(dict(m=_newM(_MM(self.__data), ImmutableMatrix)))

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
        if order == XYZ:
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
        if order == XYZ:
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
        スケーリング成分を得る。

        :rtype: `.Vector`
        """
        return _newV(_MP(_MX(self.__data).scale(_MSpace_kTransform)))

    asS = asScaling  #: `asScaling` の別名。

    def asShearing(self):
        u"""
        シアー成分を得る。

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

    def adjugate(self):
        u"""
        余因子行列を得る。

        :rtype: `Matrix`
        """
        return _newM(self.__data.adjoint())

    adjoint = adjugate  #: `adjugate` の別名。
    adj = adjugate  #: `adjugate` の別名。

    def adjugateIt(self):
        u"""
        余因子行列をセットする。

        :rtype: `Matrix` (self)
        """
        _M_setdata(self, self.__data.adjoint())
        return self

    adjointIt = adjugateIt  #: `adjugateIt` の別名。

    def cofactor(self, i, j):
        u"""
        指定位置の余因子を得る。

        :param `int` i: 行インデックス。
        :param `int` j: 列インデックス。
        :rtype: `float`
        """
        # python で det3 計算するより API を呼んだ方が速いだろう。
        return self.__data.adjoint()[j * 4 + i]

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

    orthonormalize = homogenize  # `homogenize` の別名。
    orthonormalizeIt = homogenizeIt  # `homogenizeIt` の別名。

    def det(self):
        u"""
        行列式を得る。

        :rtype: `float`
        """
        return self.__data.det4x4()

    det4 = det  #: `det` の別名。
    det4x4 = det  #: `det` の別名。
    determinant = det  #: `det` の別名。

    def det3(self):
        u"""
        3x3部分の行列式を得る。

        :rtype: `float`
        """
        return self.__data.det3x3()

    det3x3 = det3  #: `det3` の別名。
    determinant3 = det3  #: `det3` の別名。

    def det2(self):
        u"""
        2x2部分の行列式を得る。

        :rtype: `float`
        """
        m = self.__data
        return m[0] * m[5] - m[4] * m[1]

    det2x2 = det2  #: `det2` の別名。
    determinant2 = det2  #: `det2` の別名。

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

    col = column  #: `column` の別名。

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

    cols = columns  #: `columns` の別名。

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

    def mul(self, m):
        u"""
        マトリックス要素同士を乗算する。

        :type m: `Matrix`
        :param m: 乗じるマトリックス。
        :rtype: `Matrix`
        """
        a = self.__data
        b = m.__data
        return _newM(_MM([
            a[0] * b[0], a[1] * b[1], a[2] * b[2], a[3] * b[3],
            a[4] * b[4], a[5] * b[5], a[6] * b[6], a[7] * b[7],
            a[8] * b[8], a[9] * b[9], a[10] * b[10], a[11] * b[11],
            a[12] * b[12], a[13] * b[13], a[14] * b[14], a[15] * b[15],
        ]))

    def div(self, m, pre=AVOID_ZERO_DIV_PRECISION):
        u"""
        マトリックス要素同士を除算する。

        ゼロ除算を避ける為、分母が `.avoidZeroDiv`
        でフィルタされてから実行される。

        :type m: `Matrix`
        :param m: 分母のマトリックス。
        :param `float` pre: ゼロ除算を避ける為の許容誤差。
        :rtype: `Matrix`
        """
        a = self.__data
        b = m.__data
        return _newM(_MM([
            a[0] / avoidZeroDiv(b[0], pre),
            a[1] / avoidZeroDiv(b[1], pre),
            a[2] / avoidZeroDiv(b[2], pre),
            a[3] / avoidZeroDiv(b[3], pre),
            a[4] / avoidZeroDiv(b[4], pre),
            a[5] / avoidZeroDiv(b[5], pre),
            a[6] / avoidZeroDiv(b[6], pre),
            a[7] / avoidZeroDiv(b[7], pre),
            a[8] / avoidZeroDiv(b[8], pre),
            a[9] / avoidZeroDiv(b[9], pre),
            a[10] / avoidZeroDiv(b[10], pre),
            a[11] / avoidZeroDiv(b[11], pre),
            a[12] / avoidZeroDiv(b[12], pre),
            a[13] / avoidZeroDiv(b[13], pre),
            a[14] / avoidZeroDiv(b[14], pre),
            a[15] / avoidZeroDiv(b[15], pre),
        ]))

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

    @classmethod
    def makeTranslation(cls, v):
        u"""
        平行移動行列を作成する。

        :type v: `.Vector`
        :param v: 平行移動の3次元ベクトル。
        :rtype: `Matrix`
        """
        return _newM(_MM([
            1., 0., 0., 0.,
            0., 1., 0., 0.,
            0., 0., 1., 0.,
            v[0], v[1], v[2], 1.,
        ]), cls)

    makeT = makeTranslation  #: `makeTranslation` の別名。

    @classmethod
    def makeRotation(cls, v, order=XYZ):
        u"""
        オイラー角回転から回転行列を作成する。

        :param iterable v: 各軸の回転角度 (x,y,z) を Radians で。
        :param `int` order: 回転オーダーを表す整数値。
        :rtype: `Matrix`
        """
        return _newM(_ME(v, order).asMatrix(), cls)

    makeR = makeRotation  #: `makeRotation` の別名。

    @classmethod
    def makeInverseTranslation(cls, v):
        u"""
        平行移動の逆行列を作成する。

        :type v: `.Vector`
        :param v: 平行移動の3次元ベクトル。
        :rtype: `Matrix`
        """
        return _newM(_MM([
            1., 0., 0., 0.,
            0., 1., 0., 0.,
            0., 0., 1., 0.,
            -v[0], -v[1], -v[2], 1.,
        ]), cls)

    makeInvT = makeInverseTranslation  #: `makeInverseTranslation` の別名。

    @classmethod
    def makeScaling(cls, v):
        u"""
        スケーリング行列を作成する。

        :type v: `.Vector`
        :param v: スケール値の3次元ベクトル。
        :rtype: `Matrix`
        """
        return _newM(_MM([
            v[0], 0., 0., 0.,
            0., v[1], 0., 0.,
            0., 0., v[2], 0.,
            0., 0., 0., 1.,
        ]), cls)

    makeS = makeScaling  #: `makeScaling` の別名。

    @classmethod
    def makeInverseScaling(cls, v, pre=AVOID_ZERO_DIV_PRECISION):
        u"""
        スケーリングの逆行列を作成する。

        :type v: `.Vector`
        :param v: スケール値の3次元ベクトル。
        :param `float` pre: ゼロ除算を避ける為の許容誤差。
        :rtype: `Matrix`
        """
        return _newM(_MM([
            1. / avoidZeroDiv(v[0], pre), 0., 0., 0.,
            0., 1. / avoidZeroDiv(v[1], pre), 0., 0.,
            0., 0., 1. / avoidZeroDiv(v[2], pre), 0.,
            0., 0., 0., 1.,
        ]), cls)

    makeInvS = makeInverseScaling  #: `makeInverseScaling` の別名。

    @classmethod
    def makeShearing(cls, v):
        u"""
        シアー行列を作成する。

        :type v: `.Vector`
        :param v: シアー値 (xy, yz, yx)
        :rtype: `Matrix`
        """
        return _newM(_MM([
            1., 0., 0., 0.,
            v[0], 1., 0., 0.,
            v[1], v[2], 1., 0.,
            0., 0., 0., 1.,
        ]), cls)

    makeSh = makeShearing  #: `makeShearing` の別名。

    @classmethod
    def makeInverseShearing(cls, v):
        u"""
        シアーの逆行列を作成する。

        :type v: `.Vector`
        :param v: シアー値 (xy, yz, yx)
        :rtype: `Matrix`
        """
        return _newM(_MM([
            1., 0., 0., 0.,
            -v[0], 1., 0., 0.,
            v[0] * v[2] - v[1], -v[2], 1., 0.,
            0., 0., 0., 1.,
        ]), cls)

    makeInvSh = makeInverseShearing  #: `makeInverseShearing` の別名。

M = Matrix  #: `Matrix` の別名。

_MUTATOR_DICT[M] = (
    'set',
    'setRow',
    'setRows',
    'setColumn',
    'setColumns',
    'setAxis',
    'setAxes',
    'imul'
    'idiv'
    'setTranslation', 'setT',
    'addTranslation', 'addT',
    'subTranslation', 'subT',
    'mirrorIt',
    'setToIdentity',
    'init3x3',
    'initTranslation', 'initT',
    'setElem',
    'transposeIt',
    'invertIt',
    'adjugateIt', 'adjointIt',
    'homogenizeIt', 'orthonormalizeIt',
)
ImmutableMatrix = immutableType(M)  #: `Matrix` の `immutable` ラッパー。


def _newM(data, cls=M):
    obj = _object_new(cls)
    _M_setdata(obj, data)
    return obj
_object_new = object.__new__

_M_setdata = M._Matrix__data.__set__

M.Tolerance = _TOLERANCE  #: 同値とみなす許容誤差。

M.Identity = ImmutableMatrix()  #: 単位行列。
M.Zero = ImmutableMatrix([0] * 16)  #: ゼロ。


#------------------------------------------------------------------------------
# Fix DoubleAccessorBug
if MAYA_VERSION < (2023,):
    def _mirror(d, mirrorAxis, negAxis, t):
        if mirrorAxis == AXIS_X:
            t = -d[12] if t else d[12]
            if negAxis is False:
                return _MM([d[0], d[1], d[2], 0., d[4], d[5], d[6], 0., d[8], d[9], d[10], 0., t, d[13], d[14], 1.])
            elif negAxis is True or negAxis == mirrorAxis:
                return _MM([d[0], -d[1], -d[2], 0., -d[4], d[5], d[6], 0., -d[8], d[9], d[10], 0., t, d[13], d[14], 1.])
            elif negAxis is None:
                return _MM([d[0], -d[1], -d[2], 0., d[4], -d[5], -d[6], 0., d[8], -d[9], -d[10], 0., t, d[13], d[14], 1.])
            elif negAxis == AXIS_Y:
                return _MM([-d[0], d[1], d[2], 0., d[4], -d[5], -d[6], 0., -d[8], d[9], d[10], 0., t, d[13], d[14], 1.])
            else:  # AXIS_Z
                return _MM([-d[0], d[1], d[2], 0., -d[4], d[5], d[6], 0., d[8], -d[9], -d[10], 0., t, d[13], d[14], 1.])

        elif mirrorAxis == AXIS_Y:
            t = -d[13] if t else d[13]
            if negAxis is False:
                return _MM([d[0], d[1], d[2], 0., d[4], d[5], d[6], 0., d[8], d[9], d[10], 0., d[12], t, d[14], 1.])
            elif negAxis is True or negAxis == mirrorAxis:
                return _MM([d[0], -d[1], d[2], 0., -d[4], d[5], -d[6], 0., d[8], -d[9], d[10], 0., d[12], t, d[14], 1.])
            elif negAxis is None:
                return _MM([-d[0], d[1], -d[2], 0., -d[4], d[5], -d[6], 0., -d[8], d[9], -d[10], 0., d[12], t, d[14], 1.])
            elif negAxis == AXIS_X:
                return _MM([-d[0], d[1], -d[2], 0., d[4], -d[5], d[6], 0., d[8], -d[9], d[10], 0., d[12], t, d[14], 1.])
            else:  # AXIS_Z
                return _MM([d[0], -d[1], d[2], 0., d[4], -d[5], d[6], 0., -d[8], d[9], -d[10], 0., d[12], t, d[14], 1.])

        else:  # AXIS_Z
            t = -d[14] if t else d[14]
            if negAxis is False:
                return _MM([d[0], d[1], d[2], 0., d[4], d[5], d[6], 0., d[8], d[9], d[10], 0., d[12], d[13], t, 1.])
            elif negAxis is True or negAxis == mirrorAxis:
                return _MM([d[0], d[1], -d[2], 0., d[4], d[5], -d[6], 0., -d[8], -d[9], d[10], 0., d[12], d[13], t, 1.])
            elif negAxis is None:
                return _MM([-d[0], -d[1], d[2], 0., -d[4], -d[5], d[6], 0., -d[8], -d[9], d[10], 0., d[12], d[13], t, 1.])
            elif negAxis == AXIS_X:
                return _MM([-d[0], -d[1], d[2], 0., d[4], d[5], -d[6], 0., d[8], d[9], -d[10], 0., d[12], d[13], t, 1.])
            else:  # AXIS_Y
                return _MM([d[0], d[1], -d[2], 0., -d[4], -d[5], d[6], 0., d[8], d[9], -d[10], 0., d[12], d[13], t, 1.])

else:
    def _mirror(d, mirrorAxis, negAxis, t):
        if mirrorAxis == AXIS_X:
            if t:
                d[12] = -d[12]
            if negAxis is not False:
                if negAxis is True or negAxis == mirrorAxis:
                    d[1] = -d[1]
                    d[2] = -d[2]
                    d[4] = -d[4]
                    d[8] = -d[8]
                elif negAxis is None:
                    d[1] = -d[1]
                    d[2] = -d[2]
                    d[5] = -d[5]
                    d[6] = -d[6]
                    d[9] = -d[9]
                    d[10] = -d[10]
                elif negAxis == AXIS_Y:
                    d[0] = -d[0]
                    d[5] = -d[5]
                    d[6] = -d[6]
                    d[8] = -d[8]
                else:  # AXIS_Z
                    d[0] = -d[0]
                    d[4] = -d[4]
                    d[9] = -d[9]
                    d[10] = -d[10]

        elif mirrorAxis == AXIS_Y:
            if t:
                d[13] = -d[13]
            if negAxis is not False:
                if negAxis is True or negAxis == mirrorAxis:
                    d[1] = -d[1]
                    d[4] = -d[4]
                    d[6] = -d[6]
                    d[9] = -d[9]
                elif negAxis is None:
                    d[0] = -d[0]
                    d[2] = -d[2]
                    d[4] = -d[4]
                    d[6] = -d[6]
                    d[8] = -d[8]
                    d[10] = -d[10]
                elif negAxis == AXIS_X:
                    d[0] = -d[0]
                    d[2] = -d[2]
                    d[5] = -d[5]
                    d[9] = -d[9]
                else:  # AXIS_Z
                    d[1] = -d[1]
                    d[5] = -d[5]
                    d[8] = -d[8]
                    d[10] = -d[10]

        else:  # AXIS_Z
            if t:
                d[14] = -d[14]
            if negAxis is not False:
                if negAxis is True or negAxis == mirrorAxis:
                    d[2] = -d[2]
                    d[6] = -d[6]
                    d[8] = -d[8]
                    d[9] = -d[9]
                elif negAxis is None:
                    d[0] = -d[0]
                    d[1] = -d[1]
                    d[4] = -d[4]
                    d[5] = -d[5]
                    d[8] = -d[8]
                    d[9] = -d[9]
                elif negAxis == AXIS_X:
                    d[0] = -d[0]
                    d[1] = -d[1]
                    d[6] = -d[6]
                    d[10] = -d[10]
                else:  # AXIS_Y
                    d[2] = -d[2]
                    d[4] = -d[4]
                    d[5] = -d[5]
                    d[10] = -d[10]

