# -*- coding: utf-8 -*-
u"""
Mayaバージョンによるノードタイプ名変更のサポート。

新旧バージョン互換のために、そのバージョンでの正しい名前を得ることができる。

唯一のインスタンス `compat_nodetype_map` の属性アクセスという形で、
Mayaノードタイプ名を指定することで、正しい名前の文字列を得られる。

* 基本的には、変更後の新しい名前から、そのバージョンでの正しい名前を得られる

* ノードタイプ名が変更され、元の名前が別のノードに置き換えられたものを指定すると、
  新旧互換性が無いという意味で `AttributeError` となる

* 振る舞いの一貫性は欠くものの、
  ノードタイプ名が変更され、元の名前が廃止されたものを指定すると、
  新しい正しい名前を得られる。

* 上記いずれにも当てはまらない場合は、指定したものがそのまま得られる。
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from .common import Singleton, with_metaclass
import maya.OpenMaya as _api1

__all__ = ['compat_nodetype_map']

try:
    _IS_2026_OR_LATER = _api1.MGlobal.apiVersion() >= 20260000
except:
    _IS_2026_OR_LATER = False

#------------------------------------------------------------------------------
# NOTE: 2026 では多くの汎用ノードの doubleLinear 型が double 型となり、ノードタイプ名に DL が付けられた。
# - 元のノードタイプ名の多くは double 版として存続している。
# - 元のノードタイプ名で廃止されたものは以下の3点。
#   - addDoubleLinear -> addDL になり add が追加された
#   - multDoubleLinear -> multDL になり mult が追加された
#   - pointMatrixMult -> pointMatrixMultDL になり double 版は追加されなかった
#
MAYA2026_DL_TO_OLD = {
    'absoluteDL': 'absolute',
    'acosDL': 'acos',
    'addDL': 'addDoubleLinear',
    'angleBetweenDL': 'angleBetween',
    'asinDL': 'asin',
    'atan2DL': 'atan2',
    'atanDL': 'atan',
    'averageDL': 'average',
    'axisFromMatrixDL': 'axisFromMatrix',
    'ceilDL': 'ceil',
    'clampRangeDL': 'clampRange',
    'columnFromMatrixDL': 'columnFromMatrix',
    'cosDL': 'cos',
    'crossProductDL': 'crossProduct',
    'determinantDL': 'determinant',
    'distanceBetweenDL': 'distanceBetween',
    'divideDL': 'divide',
    'dotProductDL': 'dotProduct',
    'equalDL': 'equal',
    'floorDL': 'floor',
    'greaterThanDL': 'greaterThan',
    'inverseLerpDL': 'inverseLerp',
    'lengthDL': 'length',
    'lerpDL': 'lerp',
    'lessThanDL': 'lessThan',
    'logDL': 'log',
    'maxDL': 'max',
    'minDL': 'min',
    'moduloDL': 'modulo',
    'multDL': 'multDoubleLinear',
    'multiplyDL': 'multiply',
    'multiplyPointByMatrixDL': 'multiplyPointByMatrix',
    'multiplyVectorByMatrixDL': 'multiplyVectorByMatrix',
    'negateDL': 'negate',
    'normalizeDL': 'normalize',
    'pointMatrixMultDL': 'pointMatrixMult',
    'powerDL': 'power',
    'rotateVectorDL': 'rotateVector',
    'roundDL': 'round',
    'rowFromMatrixDL': 'rowFromMatrix',
    'scaleFromMatrixDL': 'scaleFromMatrix',
    'sinDL': 'sin',
    'smoothStepDL': 'smoothStep',
    'subtractDL': 'subtract',
    'sumDL': 'sum',
    'tanDL': 'tan',
    'translationFromMatrixDL': 'translationFromMatrix',
    'truncateDL': 'truncate',
}  #: Maya 2026 の DL ノードタイプ名から旧タイプ名への辞書。

MAYA2026_DELETED_TYPENAMES = frozenset([
    'addDoubleLinear',
    'multDoubleLinear',
    'pointMatrixMult',
])  #: Maya 2026 で廃止されたノードタイプ名のセット。


if _IS_2026_OR_LATER:
    # 互換性のあるタイプ名を得るための辞書。互換性が得られない名前は None になる。
    _compatDict = dict([
        (v, k) if v in MAYA2026_DELETED_TYPENAMES else (v, None)
        for k, v in MAYA2026_DL_TO_OLD.items()
    ])  # old -> (new or None)

    # 正しいタイプ名を得るための辞書。
    _correctDict = dict([(v, _compatDict[v]) for v in MAYA2026_DELETED_TYPENAMES])  # deleted old -> new

    # 将来の変更後の名前を得る。
    _futureName = _correctDict.get

else:
    # 互換性のあるタイプ名を得るための辞書。互換性が得られない名前は None になる。
    _compatDict = dict(MAYA2026_DL_TO_OLD)  # new -> old
    _compatDict.update(dict([(v, None) for v in _compatDict.values() if v not in MAYA2026_DELETED_TYPENAMES]))  # 非互換名 -> None

    # 正しいタイプ名を得るための辞書。
    _correctDict = _compatDict

    # 将来の変更後の名前を得る。
    _futureName = dict([kv[::-1] for kv in MAYA2026_DL_TO_OLD.items()]).get  # old -> new

_compatDict_get = _compatDict.get
_correctDict_get = _correctDict.get


#------------------------------------------------------------------------------
class CompatNodeTypeMap(with_metaclass(Singleton, object)):
    u"""
    Mayaバージョンによるノードタイプ名変更に伴う新旧バージョン互換性確保のための名前変換器。

    唯一のインスタンス `compat_nodetype_map` を生成済み。
    """
    def __getattr__(self, name):
        u"""
        新旧バージョン互換のための正しい名前を得る。

        旧バージョンでは存在しないもの（同名でも意味が変わってしまうものも含まれる）
        を指定すると、互換性が無いものとして、
        新旧バージョンいずれの場合も `AttributeError` になる。
        

        :param `str` name: ノードタイプ名。
        :rtype: `str`
        """
        x = _compatDict_get(name, name)
        if x is None:
            raise AttributeError('Not compatible node type name between old and new versions: %s (use %s instead)' % (name, _futureName(name)))
        setattr(self, name, x)
        return x

    def correctName(self, name):
        u"""
        正しい名前に補正する。

        `getattr` ではエラーになる
        旧バージョンでは存在しないもの（同名でも意味が変わってしまうものも含まれる）
        を指定しても、それが存在する新バージョンではエラーにならず、
        旧バージョンでは None が返される。

        :param `str` name: ノードタイプ名。
        :rtype: `str` or `None`
        """
        return _correctDict_get(name, name)

    def futureName(self, name):
        u"""
        将来の変更後の名前を得る。

        :param `str` name: ノードタイプ名。
        :rtype: `str`
        """
        return _futureName(name, name)

compat_nodetype_map = CompatNodeTypeMap()  #: `CompatNodeTypeMap` の唯一のインスタンス。

