# -*- coding: utf-8 -*-
u"""
Plugのsetやgetのテスト。
"""
import sys
from functools import partial
from maya.api.OpenMaya import (
    MVector, MPoint, MFloatVector,
    MMatrix, MFloatMatrix, MQuaternion,
    MColor,
)

from cymel.all import *
from random import seed, random, uniform, randrange
from .xform import randX

__all__ = ['doit']

_XformClasses = (cm.Matrix, cm.Transformation)


#------------------------------------------------------------------------------
def doit(s=13):
    seed(s)

    cm.loadPlugin('exprespy')
    expr = cm.nt.Exprespy()

    x = randX()

    p = expr.i[0]
    _testSetGet(p, _randI())
    _testSetGet(p, _randF())
    _testSetGet(p, x)
    _testSetGet(p, x.m)
    _testSetGet(p, MMatrix(x.m))
    _testSetGet(p, MFloatMatrix(x.m))
    _testSetGet(p, x.t)
    _testSetGet(p, MVector(x.t))
    _testSetGet(p, x.q)
    _testSetGet(p, MQuaternion(x.q))
    _testSetGet(p, MPoint(x.q))
    _testSetGet(p, _randFArr(2))
    _testSetGet(p, _randS())

    p = expr.addAttr('dblmat', 'matrix', getPlug=True)
    _testSetGet(p, x)
    _testSetGet(p, x.m)
    _testSetGet(p, MMatrix(x.m))
    _testSetGet(p, MFloatMatrix(x.m))

    p = expr.addAttr('atdblmat', 'at:matrix', getPlug=True)
    _testSetGet(p, x.m)
    _testSetGet(p, MMatrix(x.m))
    _testSetGet(p, MFloatMatrix(x.m))

    p = expr.addAttr('fltmat', 'fltMatrix', getPlug=True)
    _testSetGet(p, MFloatMatrix(x.m))

    p = expr.addAttr('bool', 'bool', getPlug=True)
    _testSetGet(p, False)
    _testSetGet(p, True)

    _testSetGet(expr.addAttr('byte', 'byte', getPlug=True), _randI(0, 128))  # 0～127
    _testSetGet(expr.addAttr('char', 'char', getPlug=True), _randI(0, 128))  # 0～127
    _testSetGet(expr.addAttr('short', 'short', getPlug=True), _randI(-32767, 32767))
    _testSetGet(expr.addAttr('long', 'long', getPlug=True), _randI())
    _testSetGet(expr.addAttr('double', 'double', getPlug=True), _randF())
    _testSetGet(expr.addAttr('doubleLinear', 'doubleLinear', getPlug=True), _randF(), partial(_compareF, tol=1e-12))
    _testSetGet(expr.addAttr('doubleAngle', 'doubleAngle', getPlug=True), _randF(), partial(_compareF, tol=1e-12))
    _testSetGet(expr.addAttr('time', 'time', getPlug=True), _randF(), partial(_compareF, tol=1e-4))

    _testSetGet(expr.addAttr('float', 'float', getPlug=True), _randF(), _compareF)
    _testSetGet(expr.addAttr('floatLinear', 'floatLinear', getPlug=True), _randF(), _compareF)
    _testSetGet(expr.addAttr('floatAngle', 'floatAngle', getPlug=True), _randF(), _compareF)

    _testSetGet(expr.addAttr('string', 'string', getPlug=True), _randS())

    _testSetGet(expr.addAttr('dtdouble3', 'dt:double3', getPlug=True), x.s)
    _testSetGet(expr.addAttr('double3', 'double3', getPlug=True), x.s)
    _testSetGet(expr.addAttr('dblang3', 'double3', 'doubleAngle', getPlug=True), x.r, partial(_compareFArr, tol=1e-12))
    _testSetGet(expr.addAttr('dbllnr3', 'double3', 'doubleLinear', getPlug=True), x.t, partial(_compareFArr, tol=1e-12))

    _testSetGet(expr.addAttr('dtfloat3', 'dt:float3', getPlug=True), x.s, _compareFArr)
    _testSetGet(expr.addAttr('float3', 'float3', getPlug=True), x.s, _compareFArr)
    _testSetGet(expr.addAttr('fltang3', 'float3', 'floatAngle', getPlug=True), x.r, _compareFArr)
    _testSetGet(expr.addAttr('fltlnr3', 'float3', 'floatLinear', getPlug=True), x.t, _compareFArr)
    _testSetGet(expr.addAttr('color', 'float3', uac=True, getPlug=True), _randColor())

    _testSetGet(expr.addAttr('reflectanceRGB', 'reflectanceRGB', getPlug=True), _randColor())
    _testSetGet(expr.addAttr('spectrumRGB', 'spectrumRGB', getPlug=True), _randColor())
    # setAttr すると Red にしか値が入らず、且つ違う値になる。-dt の方は問題ないのでバグだろう。
    #_testSetGet(expr.addAttr('reflectance', 'reflectance', getPlug=True), _randColor())
    #_testSetGet(expr.addAttr('spectrum', 'spectrum', getPlug=True), _randColor())

    _testSetGetArray(expr.addAttr('dblarr', 'doubleArray', getPlug=True), _randFArr, range(8))
    _testSetGetArray(expr.addAttr('fltarr', 'floatArray', getPlug=True), _randFArr, range(8), _compareFArr)
    _testSetGetArray(expr.addAttr('i32arr', 'Int32Array', getPlug=True), _randIArr, range(8))
    _testSetGetArray(expr.addAttr('strarr', 'stringArray', getPlug=True), _randSArr, range(8))

    # Int64Array の setAttr はバギー。
    # - long を含むとエラー。
    # - 要素数が奇数だと要素が1個減ってセットされる。
    # - 負数は含められないので、実質 unsigned ぽいが、バグか仕様かは不明。
    _testSetGetArray(expr.addAttr('i64arr', 'Int64Array', getPlug=True), partial(_randIArr, mn=0), range(0, 8, 2))  # _randLArr, range(8))

    _testSetGetArray(expr.addAttr('matarr', 'matrixArray', getPlug=True), _randMatArr, range(8))
    _testSetGetArray(expr.addAttr('vecarr', 'vectorArray', getPlug=True), _randVecArr, range(8))
    _testSetGetArray(expr.addAttr('fvecarr', 'floatVectorArray', getPlug=True), _randFVecArr, range(8))
    _testSetGetArray(expr.addAttr('pntarr', 'pointArray', getPlug=True), _randPntArr, range(8))


#------------------------------------------------------------------------------
def _testSetGetArray(plug, generator, nums, compare=None):
    for i in nums:
        _testSetGet(plug, generator(i), compare)


def _testSetGet(plug, val, compare=None):
    cls = type(val)
    mustBeTyped = not issubclass(cls, _XformClasses)
    msgbase = plug.type() + ' ' + cls.__name__

    plug.set(val)
    print(plug.mplug().getSetAttrCmds())
    v = plug.get()
    if mustBeTyped:
        v = cls(v)
    res = compare(val, v) if compare else (val == v)
    msg = msgbase + ' set/get'
    assert res, (msg + ': %r, %r' % (val, v))
    print(msg + ': OK')

    plug.setu(val)
    #print(plug.mplug().getSetAttrCmds())
    v = plug.getu()
    if mustBeTyped:
        v = cls(v)
    res = compare(val, v) if compare else (val == v)
    msg = msgbase + ' setu/getu'
    assert res, (msg + ': %r, %r' % (val, v))
    print(msg + ': OK')


#------------------------------------------------------------------------------
def _compareF(a, b, tol=1.e-6):
    return abs(a - b) <= tol


def _compareFArr(a, b, tol=1.e-6):
    na = len(a)
    nb = len(b)
    if na != nb:
        return False
    for a, b in zip(a, b):
        if abs(a - b) > tol:
            return False
    return True


#------------------------------------------------------------------------------
def _randI(mn=-cm.MAXINT32, mx=cm.MAXINT32):
    return randrange(mn, mx)


def _randIArr(n, mn=-cm.MAXINT32, mx=cm.MAXINT32):
    return [randrange(mn, mx) for i in range(n)]


def _randL():
    return randrange(_MAXINT32_1, cm.MAXINT64)
_MAXINT32_1 = int(cm.MAXINT32 + 1)


def _randLArr(n):
    return [_randL() for i in range(n)]


def _randF(mn=-10., mx=10.):
    return uniform(mn, mx)


def _randFArr(n, mn=-10., mx=10.):
    return [uniform(mn, mx) for i in range(n)]


def _randS():
    return _STR_TABLE[randrange(0, _STR_TABLE_LEN)]


def _randSArr(n):
    return [_randS() for i in range(n)]

_STR_TABLE = tuple(dir(sys))
_STR_TABLE_LEN = len(_STR_TABLE)


def _randVecArr(n):
    return [MVector(_randFArr(3)) for i in range(n)]


def _randFVecArr(n):
    return [MFloatVector(_randFArr(3)) for i in range(n)]


def _randPntArr(n):
    return [MPoint(_randFArr(4)) for i in range(n)]


def _randMatArr(n):
    return [randX().m for i in range(n)]


def _randColor():
    return MColor([_randF(0., 1.), _randF(0., 1.), _randF(0., 1.)])

