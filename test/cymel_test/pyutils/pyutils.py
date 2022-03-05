# -*- coding: utf-8 -*-
u"""
Test of cymel.pyutils.pyutils
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import unittest

from cymel.pyutils import pyutils
from cymel.pyutils.pyutils import (
    with_metaclass, EMPTY_TUPLE,
)


#------------------------------------------------------------------------------
class TestPyutils(unittest.TestCase):
    u"""
    Test of pyutils
    """
    # Singleton のテスト。
    def test_Singleton(self):
        class Foo(with_metaclass(pyutils.Singleton, object)):
            def __init__(self, v):
                self._v = v

            def __repr__(self):
                return '%s(%r)' % (type(self).__name__, self._v)

        class Bar(Foo):
            pass

        a, b, c, d = Foo(1), Foo(2), Bar(3), Bar(4)
        self.assertEqual(repr(a), 'Foo(1)')
        self.assertEqual(repr(b), 'Foo(1)')
        self.assertEqual(repr(c), 'Bar(3)')
        self.assertEqual(repr(d), 'Bar(3)')

    # 木構造のイテレーションのテスト。
    def test_iterTree(self):
        class Node(object):
            def __init__(self, name, children=EMPTY_TUPLE):
                self._name = name
                self._children = tuple(children)

            def __str__(self):
                return self._name

            def children(self):
                return self._children

        tree = [Node('top', [
            Node('foo', [
                Node('fooA'),
                Node('fooB', [Node('fooB1'), Node('fooB2')]),
                Node('fooC'),
            ]),
            Node('bar', [
                Node('barA'),
                Node('barB'),
            ]),
            Node('baz', [
                Node('bazA', [Node('bazA1')]),
                Node('bazB', [Node('bazB1')]),
                Node('bazC'),
            ]),
        ])]
        self.assertEqual(
            [str(x) for x in pyutils.iterTreeBreadthFirst(tree, 'children')],
            ['top', 'foo', 'bar', 'baz', 'fooA', 'fooB', 'fooC', 'barA', 'barB', 'bazA', 'bazB', 'bazC', 'fooB1', 'fooB2', 'bazA1', 'bazB1'],
        )
        self.assertEqual(
            [str(x) for x in pyutils.iterTreeDepthFirst(tree, 'children')],
            ['top', 'foo', 'fooA', 'fooB', 'fooB1', 'fooB2', 'fooC', 'bar', 'barA', 'barB', 'baz', 'bazA', 'bazA1', 'bazB', 'bazB1', 'bazC'],
        )


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
