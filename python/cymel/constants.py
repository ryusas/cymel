# -*- coding: utf-8 -*-
u"""
cymel全体で使用する主な定数。

よく使うものに厳選してあるので * で import しても良いかも知れない。
"""
from math import pi as PI  #: π

TO_DEG = 180. / PI  #: Radians を Degrees に変換するための係数。
TO_RAD = PI / 180.  #: Degrees を Radians に変換するための係数。

#TOLERANCE = 1. / (2 ** 30)  #: DCCツールなどで一般的に使用する想定の許容誤差。
#LOOSE_TOLERANCE = 1. / (2 ** 18)  #: DCCツールなどでの緩めの許容誤差。
AVOID_ZERO_DIV_PRECISION = 1.e-13  #: Maya では scale=0 を設定しても matrix 値は 1.e-12 くらいで潰れずに保持するようなので、それを意識したリミット。

XYZ = 0  #: Rotaion order XYZ (0)
YZX = 1  #: Rotaion order YZX (1)
ZXY = 2  #: Rotaion order ZXY (2)
XZY = 3  #: Rotaion order XZY (3)
YXZ = 4  #: Rotaion order YXZ (4)
ZYX = 5  #: Rotaion order ZYX (5)

AXIS_X = 0  #: X軸（+X方向ID） (0)
AXIS_Y = 1  #: Y軸（+X方向ID） (1)
AXIS_Z = 2  #: Z軸（+X方向ID） (2)
#AXIS_XYZ = 4  #: XYZ軸全てを意味する。
AXIS_NEG = 0x10  # X,Y,Z の軸ID（ビットフラグではない）に加算して逆向き扱いする為のビットフラグ。
#AXIS_RNEG = ~AXIS_NEG  #: AXIS_NEG のビット反転。
AXIS_NEG_X = AXIS_NEG + AXIS_X  #: -X方向ID。
AXIS_NEG_Y = AXIS_NEG + AXIS_Y  #: -Y方向ID。
AXIS_NEG_Z = AXIS_NEG + AXIS_Z  #: -Z方向ID。

