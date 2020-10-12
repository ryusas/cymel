# -*- coding: utf-8 -*-
u"""
`.Transform` クラスでサポートする機能の中核。
"""
from ...common import *
from ._api2mplug import mplug_get_nums
from ..datatypes.vector import V, _newV
from ..datatypes.quaternion import _newQ
from ..datatypes.matrix import _newM
from ..datatypes.transformation import (
    X, _MM_makeS, _MM_makeT, _MM_setT,
)
import maya.api.OpenMaya as _api2

__all__ = []

_MFn = _api2.MFn
_MX = _api2.MTransformationMatrix
_MM = _api2.MMatrix
_MQ = _api2.MQuaternion
_ME = _api2.MEulerRotation
_MP = _api2.MPoint
_MV = _api2.MVector

_MFn_kJoint = _MFn.kJoint
_MSpace_kTransform = _api2.MSpace.kTransform

_ZERO3_LIST = [0., 0., 0.]
_ONE3_LIST = [1., 1., 1.]


#------------------------------------------------------------------------------
class TransformMixin(object):
    u"""
    `.Transform` クラスでサポートする機能の中核。
    """
    __slots__ = tuple()

    def setScaling(self, v, ws=False, safe=False, get=False):
        u"""
        ノードのスケーリングの値をセットする。

        ws=False の場合は、
        単に scale アトリビュートの値を意味し、
        :mayanode:`joint` ノードのローカルマトリックスには含まれる
        inverseScale の影響は無視される。

        :param `sequence` v: セットしたい scale 値。
        :param `bool` ws: ワールド空間でセットするかどうか。
        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 のセットできる箇所だけセットされる。
        :param `bool` get:
            実際にはセットせず、
            セットされるべき scale アトリビュート値を得る。
        :rtype: `list` or None

        .. warning::
            セグメントスケール補正されていない非一様スケーリングや
            シアー変換が上位に存在する場合は、
            このノードの回転の影響も受けるため、
            先に回転をセットしなければならない。
        """
        val = v
        if ws:
            mpath = self._mpath()
            if mpath.length() > 1:
                m = _MX(mpath.inclusiveMatrix()).setScale(v, _MSpace_kTransform).asMatrix()
                m *= mpath.exclusiveMatrixInverse()
                if mpath.hasFn(_MFn_kJoint):
                    findPlug = self.mfn_().findPlug
                    if findPlug('ssc', True).asBool():
                        s = mplug_get_nums(findPlug('is', True))
                        m *= _MM_makeS(s)
                val = _MX(m).scale(_MSpace_kTransform)

            elif mpath.hasFn(_MFn_kJoint):
                findPlug = self.mfn_().findPlug
                if findPlug('ssc', True).asBool():
                    s = mplug_get_nums(findPlug('is', True))
                    if s != _ONE3_LIST:
                        m = _MX(mpath.inclusiveMatrix()).setScale(v, _MSpace_kTransform).asMatrix()
                        m *= _MM_makeS(s)
                        val = _MX(m).scale(_MSpace_kTransform)
        else:
            self.checkValid()

        if get:
            return list(v) if v is val else val
        self.plug_('s').set(val, safe=safe)

    setS = setScaling  #: `setScaling` の別名。

    def setShearing(self, v, ws=False, safe=False, get=False):
        u"""
        ノードのせん断の値をセットする。

        ws=False の場合は、
        単に shear アトリビュートの値を意味し、
        :mayanode:`joint` ノードのローカルマトリックスには含まれる
        inverseScale の影響は無視される。

        :param `sequence` v: セットしたい shear 値。
        :param `bool` ws: ワールド空間でセットするかどうか。
        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 のセットできる箇所だけセットされる。
        :param `bool` get:
            実際にはセットせず、
            セットされるべき shear アトリビュート値だけ計算する。
        :rtype: `list` or None

        .. warning::
            セグメントスケール補正されていない非一様スケーリングや
            シアー変換が上位に存在する場合は、
            このノードの回転の影響も受けるため、
            先に回転をセットしなければならない。
        """
        val = v
        if ws:
            mpath = self._mpath()
            if mpath.length() > 1:
                m = _MX(mpath.inclusiveMatrix()).setShear(v, _MSpace_kTransform).asMatrix()
                m *= mpath.exclusiveMatrixInverse()
                if mpath.hasFn(_MFn_kJoint):
                    findPlug = self.mfn_().findPlug
                    if findPlug('ssc', True).asBool():
                        s = mplug_get_nums(findPlug('is', True))
                        m *= _MM_makeS(s)
                val = _MX(m).shear(_MSpace_kTransform)

            elif mpath.hasFn(_MFn_kJoint):
                findPlug = self.mfn_().findPlug
                if findPlug('ssc', True).asBool():
                    s = mplug_get_nums(findPlug('is', True))
                    if s != _ONE3_LIST:
                        m = _MX(mpath.inclusiveMatrix()).setShear(v, _MSpace_kTransform).asMatrix()
                        m *= _MM_makeS(s)
                        val = _MX(m).shear(_MSpace_kTransform)
        else:
            self.checkValid()

        if get:
            return list(v) if v is val else val
        self.plug_('sh').set(val, safe=safe)

    setSh = setShearing  #: `setShearing` の別名。

    def setQuaternion(self, q, ws=False, ra=False, r=True, jo=True, safe=False, get=False):
        u"""
        ノードの回転のクォータニオンをセットする。

        デフォルトでは rotateAxis を含んでいない回転となり、
        マトリックスからの分解結果とは一致しないが、
        Maya の機能（Local Axis 表示やコンストレイン）が
        ノードの回転方向とする基準と一致する。

        ws=False の場合は、
        3種の回転アトリビュートのみから合成された値を意味し、
        :mayanode:`joint` ノードのローカルマトリックスには含まれる
        inverseScale の影響は無視される。

        セットするアトリビュートは通常は rotate だが、
        r=False の場合は、他のオプションによって
        jointOrient か rotateAxis になる。

        :type q: `.Quaternion`
        :param q: セットしたいクォータニオン。
        :param `bool` ws: ワールド空間でセットするかどうか。
        :param `bool` ra: rotateAxis を含んでいるかどうか。
        :param `bool` r: rotate を含んでいるかどうか。
        :param `bool` jo: jointOrient を含んでいるかどうか。
        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 のセットできる箇所だけセットされる。
        :param `bool` get:
            実際にはセットせず、
            セットされるべき rotate アトリビュート値だけ計算する。
        :rtype: `list` or None

        .. warning::
            以下のオプションの組み合わせはエラーになる。

            - ws=False, ra=True, r=False, jo=True
            - ws=True, jo=False
            - ws=True, ra=True, r=False
            - ws=True, r=False で joint ではない場合
        """
        mfn = self.mfn()
        findPlug = mfn.findPlug

        q = _MQ(q._Quaternion__data)
        ro = findPlug('ro', True).asShort()
        ra_q = None
        r_q = None

        if ws:
            mpath = self._mpath_()
            if not jo:
                raise ValueError('setQuaternion: unsupported option combination.')
            jo = mpath.hasFn(_MFn_kJoint)
            if not r and (ra or not jo):
                raise ValueError('setQuaternion: unsupported option combination.')

            if mpath.length() > 1:
                # r も ra も上位の非一様 scale の影響を受けてから取り除く。
                if not r:
                    v = mplug_get_nums(findPlug('r', True))
                    r_q = _ME(v, ro).asQuaternion()
                    q = r_q * q
                if not ra:
                    v = mplug_get_nums(findPlug('ra', True))
                    ra_q = _ME(v).asQuaternion()
                    q = ra_q * q

                m = q.asMatrix()
                m *= mpath.exclusiveMatrixInverse()
            else:
                m = None

            if jo and findPlug('ssc', True).asBool():
                s = mplug_get_nums(findPlug('is', True))
                if s != _ONE3_LIST:
                    if not m:
                        m = q.asMatrix()
                    m *= _MM_makeS(s)

            if m:
                q = _MQ().setValue(m.homogenize())

        else:
            if jo:
                jo = mfn.object().hasFn(_MFn_kJoint)
            if ra and not r and jo:
                raise ValueError('setQuaternion: unsupported option combination.')

        if ra_q:
            q = ra_q.conjugate() * q
        if r_q:
            q = r_q.conjugate() * q
        if r:
            if ra:
                v = mplug_get_nums(findPlug('ra', True))
                q = _ME(-v[0], -v[1], -v[2], ZYX).asQuaternion() * q
            if jo:
                v = mplug_get_nums(findPlug('jo', True))
                q *= _ME(-v[0], -v[1], -v[2], ZYX).asQuaternion()
            if ro:
                e = _ME(0., 0., 0., ro).setValue(q)
            else:
                e = q.asEulerRotation()
            name = 'r'
        else:
            name = 'jo' if jo else 'ra'
            e = q.asEulerRotation()

        if get:
            return list(e)
        self.plug_(name).set(e, safe=safe)

    setQ = setQuaternion  #: `setQuaternion` の別名。

    def setTranslation(self, v, ws=False, at=2, safe=False, get=False):
        u"""
        ノードの位置をセットする。

        デフォルトでは回転ピボットの位置を意味し、
        マトリックスからの分解結果とは一致しないが、
        Maya の機能（Local Axis 表示位置やコンストレイン）が
        ノードの位置とする基準と一致する。

        :param `sequence` v: セットしたい位置。
        :param `bool` ws: ワールド空間でセットするかどうか。
        :param `int` at:
            どのアトリビュートに相当する位置でセットするか。

            - 0 だとローカル原点（親の matrix 位置）。
            - 1 だと translate の位置。
            - 2 だと rotatePivot の位置。
            - 3 だと scalePivot の位置。
            - 4 以上だと matrix の位置。

        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 のセットできる箇所だけセットされる。
        :param `bool` get:
            実際にはセットせず、
            セットされるべき shear アトリビュート値だけ計算する。
        :rtype: `list` or None

        .. warning::
            at=4 の場合、
            `setScaling` 、 `setShearing` 、 `setQuaternion`
            の後で呼び出す必要がある。
            そうしないと、ピボットがローカル原点にない場合に
            それらによって位置が変わってしまう。
        """
        mpath = self._mpath()

        if ws and mpath.length() > 1:
            v = _MP(v)
            v *= mpath.exclusiveMatrixInverse()

        if at >= 3:
            mfn = self.mfn_()
            findPlug = mfn.findPlug
            attrs = {
                'ra': mplug_get_nums(findPlug('ra', True)),
                'rp': mplug_get_nums(findPlug('rp', True)),
                'rpt': mplug_get_nums(findPlug('rpt', True)),
            }
            if mpath.hasFn(_MFn_kJoint):
                attrs['ssc'] = findPlug('ssc', True).asBool()
                attrs['is'] = mplug_get_nums(findPlug('is', True))
                attrs['jo'] = mplug_get_nums(findPlug('jo', True))
            if at >= 4:
                attrs['sp'] = mplug_get_nums(findPlug('sp', True))
                attrs['spt'] = mplug_get_nums(findPlug('spt', True))
            else:
                attrs['spt'] = (
                    _MV(mplug_get_nums(findPlug('spt', True))) +
                    _MV(mplug_get_nums(findPlug('sp', True)))
                )

            m = mfn.transformationMatrix()
            _MM_setT(m, v)
            x = X(_newM(m), **attrs)
            v = x.t

        elif at >= 2:
            # -sp s sh sp spt -rp ra r jo | rp rpt -is t
            findPlug = self.mfn_().findPlug
            attrs = {
                'rpt': (
                    _MV(mplug_get_nums(findPlug('rpt', True))) +
                    _MV(mplug_get_nums(findPlug('rp', True)))
                ),
            }
            if mpath.hasFn(_MFn_kJoint):
                attrs['ssc'] = findPlug('ssc', True).asBool()
                attrs['is'] = mplug_get_nums(findPlug('is', True))

            x = X(_newM(_MM_makeT(v)), **attrs)
            v = x.t

        elif at < 1:
            v = _MV(v)
            v -= _MV(mplug_get_nums(self.mfn_().findPlug('t', True)))

        if get:
            return list(v)
        self.plug_('t').set(v, safe=safe)

    setT = setTranslation  #: `setTranslation` の別名。

    def setMatrix(self, m, ws=False, safe=False, get=False):
        u"""
        マトリックスをセットする。

        ws=True の場合は、
        `setQuaternion` の ra=True 、
        `setScaling` と `setShearing`
        そして `setTranslation` の at=4
        を順番に全て行った結果と一致する
        （Scaling と Shear の順序は問わないが、
        他はこの順序で行う必要がある）。

        ws=False の場合は、
        :mayanode:`joint` のセグメントスケール補正が効いていると、
        `setTranslation` 以外は一致しない。

        :type m: `.Matrix`
        :param m: セットしたいマトリックス。
        :param `bool` ws: ワールド空間でセットするかどうか。
        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 のセットできる箇所だけセットされる。
        :param `bool` get:
            実際にはセットせず、
            セットされるべきアトリビュート値だけ計算する。
        :rtype: `.Transformation` or None
        """
        mpath = self._mpath()

        if ws and mpath.length() > 1:
            m = _newM(m._Matrix__data * mpath.exclusiveMatrixInverse())

        findPlug = self.mfn_().findPlug
        attrs = {
            'ro': findPlug('ro', True).asShort(),
            'ra': mplug_get_nums(findPlug('ra', True)),
            'rp': mplug_get_nums(findPlug('rp', True)),
            'rpt': mplug_get_nums(findPlug('rpt', True)),
            'sp': mplug_get_nums(findPlug('sp', True)),
            'spt': mplug_get_nums(findPlug('spt', True)),
        }
        if mpath.hasFn(_MFn_kJoint):
            attrs['ssc'] = findPlug('ssc', True).asBool()
            attrs['is'] = mplug_get_nums(findPlug('is', True))
            attrs['jo'] = mplug_get_nums(findPlug('jo', True))

        x = X(m, **attrs)

        if get:
            x.r  # 結果を repr したときに r が見えるように評価。
            return x
        p_ = self.plug_
        p_('t').set(x.t, safe=safe)
        p_('r').set(x.r, safe=safe)
        p_('sh').set(x.sh, safe=safe)
        p_('s').set(x.s, safe=safe)

    setM = setMatrix  #: `setMatrix` の別名。

    def setTransformation(self, x, ws=False, safe=False, get=False):
        u"""
        トランスフォーメーションをセットする。

        ピボットや jointOrient などの修飾系アトリビュートも
        一通りセットされる。

        :mayanode:`joint` ノードと :mayanode:`transform` ノードの
        トランスフォーメーションのコピーで、
        相互に互換性の無いアトリビュートがある場合
        （ピボット系、segmentScaleCompensate、jointOrientなど）、
        マトリックスが一致するようにセットされる。

        :mayanode:`joint` ノードではピボット系アトリビュートは
        サポートされないものとして扱うが shear は利用する。

        :type x: `.Transformation`
        :param x: セットしたいトランスフォーメーション情報。
        :param `bool` ws: ワールド空間でセットするかどうか。
        :param `bool` safe:
            アトリビュートがロックされていているなどのために
            セットできない場合もエラーにならない。
            また、 double3 のセットできる箇所だけセットされる。
        :param `bool` get:
            実際にはセットせず、
            セットされるべきアトリビュート値だけ計算する。
        :rtype: `.Transformation` or None
        """
        mpath = self._mpath()
        isJoint = mpath.hasFn(_MFn_kJoint)

        # Transformation に Matrix を乗じることで、
        # ピボットなどの各基準位置もワールド空間で一致させる。
        x = x._Transformation__copy()
        if ws and mpath.length() > 1:
            x *= _newM(mpath.exclusiveMatrixInverse())
        m = x.m

        # ノードタイプによって修飾属性の有無や利用可否を合わせる。
        clear = x.clear
        if isJoint:
            clear('rp')
            clear('rpt')
            clear('sp')
            clear('spt')
            x.is_ = _newV(_MP(mplug_get_nums(self.mfn_().findPlug('is', True))))
        else:
            clear('jo')
            clear('ssc')
            clear('is')

        if get:
            x.m = m
            return x

        # 修飾属性をセットする。
        # 完全にセットできなかった場合は、その値を読み取る。
        p_ = self.plug_
        if isJoint:
            _fitXformQuatAttr(p_, x, 'jo')
            _fitXformAttr(p_, x, 'ssc')
        _fitXformAttr(p_, x, 'rp')
        _fitXformAttr(p_, x, 'rpt')
        _fitXformAttr(p_, x, 'sp')
        _fitXformAttr(p_, x, 'spt')
        _fitXformQuatAttr(p_, x, 'ra')
        _fitXformAttr(p_, x, 'ro')

        # マトリックスを分解し要素値をセットする。
        x.m = m
        p_('t').set(x.t, safe=safe)
        p_('r').set(x.r, safe=safe)
        p_('sh').set(x.sh, safe=safe)
        p_('s').set(x.s, safe=safe)

    setX = setTransformation  #: `setTransformation` の別名。


#------------------------------------------------------------------------------
def _fitXformAttr(p_, x, name):
    plug = p_(name)
    if plug.set(getattr(x, name), safe=True):
        setattr(x, name, plug.get())


def _fitXformQuatAttr(p_, xform, name):
    plug = p_(name)
    if plug.set(getattr(xform, name).asE(), safe=True):
        setattr(xform, name, plug.get())

