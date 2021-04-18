# -*- coding: utf-8 -*-
u"""
トランスフォーメーション情報クラス。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from ...common import *
from ...pyutils.immutables import OPTIONAL_MUTATOR_DICT as _MUTATOR_DICT
from .eulerrotation import E, ImmutableEulerRotation, _newE
from .matrix import M, ImmutableMatrix, _newM
from .quaternion import Q, ImmutableQuaternion, _newQ
from .vector import V, ImmutableVector, _newV
import maya.api.OpenMaya as _api2

__all__ = ['Transformation', 'X', 'ImmutableTransformation']

_newIE = partial(_newE, cls=ImmutableEulerRotation)
_newIM = partial(_newM, cls=ImmutableMatrix)
_newIQ = partial(_newQ, cls=ImmutableQuaternion)
_newIV = partial(_newV, cls=ImmutableVector)
del _newE, _newM, _newQ, _newV

_MP = _api2.MPoint
_MV = _api2.MVector
_MM = _api2.MMatrix
_ME = _api2.MEulerRotation
_MQ = _api2.MQuaternion
_MX = _api2.MTransformationMatrix
_MSpace_kTransform = _api2.MSpace.kTransform
_MP_Origin_isEquivalent = _MP.kOrigin.isEquivalent

_M_makeT = M.makeT
_M_makeS = M.makeS
_M_makeSh = M.makeSh
_M_makeInvS = M.makeInvS

_Q_Identity = Q.Identity
_E_Zero = E.Zero
_V_Zero = V.Zero
_V_One = V.One
_TOLERANCE = M.Tolerance


#------------------------------------------------------------------------------
class Transformation(object):
    u"""
    トランスフォーメーション情報クラス。

    Maya の matrix データ型アトリビュートには、
    マトリックスの値そのものの他に、
    トランスフォーメーション情報をストアすることができる。
    本クラスではそれに対応し、
    プラグがデータを持っていれば、
    このオブジェクトを直接 `~.Plug.get` することができる
    （持っている情報に応じて `.Matrix` や
    `Transformation` 、あるいは None が得られる）。
    また、このオブジェクトをプラグに直接 `~.Plug.set` することもできる。

    さらに、本クラスは、
    トランスフォーメーション要素をマトリックスに合成したり、
    マトリックスからトランスフォーメーション要素に分解したり
    する機能を備える。
    操作は、通常の python オブジェクトの属性アクセスを通して
    自動的に行われる。
    matrix や quaternion といった属性の他に、
    トランスフォーメーション要素としては、
    :mayanode:`transform` ノードの
    アトリビュートとそっくり同じ名前で対応した属性を備えている。

    各属性はロング名とショート名のどちらででもアクセス可能で、
    以下のものがある。
    それぞれ、ロング名に続くカッコはショート名と値の型を表す。

    * 基本トランスフォーメーション要素属性

      これらによってマトリックスを合成したり、
      マトリックスからこれらの値に分解することができる。

      - translate (t) (`.Vector`)
      - rotate (r) (`.EulerRotation`)
      - quaternion (q) (`.Quaternion`)
      - shear (sh) (`.Vector`)
      - scale (s) (`.Vector`)

      rotate と quaternion は同じ要素（rotate）を示すが、
      どちらの手段（形式）でもセットやゲットが可能。

    * トランスフォーメーション修飾属性

      基本トランスフォーメーション要素の働きを修飾する補助属性。

      マトリックスからこれらの値に直接分解することはできず、
      分解・合成するための補助属性という位置づけである。

      - rotateOrder (ro) (`int`)
      - segmentScaleCompensate (ssc) (`bool`)
      - inverseScale (is) (`.Vector`)
      - jointOrient (jo) (`.Quaternion`)
      - rotateAxis (ra) (`.Quaternion`)
      - rotatePivot (rp) (`.Vector`)
      - rotatePivotTranslate (rpt) (`.Vector`)
      - scalePivot (sp) (`.Vector`)
      - scalePivotTranslate (spt) (`.Vector`)

      rotateOrder は
      rotate (`.EulerRotation`)
      の order と同じものだが、任意の rotateOrder を設定して、
      そのオーダーの rotate を得る目的で使うことができる。

      jointOrient と rotateAxis のタイプが
      `.Quaternion`
      なのは、Maya のトランスフォーメーションマトリックスアトリビュートの
      仕様に準じているためである。

      inverseScale のショート名 ``is`` は、文字列にしないと python の
      ``is`` と衝突してしまうので、代わりに ``is_`` を使用することもできる。

    * マトリックス属性

      合成されたマトリックス値。

      - matrix (m) (`.Matrix`)

    各属性値は、自由に参照したり、セットしたりすることができるが、
    `.immutable` でラップされた変更不可な値となっている。
    つまり、それ自身を変更するメソッドを使用することはできない。
    たとえば ``r`` をリオーダーするには `.EulerRotation.reorderIt`
    を呼ぶとエラーになるので `.EulerRotation.reorder` で得たものを
    セットし直すか ``ro`` をセットする。

    基本トランスフォーメーション要素属性か
    トランスフォーメーション修飾属性をセットすると、
    マトリックス属性がクリアされ、
    その後、マトリックス値を読み取ろうとする際に合成の計算がされる。

    マトリックス属性をセットすると、
    基本トランスフォーメーション要素属性がクリアされ、
    その後、要素の値を読み取ろうとする際に分解の計算がされる。

    例えば、目的に応じて以下のようにマトリックスを分解できる。

    * ピボットや jointOrient などの設定に応じて
      マトリックスを分解するには、
      それらを一通りセットしてから m をセットし、
      t, r(q), sh, s の値を得る。

    * マトリックスを変えずに、一部の修飾属性を変更するには、
      m をゲットして退避しておき、
      変更する修飾属性をセットし、
      m をセットし直し、
      t, r(q), sh, s の値を得る。

    さらに、以下のような機能を備えている。

    * コンストラクタの引数には以下を0から1個指定できる。

      - `Transformation`
      - `.Matrix`
      - `.Quaternion`
      - `.EulerRotation`

    * コンストラクタのキーワード引数に、
      ロング名やショート名で属性値を指定できる。

    * 属性値をセットする際は、本来の型に合わせなくても、
      `.Plug` から `~.Plug_c.get` した値を
      そのままセットすることができる。
      例えば、rotateAxis 属性の型は
      `.Quaternion`
      だが Radians の 3値の `list` をセットしても、
      適切に Quaternion に変換される。

    * `Transformation` か `.Matrix`
      と乗算できる。

    * シーケンスとして評価すると
      matrix データ型アトリビュートへの
      :mayacmd:`setAttr` コマンドの形式になる。
    """
    __slots__ = ('__data',)
    __hash__ = None

    def __new__(cls, val=None, **kwargs):
        # 第1引数。
        if val:
            if hasattr(val, '_Transformation__data'):
                data = dict(val.__data)
                data.update(kwargs)
                kwargs = data
            elif hasattr(val, '_Matrix__data'):
                kwargs['m'] = val
                kwargs.pop('matrix', None)
            elif hasattr(val, '_Quaternion__data'):
                kwargs['q'] = val
                kwargs.pop('quaternion', None)
            elif hasattr(val, '_EulerRotation__data'):
                kwargs['r'] = val
                kwargs.pop('rotate', None)
            else:
                raise ValueError(cls.__name__ + ' : not matching constructor found.')

        # キーワード引数のショート名化とタイプラップ（変換か複製）。
        # サポートされていない属性はここで _TO_SHORTNAME によってエラーになる。
        data = dict([
            (_TO_SHORTNAME[k], _SRC_FILTER_DICT_get(k, _throgh)(v))
            for k, v in kwargs.items()])
        e = data.get('r')
        if e:
            ro = data.get('ro')
            #if ro is not None and e.order != ro:
            #    data['r'] = _newIE(e._EulerRotation__data.reorder(ro))
            if ro is not None:
                e._EulerRotation__data.order = ro

        # デフォルト値のトランスフォーメーション修飾属性は削除。
        return _newX(dict([kv for kv in data.items() if kv[1] != _MOD_ATTR_DICT_get(kv[0])]), cls)

    def __copy(self):
        return _newX(dict([
            kv for kv in [(k, _SRC_FILTER_DICT_get(k, _throgh)(v)) for k, v in self.__data.items()]
            if kv[1] != _MOD_ATTR_DICT_get(kv[0])
        ]), type(self))

    def __reduce__(self):
        return type(self), EMPTY_TUPLE, self.__data

    def __setstate__(self, state):
        _X_setdata(self, state)

    def __repr__(self):
        return type(self).__name__ + str(self)

    def __str__(self):
        dt = self.__data
        if 'm' in dt:
            _decomposeM(dt, 't')
            dt = dict(dt)
            del dt['m']
            if 'q' in dt and 'r' in dt:
                del dt['q']
        elif 'q' in dt and 'r' in dt:
            dt = dict(dt)
            del dt['q']
        return '(' + ', '.join(['%s=%r' % kv for kv in dt.items()]) + ')'

    def __eq__(self, other):
        try:
            for k in _ATTRS_TO_COMPARE:
                if getattr(self, k) != getattr(other, k):
                    return False
        except:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __getattr__(self, name):
        return _GETTER_DICT[name](self.__data)

    def __setattr__(self, name, val):
        _SETTER_DICT[name](self.__data, val)

    def __len__(self):
        return 14

    def __getitem__(self, i):
        return getattr(self, _SHORTNAMES[i]) if i else 'xform'

    def __mul__(self, v):
        if hasattr(v, '_Transformation__data'):
            v = v.m
        x = self.__copy()
        if not v.isIdentity():
            _multMatrix(x.__data, v._Matrix__data)
        return x

    def __imul__(self, v):
        if hasattr(v, '_Transformation__data'):
            v = v.m
        if not v.isIdentity():
            _multMatrix(self.__data, v._Matrix__data)
        return self

    def isEquivalent(self, v, tol=_TOLERANCE):
        u"""
        各属性値がほぼ同値かどうか。

        :param v:
            比較する値。
            `Transformation` か
            `.Matrix`
            を指定可能。
        :param `float` tol: 許容誤差。
        :rtype: `bool`
        """
        ssc = self.ssc
        try:
            if ssc == v.ssc:
                for k in (_ATTRS_TO_COMPARE_NO_SSC if ssc else _ATTRS_TO_COMPARE_NO_IS):
                    if not getattr(self, k).isEquivalent(getattr(v, k), tol):
                        return False
            return True
        except:
            return False

    def clear(self, name):
        u"""
        トランスフォーメーション修飾属性をクリアする。

        :param `str` name: トランスフォーメーション修飾属性名。
        """
        _CLEARER_DICT[name](self.__data)

    def hasValue(self, name):
        u"""
        デフォルト値ではない修飾属性の値を持っているかどうか。

        :param `str` name: トランスフォーメーション修飾属性名。
        :rtype: `bool`
        """
        return _TO_SHORTNAME[name] in self.__data

    def asPosition(self, at=2):
        u"""
        指定した基準位置を得る。

        :param `int` at:
            どのアトリビュートに相当する位置を得るか。

            - 0 だと原点（ゼロ）。
            - 1 だと translate の位置（属性値そのもの）。
            - 2 だと rotatePivot の位置。
            - 3 だと scalePivot の位置。
            - 4 以上だと matrix の位置。
        """
        if at < 1:
            return _V_Zero

        data = self.__data
        get = data.get

        if at >= 3:
            m = get('m')
            m = m._Matrix__data if m else _compute_api2_M(get)
            if at < 4:
                p = get('sp')
                if p:
                    return _newIV(p._Vector__data * m)
            return _newIV(_MP(m[12], m[13], m[14]))

        p = _MP(_decomposeM(data, 't'))

        if at >= 2:
            rp = get('rp')
            rpt = get('rpt')
            if rp:
                v = _MV(rp)
                if rpt:
                    v += _MV(rpt)
            elif rpt:
                v = _MV(rpt)
            else:
                v = None
            if v:
                if get('ssc', True):
                    s = get('is')
                    if s:
                        v *= _MM_makeInvS(s)
                p += v

        return _newIV(p)

    def getSetAttrCmds(self):
        u"""
        :mayacmd:`setAttr` コマンドの MEL 文字列リストを得る。

        コマンド構文のアトリビュート名の部分は "%s" となる。

        :rtype: `list`
        """
        return [
            'setAttr "%s" -type "matrix" "xform"',
            ' '.join([str(x) for x in getattr(self, 's')]),
            ' '.join([str(x) for x in getattr(self, 'r')]),
            str(getattr(self, 'ro')),
            ' '.join([str(x) for x in getattr(self, 't')]),
            ' '.join([str(x) for x in getattr(self, 'sh')]),
            ' '.join([str(x) for x in getattr(self, 'sp')]),
            ' '.join([str(x) for x in getattr(self, 'spt')]),
            ' '.join([str(x) for x in getattr(self, 'rp')]),
            ' '.join([str(x) for x in getattr(self, 'rpt')]),
            ' '.join([str(x) for x in getattr(self, 'ra')]),
            ' '.join([str(x) for x in getattr(self, 'jo')]),
            ' '.join([str(x) for x in getattr(self, 'is')]),
            ('yes' if getattr(self, 'ssc') else 'no'),
        ]

    @classmethod
    def fromSetAttrCmds(cls, lines):
        u"""
        :mayacmd:`setAttr` コマンドの MEL 文字列リストから生成する。
        """
        tkns = ' '.join(lines).split()[5:]
        p = tkns.pop
        kwargs = {'ssc': p() == 'yes;'}
        kwargs['is'] = [float(p()), float(p()), float(p())][::-1]
        kwargs['jo'] = [float(p()), float(p()), float(p()), float(p())][::-1]
        kwargs['ra'] = [float(p()), float(p()), float(p()), float(p())][::-1]
        kwargs['rpt'] = [float(p()), float(p()), float(p())][::-1]
        kwargs['rp'] = [float(p()), float(p()), float(p())][::-1]
        kwargs['spt'] = [float(p()), float(p()), float(p())][::-1]
        kwargs['sp'] = [float(p()), float(p()), float(p())][::-1]
        kwargs['sh'] = [float(p()), float(p()), float(p())][::-1]
        kwargs['t'] = [float(p()), float(p()), float(p())][::-1]
        kwargs['r'] = [int(p()), float(p()), float(p()), float(p())][::-1]
        kwargs['s'] = [float(p()), float(p()), float(p())][::-1]
        return cls(**kwargs)

X = Transformation  #: `Transformation` の別名。

_MUTATOR_DICT[X] = (
    'clear',
)
ImmutableTransformation = immutableType(X)  #: `Transformation` の `immutable` ラッパー。


def _newX(data, cls=X):
    obj = _object_new(cls)
    _X_setdata(obj, data)
    return obj
_object_new = object.__new__

_X_setdata = X._Transformation__data.__set__


#------------------------------------------------------------------------------
_ATTR_NAMES = (
    ('m', 'matrix'),

    ('s', 'scale'),
    ('r', 'rotate'),
    ('ro', 'rotateOrder'),
    ('t', 'translate'),
    ('sh', 'shear'),

    ('sp', 'scalePivot'),
    ('spt', 'scalePivotTranslate'),
    ('rp', 'rotatePivot'),
    ('rpt', 'rotatePivotTranslate'),

    ('ra', 'rotateAxis'),
    ('jo', 'jointOrient'),

    ('is', 'inverseScale'),
    ('ssc', 'segmentScaleCompensate'),

    ('q', 'quaternion'),
)  #: アトリビュート名テーブル。_SHORTNAMES のために順番が重要。
_SHORTNAMES = [x[0] for x in _ATTR_NAMES][:-1]  #: data の setAttr に指定する順のアトリビュート名。

_TO_SHORTNAME = dict([x[::-1] for x in _ATTR_NAMES])
_TO_SHORTNAME['is_'] = 'is'
_TO_SHORTNAME.update([(x, x) for x, y in _ATTR_NAMES])

_TO_LONGNAME = dict(_ATTR_NAMES)
_TO_LONGNAME['is_'] = _TO_LONGNAME['is']

y = ('m', 'q', 'ro')
_ATTRS_TO_COMPARE = tuple([x for x in _SHORTNAMES if x not in y])
_ATTRS_TO_COMPARE_NO_SSC = tuple([x for x in _ATTRS_TO_COMPARE if x != 'ssc'])
_ATTRS_TO_COMPARE_NO_IS = tuple([x for x in _ATTRS_TO_COMPARE_NO_SSC if x != 'is'])


def _inputQ(v):
    return _newIQ(_ME(v).asQuaternion()) if len(v) is 3 else ImmutableQuaternion(v)

_SRC_FILTER_DICT = {
    'm': ImmutableMatrix,

    't': ImmutableVector,
    'q': _inputQ,
    'r': ImmutableEulerRotation,
    'sh': ImmutableVector,
    's': ImmutableVector,

    #'ro': int,

    #'ssc': bool,
    'is': ImmutableVector,
    'jo': _inputQ,
    'ra': _inputQ,
    'rp': ImmutableVector,
    'rpt': ImmutableVector,
    'sp': ImmutableVector,
    'spt': ImmutableVector,
}  #: 属性セット時のフィルタ。
_SRC_FILTER_DICT.update([
    (_TO_LONGNAME[x], y) for x, y in _SRC_FILTER_DICT.items()])
_SRC_FILTER_DICT['is_'] = _SRC_FILTER_DICT['is']
_SRC_FILTER_DICT_get = _SRC_FILTER_DICT.get

_MOD_ATTR_DICT = {
    'ssc': True,
    'is': _V_One,
    'jo': _Q_Identity,
    'ra': _Q_Identity,
    'rp': _V_Zero,
    'rpt': _V_Zero,
    'sp': _V_Zero,
    'spt': _V_Zero,
}  #: 修飾属性のデフォルト辞書。
_MOD_ATTR_DICT_get = _MOD_ATTR_DICT.get


#------------------------------------------------------------------------------
def _throgh(v):
    return v


#def _setMulD3(a, b):
#    a[0] *= b[0]
#    a[1] *= b[1]
#    a[2] *= b[2]


#def _setDivD3(a, b):
#    a[0] /= b[0]
#    a[1] /= b[1]
#    a[2] /= b[2]


def _MM_3x3(m):
    u"""
    3x3部分以外を初期化した API2 の MMatrix を得る。
    """
    return _MM([
        m[0], m[1], m[2], 0.,
        m[4], m[5], m[6], 0.,
        m[8], m[9], m[10], 0.,
        0., 0., 0., 1.,
    ])


def _MM_makeS(v):
    u"""
    scale 行列を API2 の MMatrix で得る。
    """
    return _MM([
        v[0], 0., 0., 0.,
        0., v[1], 0., 0.,
        0., 0., v[2], 0.,
        0., 0., 0., 1.,
    ])


def _MM_makeInvS(v):
    u"""
    scale 逆行列を API2 の MMatrix で得る。
    """
    return _MM([
        1. / v[0], 0., 0., 0.,
        0., 1. / v[1], 0., 0.,
        0., 0., 1. / v[2], 0.,
        0., 0., 0., 1.,
    ])


def _MM_makeSh(v):
    u"""
    shear 行列を API2 の MMatrix で得る。
    """
    return _MM([
        1., 0., 0., 0.,
        v[0], 1., 0., 0.,
        v[1], v[2], 1., 0.,
        0., 0., 0., 1.,
    ])


def _MM_makeT(v):
    u"""
    translate 行列を API2 の MMatrix で得る。
    """
    return _MM([
        1., 0., 0., 0.,
        0., 1., 0., 0.,
        0., 0., 1., 0.,
        v[0], v[1], v[2], 1.,
    ])


def _MM_setT(m, v):
    u"""
    API2 の MMatrix の translate をセットする。
    """
    # Fix DoubleAccessorBug
    m += _MM((
        0., 0., 0., 0.,
        0., 0., 0., 0.,
        0., 0., 0., 0.,
        v[0] - m[12], v[1] - m[13], v[2] - m[14], 0.,
    ))


#------------------------------------------------------------------------------
def _multMatrix(data, pm):
    u"""
    マトリックスを乗じつつ spt と rpt を必要に応じて調整して、rp と t の位置も正確に変換する。

    m と sp の位置は何もしなくても合う。
    """
    get = data.get

    # 現在のマトリックス。
    m = get('m')
    m = _MM(m._Matrix__data) if m else _compute_api2_M(get)

    # 維持したい現在の local translate 位置。
    sp, spt_rp, rp_offset, sscm, sscim = _prepareTo_compute_api2_T(get)
    last_t = _compute_api2_T(m, sp, spt_rp, rp_offset, sscm, sscim)[0]
    #last_t = _MP(_decomposeM(data, 't'))

    # 現在のマトリックスに指定されたマトリックスを乗じる。
    m *= pm
    mat = _newIM(m)
    #_clearElemAttrs(data)
    #data['m'] = mat

    # マトリックスを乗じた後の仮の local translate 位置。
    cur_t, rim = _compute_api2_T(m, sp, spt_rp, rp_offset, sscm, sscim)
    #cur_t = _MP(_decomposeM(data, 't'))

    # spt を調整して rotatePivot 位置を合わせる。matrix を維持すれば scalePivot 位置はずれない。
    if rp_offset:
        last_rp = last_t + rp_offset
        cur_rp = cur_t + rp_offset
        v = _MV(last_rp * pm - cur_rp)
        cur_t += v  # ここでの調整による影響を考慮。

        v *= rim
        spt = get('spt')
        if spt:
            spt = spt._Vector__data - v
        else:
            spt = _MP(-v[0], -v[1], -v[2])
        if _MP_Origin_isEquivalent(spt):
            data.pop('spt', None)
        else:
            data['spt'] = _newIV(spt)

    # rpt を調整して translate 位置を合わせる。matrix を維持すれば rotatePivot 位置はずれない。
    v = _MV(last_t * pm - cur_t)
    if sscim:
        v *= sscim
    rpt = get('rpt')
    if rpt:
        rpt = rpt._Vector__data - v
    else:
        rpt = _MP(-v[0], -v[1], -v[2])
    if _MP_Origin_isEquivalent(rpt):
        data.pop('rpt', None)
    else:
        data['rpt'] = _newIV(rpt)

    # matrix を維持。
    _clearElemAttrs(data)
    data['m'] = mat


def _prepareTo_compute_api2_T(get):
    u"""
    補助属性から _compute_api2_T のための情報を事前に計算する。
    """
    # ssc
    ssc = get('ssc', True) and get('is')
    if ssc:
        sscm = _MM_makeInvS(ssc)
        sscim = _MM_makeS(ssc)
    else:
        sscm = None
        sscim = None

    # rp_offset = rotatePivot位置 - t
    rp = get('rp')
    rpt = get('rpt')
    if rp:
        rp = _MV(rp)
        if rpt:
            rpt = _MV(rpt)
            rp_offset = rp + rpt
        else:
            rp_offset = _MV(rp)
        if ssc:
            rp_offset *= sscm
    elif rpt:
        rpt = _MV(rpt)
        rp_offset = _MV(rpt)
        if ssc:
            rp_offset *= sscm
    else:
        rp_offset = None

    # spt - rp
    spt_rp = get('spt')
    if spt_rp:
        spt_rp = _MV(spt_rp)
        if rp:
            spt_rp -= rp
    elif rp:
        spt_rp = -rp

    # sp
    sp = get('sp')
    if sp:
        sp = _MV(sp)

    return sp, spt_rp, rp_offset, sscm, sscim


def _compute_api2_T(m, sp, spt_rp, rp_offset, sscm, sscim):
    u"""
    マトリックスと補助属性から t を計算する。

    _decomposeM でも計算できるが、大がかかりなので。
    """
    t = _MP(m[12], m[13], m[14])

    if sp or spt_rp or rp_offset:
        if sscm:
            hm = _MM_3x3(m * sscim).homogenize()
            rm = hm * sscm
            rim = sscim * hm.transpose()
        else:
            hm = _MM_3x3(m).homogenize()
            rm = hm
            rim = hm.transpose()

        if sp:
            offset = sp - sp * (m * rim)
            if spt_rp:
                offset += spt_rp
            offset *= rm
            t -= offset
        elif spt_rp:
            t -= spt_rp * rm

        if rp_offset:
            t -= rp_offset

        return t, rim
    else:
        return t, None


#------------------------------------------------------------------------------
def _decomposeM(data, name):
    u"""
    指定要素属性値を得る。未評価ならマトリックスを分解する。

    指定属性もマトリックス属性も設定されていなければ None が返される。
    """
    get = data.get

    # 指定属性値が存在すればそれを返す。
    val = get(name)
    if val:
        return val

    # マトリックス属性を得る。存在しなければ None を返す。
    m = get('m')
    if not m:
        return
    m = m._Matrix__data

    # -sp s sh sp spt -rp ra r jo rp rpt -is t

    # ssc の inverseScale 考慮した後 s, sh, q を分解。
    ssc = get('ssc', True) and get('is')
    if ssc:
        ssc = _MM_makeS(ssc)
        xm = _MX(m * ssc)
    else:
        xm = _MX(m)

    s = xm.scale(_MSpace_kTransform)
    data['s'] = _newIV(_MP(s))

    sh = xm.shear(_MSpace_kTransform)
    data['sh'] = _newIV(_MP(sh))

    q = xm.rotation(True)

    # ピボットに scalePivot を考慮。
    sp = get('sp')
    if sp:
        sm = _MM_makeS(s)
        sm *= _MM_makeSh(sh)
        pv = _MV(sp)
        pv -= pv * sm
    else:
        pv = _MV()

    # ピボットに scalePivotTranslate を考慮。
    spt = get('spt')
    if spt:
        pv += _MV(spt)

    # ピボットに rotatePivot を考慮。
    rp = get('rp')
    if rp:
        rp = _MV(rp)
        pv -= rp
        pv = pv.rotateBy(q)
        pv += rp
    else:
        pv = pv.rotateBy(q)

    # ピボットに rotatePivotTranslate を考慮。
    rpt = get('rpt')
    if rpt:
        pv += _MV(rpt)

    # ピボットに ssc を考慮。
    if ssc:
        pv[0] /= ssc[0]
        pv[1] /= ssc[5]
        pv[2] /= ssc[10]

    # ピボットによる効果を差し引いて translate を分解。
    t = _MP(m[12], m[13], m[14])  # ssc 無視した値。
    t -= pv
    data['t'] = _newIV(t)

    # quaternion (rotate) を分解。
    ra = get('ra')
    if ra:
        q = ra._Quaternion__data.conjugate() * q
    jo = get('jo')
    if jo:
        q *= jo._Quaternion__data.conjugate()
    data['q'] = _newIQ(q)

    return data[name]


#------------------------------------------------------------------------------
def _getM(data):
    u"""
    matrix 属性値を得るか、要素から合成する。
    """
    get = data.get
    m = get('m')
    if not m:
        m = _newIM(_compute_api2_M(get))
        data['m'] = m
    return m


def _compute_api2_M(get):
    u"""
    トランスフォーメーション属性から MMatrix を計算する。
    """
    # -sp s sh sp spt -rp ra r jo rp rpt -is t

    # scale と shear を計算。
    s = get('s')
    sh = get('sh')
    if s:
        m = _MM_makeS(s)
        if sh:
            m *= _MM_makeSh(sh)
    elif sh:
        m = _MM_makeSh(sh)
    else:
        m = None

    # ピボットに scalePivot を考慮。
    sp = m and get('sp')
    if sp:
        trn = _MV(sp)
        trn -= trn * m
    else:
        trn = _MV()

    # ピボットに scalePivotTranslate を考慮。
    spt = get('spt')
    if spt:
        trn += _MV(spt)

    # rotate を計算。
    q = get('q')
    if q:
        q = _MQ(q)
    else:
        e = get('r')
        q = e and e._EulerRotation__data.asQuaternion()

    ra = get('ra')
    if ra:
        if q:
            q = ra._Quaternion__data * q
        else:
            q = _MQ(ra)

    jo = get('jo')
    if jo:
        if q:
            q *= jo._Quaternion__data
        else:
            q = _MQ(jo)

    if q:
        if m:
            m *= q.asMatrix()
        else:
            m = q.asMatrix()

    # ピボットに rotatePivot を考慮。
        rp = get('rp')
        if rp:
            rp = _MV(rp)
            trn -= rp
            trn = trn.rotateBy(q)
            trn += rp
        else:
            trn = trn.rotateBy(q)

    # ピボットに rotatePivotTranslate を考慮。
    rpt = get('rpt')
    if rpt:
        trn += _MV(rpt)

    # ssc を計算。
    ssc = get('ssc', True) and get('is')
    if ssc:
        sx = 1. / ssc[0]
        sy = 1. / ssc[1]
        sz = 1. / ssc[2]
        trn[0] *= sx
        trn[1] *= sy
        trn[2] *= sz
        if m:
            m *= _MM_makeS((sx, sy, sz))
        else:
            m = _MM_makeS((sx, sy, sz))

    # translate を計算。
    t = get('t')
    if t:
        trn = t._Vector__data + trn
    if m:
        _MM_setT(m, trn)
    else:
        m = _MM_makeT(trn)

    return m


def _getQ(data):
    u"""
    quaternion 属性値を得るか、マトリックスから分解する。
    """
    q = data.get('q')
    if q:
        return q

    e = data.get('r')
    if e:
        q = _newIQ(e._EulerRotation__data.asQuaternion())
    else:
        q = _decomposeM(data, 'q') or _Q_Identity
    data['q'] = q
    return q


def _getR(data):
    u"""
    rotate 属性値を得るか、マトリックスから分解する。
    """
    e = data.get('r')
    if e:
        return e

    ro = data.pop('ro', XYZ)  # r に持たせるので ro は削除。
    q = _decomposeM(data, 'q')
    if q:
        if ro == XYZ:
            e = _newIE(q._Quaternion__data.asEulerRotation())
        else:
            e = _ME(0., 0., 0., ro)
            e.setValue(q._Quaternion__data)
            e = _newIE(e)
    else:
        if ro == XYZ:
            return _E_Zero
        e = _newIE(_ME(0., 0., 0., ro))
    data['r'] = e
    return e


def _getT(data):
    u"""
    translate 属性値を得るか、マトリックスから分解する。
    """
    return _decomposeM(data, 't') or _V_Zero


def _getS(data):
    u"""
    scale 属性値を得るか、マトリックスから分解する。
    """
    return _decomposeM(data, 's') or _V_One


def _getSh(data):
    u"""
    shear 属性値を得るか、マトリックスから分解する。
    """
    return _decomposeM(data, 'sh') or _V_Zero


def _getRO(data):
    u"""
    rotateOrder 属性値を得る。
    """
    e = data.get('r')
    if e:
        return e.order
    return data.get('ro', XYZ)


_GETTER_DICT = {
    'm': _getM,

    't': _getT,
    'q': _getQ,
    'r': _getR,
    'sh': _getSh,
    's': _getS,

    'ro': _getRO,

    'ssc': lambda d: d.get('ssc', True),
    'is': lambda d: d.get('spt', _V_One),
    'jo': lambda d: d.get('jo', _Q_Identity),
    'ra': lambda d: d.get('ra', _Q_Identity),
    'rp': lambda d: d.get('rp', _V_Zero),
    'rpt': lambda d: d.get('rpt', _V_Zero),
    'sp': lambda d: d.get('sp', _V_Zero),
    'spt': lambda d: d.get('spt', _V_Zero),
}
_GETTER_DICT.update([
    (_TO_LONGNAME[x], y) for x, y in _GETTER_DICT.items()])
_GETTER_DICT['is_'] = _GETTER_DICT['is']


#------------------------------------------------------------------------------
def _makeSetElemProc(name, default):
    u"""
    基本トランスフォーメーション要素属性のセット処理（quaternion と rotate は除く）。
    """
    def setter(data, v):
        v = cls(v)
        if not (_decomposeM(data, name) or default).isEquivalent(v):
            data.pop('m', None)
        data[name] = v
    cls = type(default)
    return setter


def _setQ(data, v):
    u"""
    quaternion 属性のセット処理。
    """
    v = _inputQ(v)
    if not (_decomposeM(data, 'q') or _Q_Identity).isEquivalent(v):
        data.pop('m', None)
        r = data.pop('r', None)
        if r and r.order:
            data['ro'] = r.order
    data['q'] = v


def _setR(data, v):
    u"""
    rotate 属性のセット処理。
    """
    v = ImmutableEulerRotation(v)
    if not (_decomposeM(data, 'q') or _Q_Identity).isEquivalent(v.asQ()):
        data.pop('m', None)
        data.pop('q', None)
    data['r'] = v


def _setM(data, v):
    u"""
    matrix 属性のセット処理。
    """
    v = ImmutableMatrix(v)
    m = data.get('m')
    if not(m and m.isEquivalent(v)):
        _clearElemAttrs(data)
    data['m'] = v


def _clearElemAttrs(data):
    pop = data.pop
    pop('t', None)
    pop('q', None)
    pop('sh', None)
    pop('s', None)
    r = pop('r', None)
    if r and r.order:
        data['ro'] = r.order


def _makeSetAttrProc(name):
    u"""
    トランスフォーメーション修飾属性のセット処理。
    """
    default = _MOD_ATTR_DICT[name]
    toVal = _SRC_FILTER_DICT_get(name)
    if toVal:
        default_isEquivalent = default.isEquivalent
        isEquivalent = lambda a, b: a.isEquivalent(b)
    else:
        toVal = _throgh
        default_isEquivalent = lambda v: default == v
        isEquivalent = lambda a, b: a == b

    def setter(data, v):
        v = toVal(v)
        val = data.get(name)
        if val is None:
            # 値を持っておらず、セットされる値もデフォルト値ならスルーする。
            if default_isEquivalent(v):
                return
            data[name] = v
        else:
            # セットする値が今の値と同じならスルーする。
            if isEquivalent(val, v):
                return
            if default_isEquivalent(v):
                del data[name]
            else:
                data[name] = v
        data.pop('m', None)

    return setter


def _setRO(data, v=XYZ):
    u"""
    rotateOrder 属性のセット処理。
    """
    e = data.get('r')
    if e:
        if e.order != v:
            data['r'] = _newIE(e._EulerRotation__data.reorder(v))
    elif v == XYZ:
        data.pop('ro', None)
    else:
        data['ro'] = v

# m がセットされたら、要素属性クリア。
# 要素属性セットされたら、他の要素を評価してから m をクリア。
# 修飾属性がセットされたら、m をクリア。

_SETTER_DICT = {
    'm': _setM,

    't': _makeSetElemProc('t', _V_Zero),
    'q': _setQ,
    'r': _setR,
    'sh': _makeSetElemProc('sh', _V_Zero),
    's': _makeSetElemProc('s', _V_One),

    'ro': _setRO,

    'ssc': _makeSetAttrProc('ssc'),
    'is': _makeSetAttrProc('is'),
    'jo': _makeSetAttrProc('jo'),
    'ra': _makeSetAttrProc('ra'),
    'rp': _makeSetAttrProc('rp'),
    'rpt': _makeSetAttrProc('rpt'),
    'sp': _makeSetAttrProc('sp'),
    'spt': _makeSetAttrProc('spt'),
}
_SETTER_DICT.update([
    (_TO_LONGNAME[x], y) for x, y in _SETTER_DICT.items()])
_SETTER_DICT['is_'] = _SETTER_DICT['is']


#------------------------------------------------------------------------------
def _makeClearAttrProc(name):
    u"""
    トランスフォーメーション修飾属性のクリア処理。
    """
    def clearer(data):
        if data.pop(name, None) is not None:
             data.pop('m', None)
    return clearer

_CLEARER_DICT = {
    'ro': _setRO,
    'ssc': _makeClearAttrProc('ssc'),
    'is': _makeClearAttrProc('is'),
    'jo': _makeClearAttrProc('jo'),
    'ra': _makeClearAttrProc('ra'),
    'rp': _makeClearAttrProc('rp'),
    'rpt': _makeClearAttrProc('rpt'),
    'sp': _makeClearAttrProc('sp'),
    'spt': _makeClearAttrProc('spt'),
}
_CLEARER_DICT.update([
    (_TO_LONGNAME[x], y) for x, y in _CLEARER_DICT.items()])
_CLEARER_DICT['is_'] = _CLEARER_DICT['is']

if IS_PYTHON2:
    del x, y

