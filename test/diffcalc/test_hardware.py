###
# Copyright 2008-2011 Diamond Light Source Ltd.
# This file is part of Diffcalc.
#
# Diffcalc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Diffcalc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Diffcalc.  If not, see <http://www.gnu.org/licenses/>.
###

import unittest

try:
    from gdascripts.pd.dummy_pds import DummyPD  # @UnusedImport
except ImportError:
    from diffcalc.gdasupport.minigda.scannable import DummyPD


from diffcalc.gdasupport.scannable.base import ScannableGroup
from diffcalc.gdasupport.scannable.diffractometer import \
    DiffractometerScannableGroup
from diffcalc.gdasupport.scannable.mock import MockMotor
from diffcalc.hardware import HardwareCommands
from diffcalc.hardware import DummyHardwareAdapter
from diffcalc.hardware import HardwareAdapter
from diffcalc.hardware import ScannableHardwareAdapter
from nose.tools import eq_, assert_raises  # @UnresolvedImport
from test.diffcalc.gdasupport.scannable.mockdiffcalc import MockDiffcalc


class SimpleHardwareAdapter(HardwareAdapter):

    def getPosition(self):
        return [1, 2, 3]

    def getEnergy(self):
        return 1.


class TestHardwareAdapterBase(unittest.TestCase):

    def setUp(self):
        self.hardware = SimpleHardwareAdapter(['a', 'b', 'c'])

    def test__init__AndGetPhysicalAngleNames(self):
        self.assertEquals(self.hardware.getPhysicalAngleNames(),
                          ('a', 'b', 'c'))

    def test__repr__(self):
        print self.hardware.__repr__()

    def testSetGetPosition(self):
        pass

    def testSetGetEnergyWavelength(self):
        pass

    def testGetPositionByName(self):
        self.assertEqual(self.hardware.getPositionByName('c'), 3.)
        self.assertRaises(ValueError, self.hardware.getPositionByName,
                          'not an angle name')

    def testLowerLimitSetAndGet(self):
        self.hardware.setLowerLimit('a', -1)
        self.hardware.setLowerLimit('b', -2)
        self.hardware.setLowerLimit('c', -3)
        self.assertRaises(ValueError, self.hardware.setLowerLimit,
                          'not an angle', 1)
        self.hardware.setLowerLimit('b', None)
        print "Shoule print WARNING:"
        self.hardware.setLowerLimit('b', None)
        self.assertEquals(self.hardware.getLowerLimit('a'), -1)
        self.assertEquals(self.hardware.getLowerLimit('c'), -3)

    def testUpperLimitSetAndGet(self):
        self.hardware.setUpperLimit('a', 1)
        self.hardware.setUpperLimit('b', 2)
        self.hardware.setUpperLimit('c', 3)
        self.assertRaises(ValueError, self.hardware.setUpperLimit,
                          'not an angle', 1)
        self.hardware.setUpperLimit('b', None)
        print "Shoule print WARNING:"
        self.hardware.setUpperLimit('b', None)
        self.assertEquals(self.hardware.getUpperLimit('a'), 1)
        self.assertEquals(self.hardware.getUpperLimit('c'), 3)

    def testIsPositionWithinLimits(self):
        self.hardware.setUpperLimit('a', 1)
        self.hardware.setUpperLimit('b', 2)
        self.hardware.setLowerLimit('a', -1)
        self.assertTrue(self.hardware.isPositionWithinLimits([0, 0, 999]))
        self.assertTrue(self.hardware.isPositionWithinLimits([1, 2, 999]))
        self.assertTrue(self.hardware.isPositionWithinLimits([-1, -999, 999]))
        self.assertFalse(self.hardware.isPositionWithinLimits([1.01, 0, 999]))
        self.assertFalse(self.hardware.isPositionWithinLimits([0, 2.01, 999]))
        self.assertFalse(self.hardware.isPositionWithinLimits([-1.01, 0, 999]))

    def testIsAxisWithinLimits(self):
        self.hardware.setUpperLimit('a', 1)
        self.hardware.setUpperLimit('b', 2)
        self.hardware.setLowerLimit('a', -1)

        self.assertTrue(self.hardware.isAxisValueWithinLimits('a', 0))
        self.assertTrue(self.hardware.isAxisValueWithinLimits('b', 0))
        self.assertTrue(self.hardware.isAxisValueWithinLimits('c', 999))

        self.assertTrue(self.hardware.isAxisValueWithinLimits('a', 1))
        self.assertTrue(self.hardware.isAxisValueWithinLimits('b', 2))
        self.assertTrue(self.hardware.isAxisValueWithinLimits('c', 999))

        self.assertTrue(self.hardware.isAxisValueWithinLimits('a', -1))
        self.assertTrue(self.hardware.isAxisValueWithinLimits('b', -999))

        self.assertFalse(self.hardware.isAxisValueWithinLimits('a', 1.01))
        self.assertFalse(self.hardware.isAxisValueWithinLimits('b', 2.01))
        self.assertFalse(self.hardware.isAxisValueWithinLimits('a', 1.01))

    def setCutAndGetCuts(self):
        self.hardware.setCut('a', 2)
        self.hardware.setCut('b', 2)
        self.hardware.setCut('c', 2)
        self.assertEquals(self.hardware.getCuts(), {'a': 1, 'b': 2, 'c': 3})
        self.assertRaises(KeyError, self.hardware.setCut, 'not_a_key', 1)

    def test__configureCuts(self):
        hardware = SimpleHardwareAdapter(['a', 'b', 'c'])
        self.assertEquals(hardware.getCuts(),
                          {'a': -180, 'b': -180, 'c': -180})
        hardware = SimpleHardwareAdapter(['a', 'phi', 'c'])
        self.assertEquals(hardware.getCuts(), {'a': -180, 'phi': 0, 'c': -180})

    def test__configureCutsWithDefaults(self):
        hardware = SimpleHardwareAdapter(['a', 'b', 'c'],
                                               {'a': 1, 'b': 2})
        self.assertEquals(hardware.getCuts(), {'a': 1, 'b': 2, 'c': -180})
        hardware = SimpleHardwareAdapter(['a', 'phi', 'c'],
                                               {'a': 1, 'phi': 2})
        self.assertEquals(hardware.getCuts(), {'a': 1, 'phi': 2, 'c': -180})
        self.assertRaises(
            KeyError, SimpleHardwareAdapter, ['a', 'b', 'c'],
            {'a': 1, 'not_a_key': 2})

    def testCut(self):
        self.assertEquals(self.hardware.cutAngles((1, 2, 3)),
                          (1, 2, 3))
        self.assertEquals(self.hardware.cutAngles((-181, 0, 181)),
                          (179, 0, -179))
        self.assertEquals(self.hardware.cutAngles((-180, 0, 180,)),
                          (-180, 0, 180))
        self.assertEquals(self.hardware.cutAngles((-360, 0, 360)),
                          (0, 0, 0))


class TestHardwareCommands():

    def setup(self):
        self.hardware = SimpleHardwareAdapter(['a', 'b', 'c'])
        self.commands = HardwareCommands(self.hardware)

    def testSetcut(self):
        print "*******"
        self.commands.setcut()
        print "*******"
        self.commands.setcut('a')
        print "*******"
        self.commands.setcut('a', -181)
        print "*******"
        eq_(self.commands._hardware.getCuts()['a'], -181)
        assert_raises(
            ValueError, self.commands.setcut, 'a', 'not a number')
        assert_raises(
            KeyError, self.commands.setcut, 'not an axis', 1)

    def test_set_lim(self):
        self.commands.setmin('a', -1)
        print "*******"
        self.commands.setmin()
        print "*******"
        self.commands.setmax()
        print "*******"


class TestDummyHardwareAdapter(unittest.TestCase):

    def setUp(self):
        self.hardware = DummyHardwareAdapter(
            ['alpha', 'delta', 'gamma', 'omega', 'chi', 'phi'])

    def test__init__(self):
        self.assertEquals(self.hardware.getPosition(), [0.] * 6)
        self.assertEquals(self.hardware.getEnergy(), 12.39842)
        self.assertEquals(self.hardware.getWavelength(), 1.)
        self.assertEquals(self.hardware.getPhysicalAngleNames(),
                          ('alpha', 'delta', 'gamma', 'omega', 'chi', 'phi'))

    def test__repr__(self):
        print self.hardware.__repr__()

    def testSetGetPosition(self):
        pass

    def testSetGetEnergyWavelength(self):
        pass

    def testGetPositionByName(self):
        self.hardware.setPosition([1., 2., 3., 4., 5., 6.])
        self.assertEqual(self.hardware.getPositionByName('gamma'), 3.)
        self.assertRaises(ValueError, self.hardware.getPositionByName,
                          'not an angle name')


def createDummyAxes(names):
    result = []
    for name in names:
        result.append(DummyPD(name))
    return result


class TestGdaHardwareMonitor(unittest.TestCase):

    def setUp(self):
        dummy = createDummyAxes(['a', 'b', 'c', 'd', 'e', 'f'])
        self.grp = ScannableGroup('grp', dummy)
        self.diffhw = DiffractometerScannableGroup('sixc', MockDiffcalc(6),
                                                   self.grp)
        self.energyhw = MockMotor()
        self.hardware = ScannableHardwareAdapter(self.diffhw,
                                                       self.energyhw)

    def test__init__AndGetPhysicalAngleNames(self):
        self.assertEquals(self.hardware.getPhysicalAngleNames(),
                          ('a', 'b', 'c', 'd', 'e', 'f'))

    def testGetPosition(self):
        self.diffhw.asynchronousMoveTo((1, 2, 3, 4, 5, 6))
        self.assertEqual(self.hardware.getPosition(),
                         [1.0, 2.0, 3.0, 4.0, 5.0, 6.0])

    def testGetEnergy(self):
        self.energyhw.asynchronousMoveTo(1.0)
        self.assertEqual(self.hardware.getEnergy(), 1.0)

    def testGetWavelength(self):
        self.energyhw.asynchronousMoveTo(1.0)
        self.assertEqual(self.hardware.getWavelength(), 12.39842 / 1.0)
