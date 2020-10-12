# -*- coding: utf-8 -*-
u"""
`.CyObject` の参照が切れていても再取得が可能な弱参照ラッパー。
"""
from ...common import *
from .cyobject import CyObject, _decideNodeClsFromData
from weakref import ref as _wref

__all__ = ['ObjectRef']


#------------------------------------------------------------------------------
class ObjectRef(CyObject):
    u"""
    `.CyObject` の参照が切れていても再取得が可能な弱参照ラッパー。

    これ自身も `.CyObject` であるため、参照先を得ずとも、
    基底でサポートする範囲でオリジナルのようにも振る舞える。
    """
    __slots__ = ('__data',)

    CLASS_TYPE = -1  #: ラッパークラスの種類が `ObjectRef` であることを表す。

    def __call__(self):
        return self.__data['wref']() or self._newobject()

    @classmethod
    def newObject(cls, data):
        u"""
        内部データとともにインスタンスを生成する。

        内部データはブラックボックスであるものとし、
        本メソッドをオーバーライドする場合も、
        基底メソッドを呼び出して処理を完遂させなければならない。

        内部データを拡張する場合は `internalData` も
        オーバーライドすること。

        :type cls: `type`
        :param cls: 生成するインスタンスのクラス。
        :param data: インスタンスにセットする内部データ。
        :rtype: 指定クラス
        """
        core = data.get('DATA')
        dt = core.get('DATA')
        while dt:
            core = dt
            dt = core.get('DATA')
        obj = super(ObjectRef, cls).newObject(core)
        obj.__data = data
        return obj

    def internalData(self):
        u"""
        内部データを返す。

        派生クラスで内部データを拡張する場合にオーバーライドする。
        その場合、 `newObject` クラスメソッドもオーバーライドし、
        拡張に対応させる。

        内部データはブラックボックスであるものとし、
        拡張データでは基底のデータも内包させる必要がある。
        """
        return self.__data

    def refdata(self):
        u"""
        ラップしているオブジェクトの内部データを得る。
        """
        return self.__data['DATA']

    def refclass(self):
        u"""
        ラップしているオブジェクトのクラスを得る。
        """
        if not self.__data['cls']:
            self.__data['cls'] = _decideNodeClsFromData(self.__data['DATA'])
        return self.__data['cls']

    def object(self):
        u"""
        弱参照が切れていなければオブジェクトを得る。

        :rtype: `.CyObject`
        """
        return self.__data['wref']()

    def weakref(self):
        u"""
        弱参照を得る。

        :rtype: `weakref.ref`
        """
        return self.__data['wref']

    def _newobject(self):
        u"""
        内部データから新しいオブジェクトを復元する。

        `__call__` が実装されているため、
        通常はただオブジェクトを呼び出す方が良い。

        こちらのメソッドでは、
        弱参照が切れているかどうかのチェックはしないので、
        先に `object` の戻り値をチェックしてから利用する。

        :rtype: `.CyObject`
        """
        obj = self.refclass().newObject(self.__data['DATA'])
        obj._CyObject__ref = self
        self.__data['wref'] = _wref(obj)
        return obj

    def node(self):
        u"""
        ノードを得る。

        :rtype: `.Node` 派生クラス
        """
        noderef = self._CyObject__data.get('noderef')
        if noderef:
            return noderef()

        if 'mnode' in self._CyObject__data:
            obj = self()
            while obj.CLASS_TYPE is -1:
                obj = obj()
            return obj


#------------------------------------------------------------------------------
def _getObjectRef(src, cls=ObjectRef):
    u"""
    任意の `.CyObject` 派生インスタンスをラップした `ObjectRef` を得る。
    """
    ref = src._CyObject__ref
    if ref is None or type(ref) is not cls:
        ref = cls.newObject({
            'DATA': src.internalData(),
            'wref': _wref(src),
            'cls': type(src),
        })
        src._CyObject__ref = ref
    return ref


def _newNodeRefFromData(data, cls=ObjectRef):
    u"""
    `.Node` 内部データから `ObjectRef` を生成する。
    """
    return cls.newObject({
        'DATA': data,
        'wref': donothing,
        'cls': None,
    })


def _newPlugRefFromData(data, cls=ObjectRef):
    u"""
    `.Plug` 内部データから `ObjectRef` を生成する。
    """
    return cls.newObject({
        'DATA': data,
        'wref': donothing,
        'cls': data['noderef']._CyObject__data['plugcls'] or CyObject._CyObject__glbpcls,
    })

