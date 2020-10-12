# -*- coding: utf-8 -*-
u"""
トランスフォーメーション関連のテスト。
"""
from cymel.all import *
from random import seed, random, uniform, randrange
from math import sqrt, cos, sin

__all__ = ['doit']

cm_O = cm.O
Transform = cm.Transform

Vector = cm.V
Quaternion = cm.Q
EulerRotation = cm.E
Matrix = cm.M
Transformation = cm.X

_2PI = 2. * PI
_n2PI = -2. * PI

HAS_JOINT_SHEAR_BUG = (2019,) <= cm.MAYA_VERSION < (2020, 1)    #: joint の shear が利用不可。


#------------------------------------------------------------------------------
def doit(s=13):
    #cmds.file(f=True, new=True)

    seed(s)

    #---------------------------------------
    # transform の階層。
    # tranform から transform へのフィッティングのテスト。
    obja = Transform(n='a')
    _setXform(obja)

    objb = cm_O(cmds.polyCube(n='b')[0])
    objb.dla.set(True)
    objb.dsp.set(True)
    objb.setParent(obja, r=True)
    _setXform(objb)

    shape = objb.shape()

    objc = Transform(n='c')
    _setXform(objc)

    objd = Transform(n='d')
    objd.addChild(shape, add=True)
    objd.dla.set(True)
    objd.dsp.set(True)
    objd.setParent(objc, r=True)
    _setXform(objd)

    obje = Transform(n='e')
    obje.addChild(shape, add=True)
    obje.dla.set(True)
    obje.dsp.set(True)
    _setXform(obje)

    _testFitAll(objd, objb)
    _testFitAll(obje, objb)

    #---------------------------------------
    # joint の階層。
    # joint から joint へのフィッティングのテスト。
    # transform から joint へのフィッティングのテスト。
    jnta = cm.nt.Joint(n='ja')
    _setXform(jnta)

    jntb = cm.nt.Joint(n='jb')
    jntb.addChild(shape, add=True)
    jntb.dla.set(True)
    jntb.dsp.set(True)
    jntb.setParent(jnta, r=True)
    _setXform(jntb)

    jntc = cm.nt.Joint(n='jc')
    _setXform(jntc)

    jntd = cm.nt.Joint(n='jd')
    jntd.addChild(shape, add=True)
    jntd.dla.set(True)
    jntd.dsp.set(True)
    jntd.setParent(jntc, r=True)
    _setXform(jntd)

    jnte = cm.nt.Joint(n='je')
    jnte.addChild(shape, add=True)
    jnte.dla.set(True)
    jnte.dsp.set(True)
    _setXform(jnte)

    # joint の shear が利用できないバージョンではテストしない。
    if not HAS_JOINT_SHEAR_BUG:
        _testFitAll(jntd, jntb)
        _testFitAll(jnte, jntb)

        _testFitAll(jntb, objb)
        _testFitAll(jntd, objb)
        _testFitAll(jnte, objb)

    #---------------------------------------
    # transform 階層を追加。
    # joint から transform へのフィッティングのテスト。
    objf = Transform(n='f')
    _setXform(objf)

    objg = Transform(n='g')
    objg.addChild(shape, add=True)
    objg.dla.set(True)
    objg.dsp.set(True)
    objg.setParent(objf, r=True)
    _setXform(objg)

    objh = Transform(n='h')
    objh.addChild(shape, add=True)
    objh.dla.set(True)
    objh.dsp.set(True)
    _setXform(objh)

    _testFitAll(objg, jntb)
    _testFitAll(objh, jntb)


#------------------------------------------------------------------------------
def _setXform(obj, x=None, **kwargs):
    u"""
    Transformation をセットし、うまくいくかテストする。
    """
    print('# %r.setX: (%s)' % (obj, _optstr(kwargs)))
    if not x:
        x = randX(obj.isJoint())

    obj.setX(x, **kwargs)
    s = x.m
    d = obj.getM(**kwargs)
    assert d.isEquivalent(s), '%r <- X(%s)' % (obj, _optstr(kwargs))

    if not kwargs.get('ws'):
        _checkXform(obj, x, **kwargs)

    _checkXform(obj)
    _checkXform(obj, ws=True)

    return x


def _testFitAll(dst, src):
    u"""
    様々なトランスフォーメーション要素のフィッティングのテスト。
    """
    xform = dst.getX()
    for ws in (False, True):
        # 各テストの最初に毎回 _setXform しているのは、
        # その前の操作の影響が無いように公平にテストするため。

        # 様々な位置。
        if ws:
            _setXform(dst, xform)
        _fittest(dst, src, 'T', ws=ws, at=1)
        _fittest(dst, src, 'T', ws=ws, at=2)
        _fittest(dst, src, 'T', ws=ws, at=3)

        # 回転姿勢。
        if dst.isJoint():
            _fittest(dst, src, 'Q', ws=ws, r=False)
        _fittest(dst, src, 'Q', ws=ws)

        # q, s, sh, t を個別にフィット。最後は matrix も比較。
        _setXform(dst, xform)
        _fittest(dst, src, 'Q', ws=ws, ra=True)
        _fittest(dst, src, 'S', ws=ws)
        _fittest(dst, src, 'Sh', ws=ws)
        _fittest(dst, src, 'T', ws=ws, at=4)
        _compare(dst, src, 'M', ws=ws)

        # マトリックス。
        _setXform(dst, xform)
        _fittest(dst, src, 'M', ws=ws)

        # ピボットなども含めたトランスフォーメーション情報。
        _setXform(dst, xform)
        _fittest(dst, src, 'X', ws=ws)


def _fittest(dst, src, key, **kwargs):
    u"""
    get<key> の結果を set<key> して <key> がフィットしたかをテストする。

    <key> には M, Q, S, Sh, T, X などを指定。
    """
    print('# fit: %r <- %r : %s(%s)' % (dst, src, key, _optstr(kwargs)))
    s = getattr(src, 'get' + key)(**kwargs)
    getattr(dst, 'set' + key)(s, **kwargs)
    _compare(dst, src, key, s, **kwargs)


def _compare(dst, src, key, s=None, **kwargs):
    u"""
    <key> のフィット具合を比較する。
    """
    if not s:
        s = getattr(src, 'get' + key)(**kwargs)
    d = getattr(dst, 'get' + key)(**kwargs)
    if key != 'X' or dst.isJoint() == src.isJoint():
        assert d.isEquivalent(s), '%r <- %r : %s(%s) : %r, %r' % (dst, src, key, _optstr(kwargs), d, s)
    else:
        assert d.m.isEquivalent(s.m), '%r <- %r : %s(%s).m : %r, %r' % (dst, src, key, _optstr(kwargs), d.m, s.m)
        assert d.s.isEquivalent(s.s), '%r <- %r : %s(%s).s : %r, %r' % (dst, src, key, _optstr(kwargs), d.s, s.s)
        assert d.sh.isEquivalent(s.sh), '%r <- %r : %s(%s).sh : %r, %r' % (dst, src, key, _optstr(kwargs), d.sh, s.sh)
        assert d.ra.isEquivalent(s.ra), '%r <- %r : %s(%s).ra : %r, %r' % (dst, src, key, _optstr(kwargs), d.ra, s.ra)


def _checkXform(obj, x=None, **kwargs):
    u"""
    Transformation の各要素を比較する。
    """
    if not x:
        x = obj.getX(**kwargs)

    # matrix
    d = x.m
    s = obj.getM(**kwargs)
    assert d.isEquivalent(s), '%r : xform M(%s) : %r, %r' % (obj, _optstr(kwargs), d, s)

    # scaling
    d = x.s
    s = obj.getS(**kwargs)
    assert d.isEquivalent(s), '%r : xform S(%s) : %r, %r' % (obj, _optstr(kwargs), d, s)

    # shearing
    d = x.sh
    s = obj.getSh(**kwargs)
    assert d.isEquivalent(s), '%r : xform Sh(%s) : %r, %r' % (obj, _optstr(kwargs), d, s)

    # rotation(ra * r * jo)
    d = x.ra * x.r.asQ() * x.jo
    opts = dict(kwargs)
    opts['ra'] = True
    s = obj.getQ(**opts)
    assert d.isEquivalent(s), '%r : xform Q(%s) : %r, %r' % (obj, _optstr(opts), d, s)

    # rotation(r * jo)
    d = x.r.asQ() * x.jo
    s = obj.getQ(**kwargs)
    assert d.isEquivalent(s), '%r : xform Q(%s) : %r, %r' % (obj, _optstr(kwargs), d, s)

    # rotation(jo)
    if obj.isJoint() and not kwargs.get('ws'):
        d = x.jo
        opts = dict(kwargs)
        opts['r'] = False
        s = obj.getQ(**opts)
        assert d.isEquivalent(s), '%r : xform Q(%s) : %r, %r' % (obj, _optstr(opts), d, s)

    # position
    for i in ((4,) if obj.isJoint() else (4, 3, 2, 1)):
        d = x.asPosition(i)
        opts = dict(kwargs)
        opts['at'] = i
        s = obj.getT(**opts)
        assert d.isEquivalent(s), '%r : xform T(%s) : %r, %r' % (obj, _optstr(opts), d, s)


def _optstr(opts):
    return ', '.join([('%s=%r' % kv) for kv in opts.items()])


#------------------------------------------------------------------------------
def sphrand():
    t = uniform(0., _2PI)
    z = uniform(-1., 1.)
    zz = z * z
    return Vector(sqrt(1. - zz) * cos(t), sqrt(1. - zz) * sin(t), z)


def randE():
    return EulerRotation(
        uniform(_n2PI, _2PI),
        uniform(_n2PI, _2PI),
        uniform(_n2PI, _2PI),
        randrange(0, 6)
    )


def randQ():
    return Quaternion(sphrand(), uniform(_n2PI, _2PI))


def rand3(v):
    return uniform(-v, v), uniform(-v, v), uniform(-v, v)


def randScl(v):
    return uniform(0., v), uniform(0., v), uniform(0., v)


def randX(isJoint=False):
    opts = dict(
        t=rand3(5),
        r=randE(),
        sh=rand3(.5),
        s=randScl(2),
        ra=randQ(),
    )
    if isJoint:
        if HAS_JOINT_SHEAR_BUG:
            del opts['sh']
        opts['jo'] = randQ()
    else:
        opts['rpt'] = rand3(2)
        opts['rp'] = rand3(2)
        opts['spt'] = rand3(2)
        opts['sp'] = rand3(2)
    return Transformation(**opts)

