# -*- coding: utf-8 -*-
u"""
Test of cymel.utils.optionvar
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
import unittest

import maya.cmds as cmds

from cymel.utils.optionvar import OptionVar
from cymel.initmaya import MAYA_VERSION

_PREFIX = '_cymel_test.'
_DEFAULTS = dict(
    boolFalse=False,
    boolTrue=True,
    int0=0,
    int1=1,
    int2=2,
    intN1=-1,
    intN2=-2,
    float0=0.,
    float1=1.,
    float2=2.,
    floatN1=-1.,
    floatN2=-2.,
    strVal='',
    arrA=[1, 2, 3],
    arrB=[1., 2., 3.],
    arrC=['1', '2', '3'],
)
_KEY_SET = frozenset(_DEFAULTS)
_GKEY_SET = frozenset([_PREFIX + x for x in _DEFAULTS])

if sys.hexversion < 0x3000000 and MAYA_VERSION >= (2016,):
    # 2016 以降、int は int だが intArray は long になる。
    _INTARRAY = lambda a: [long(x) for x in a]
else:
    _INTARRAY = lambda a: a


#------------------------------------------------------------------------------
class TestOptionVar(unittest.TestCase):
    u"""
    Test of cymel.utils.optionvar
    """
    def setUp(self):
        self._optvar = OptionVar(_PREFIX)
        self._optvar.clear()
        self._optvar.setDefaults(_DEFAULTS)
        self._optvar.resetToDefaults()

    def tearDown(self):
        self._optvar.clear()

    def test_defaults(self):
        opts = self._optvar

        self.assertFalse(_getGlobalKeys())

        self.assertEqual(set(opts.defaultKeys()), _KEY_SET)
        self.assertEqual([opts[x] for x in opts.defaultKeys()], opts.defaultValues())
        self.assertEqual([(x, opts[x]) for x in opts.defaultKeys()], opts.defaultItems())

        for key, val in _DEFAULTS.items():
            self.assertTrue(opts.hasDefault(key))
            self.assertTrue(key in opts)
            self.assertEqual(opts[key], val)
            opts[key] = None

        self.assertEqual(set(_getGlobalKeys()), _GKEY_SET)

    def test_values(self):
        opts = self._optvar

        self.assertFalse(opts.nonDefaultKeys())
        self.assertFalse(opts.nonDefaultValues())
        self.assertFalse(opts.nonDefaultItems())

        for key, val in _DEFAULTS.items():
            self.assertTrue(key in opts)
            #self.assertTrue(opts.has_key(key))
            self.assertTrue(opts.hasDefault(key))
            self.assertFalse(opts.hasNonDefaultValue(key))
            self.assertEqual(opts[key], val)
            opts[key] = None

        self.assertEqual(set(opts.nonDefaultKeys()), _KEY_SET)

        opts.resetToDefaults()
        self.assertFalse(opts.nonDefaultKeys())

        num = len(opts)
        opts['baka'] = 123
        num += 1
        self.assertEqual(len(opts), num)

        opts.reset('baka')
        num -=1
        self.assertEqual(len(opts), num)

        opts.pop('strVal')
        num -= 1
        self.assertEqual(len(opts), num)

    def test_translator(self):
        opts = self._optvar
        opts.setTranslator('arrA')
        val = [1, 2.3, u'4.5', [3, 4, 5], None, 'foo']
        opts['arrA'] = val
        self.assertEqual(opts['arrA'], val)
        self.assertEqual(repr(val), cmds.optionVar(q=_PREFIX + 'arrA'))
        self.assertEqual([v for k, v in zip(opts.keys(), opts.values()) if k == 'arrA'], [val])
        self.assertEqual([v for k, v in opts.items() if k == 'arrA'], [val])

    def test_val_bool(self):
        self._checkToChangeValue('boolFalse')
        self._checkToChangeValue('boolTrue')

    def test_val_int(self):
        self._checkToChangeValue('int0')
        self._checkToChangeValue('int1')
        self._checkToChangeValue('int2')
        self._checkToChangeValue('intN1')
        self._checkToChangeValue('intN2')

    def test_val_float(self):
        self._checkToChangeValue('float0')
        self._checkToChangeValue('float1')
        self._checkToChangeValue('float2')
        self._checkToChangeValue('floatN1')
        self._checkToChangeValue('floatN2')

    def test_val_str(self):
        self._checkToChangeValue('strVal')

    def test_val_arr(self):
        self._checkToChangeValue('arrA')

    def test_val_arrB(self):
        self._checkToChangeValue('arrB')

    def test_val_arrC(self):
        self._checkToChangeValue('arrC')

    def _checkToChangeValue(self, key):
        vals = [
            True, False,
            1, 0, 2, -1, 999,
            1., 0., 2., -1., 1.23,
            None, 
            u'1.24',
            _INTARRAY([7, -8, 9]),
            [1.7, -1.8, 1.9],
            [u'1.1', u'foo', u'2.2']
        ]

        opts = self._optvar
        orig = opts[key]
        default = opts.getDefault(key)

        #if default is False:
        #    vals += [True, False, 1, (0, False)]
        #elif default is True:
        #    vals += [True, False, (1, True), 0]
        #elif default is 0:
        #    vals += [True, (False, 0), 1, 0]
        #elif default is 1:
        #    vals += [(True, 1), False, 1, 0]
        #elif default == 0.:
        #    vals += [True, (False, 0.), 1, (0, 0.)]
        #elif default == 1.:
        #    vals += [(True, 1.), False, (1, 1.), 0]
        #else:
        #    vals += [True, False, 1, 0]

        for v in vals:
            if isinstance(v, tuple):
                v, store = v
            else:
                store = v
            opts[key] = v
            self.assertEqual(opts.hasNonDefaultValue(key), v != default or type(v) is not type(default))
            self.assertEqual(repr(opts[key]), repr(store))
        opts[key] = orig


def _getGlobalKeys():
    return [x for x in cmds.optionVar(l=True) if x.startswith(_PREFIX)]


#------------------------------------------------------------------------------
def suite():
    return unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])


def run(**kwargs):
    unittest.TextTestRunner(**kwargs).run(suite())

if __name__ == '__main__':
    run(verbosity=2)
