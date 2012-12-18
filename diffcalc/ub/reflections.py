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

from copy import deepcopy
import datetime  # @UnusedImport for the eval below

from diffcalc.util import DiffcalcException
from diffcalc.hkl.vlieg.geometry import VliegPosition


class Reflection:
    """A reflection"""
    def __init__(self, h, k, l, position, energy, tag, time):

        self.h = float(h)
        self.k = float(k)
        self.l = float(l)
        self.pos = position
        self.tag = tag
        self.energy = float(energy)      # energy=12.39842/lambda
        self.wavelength = 12.3984 / self.energy
        self.time = time

    def __str__(self):
        return ("energy=%-6.3f h=%-4.2f k=%-4.2f l=%-4.2f  alpha=%-8.4f "
                "delta=%-8.4f gamma=%-8.4f omega=%-8.4f chi=%-8.4f "
                "phi=%-8.4f  %-s %s" % (self.energy, self.h, self.k, self.l,
                self.pos.alpha, self.pos.delta, self.pos.gamma, self.pos.omega,
                self.pos.chi, self.pos.phi, self.tag, self.time))

    def getStateDict(self):
        return {
            'h': self.h,
            'k': self.k,
            'l': self.l,
            'position': self.pos.totuple(),
            'energy': self.energy,
            'tag': self.tag,
            'time': self.time
        }


class ReflectionList:

    def __init__(self, diffractometerPluginObject, externalAngleNames):
        self._geometry = diffractometerPluginObject
        self._reflist = []   # Will be a list of Reflections
        self._externalAngleNames = externalAngleNames

    def add_reflection(self, h, k, l, position, energy, tag, time):
        """adds a reflection, position in degrees
        """
        if type(position) in (list, tuple):
            try:
                position = self._geometry.create_position(*position)
            except AttributeError:
                position = VliegPosition(*position)
        self._reflist += [Reflection(h, k, l, position, energy, tag,
                                     time.__repr__())]

    def edit_reflection(self, num, h, k, l, position, energy, tag, time):
        """num starts at 1"""
        if type(position) in (list, tuple):
            position = VliegPosition(*position)
        try:
            self._reflist[num - 1] = Reflection(h, k, l, position, energy, tag,
                                                time.__repr__())
        except IndexError:
            raise DiffcalcException("There is no reflection " + repr(num)
                                     + " to edit.")

    def getReflection(self, num):
        """
        getReflection(num) --> ( [h, k, l], position, energy, tag, time ) --
        num starts at 1 position in degrees
        """
        r = deepcopy(self._reflist[num - 1])  # for convenience
        return [r.h, r.k, r.l], deepcopy(r.pos), r.energy, r.tag, eval(r.time)

    def get_reflection_in_external_angles(self, num):
        """getReflection(num) --> ( [h, k, l], (angle1...angleN), energy, tag )
        -- num starts at 1 position in degrees"""
        r = deepcopy(self._reflist[num - 1])  # for convenience
        externalAngles = self._geometry.internal_position_to_physical_angles(r.pos)
        result = [r.h, r.k, r.l], externalAngles, r.energy, r.tag, eval(r.time)
        return result

    def removeReflection(self, num):
        del self._reflist[num - 1]

    def swap_reflections(self, num1, num2):
        orig1 = self._reflist[num1 - 1]
        self._reflist[num1 - 1] = self._reflist[num2 - 1]
        self._reflist[num2 - 1] = orig1

    def __len__(self):
        return len(self._reflist)

    def __str__(self):
        return '\n'.join(self.str_lines())

    def str_lines(self):
        axes = tuple(s.upper() for s in self._externalAngleNames)
        if not self._reflist:
            return ["   <<< none specified >>>"]

        lines = []

        format = ("     %6s %5s %5s %5s  " + "%8s " * len(axes) + " TAG")
        values = ('ENERGY', 'H', 'K', 'L') + axes
        lines.append(format % values)

        for n in range(len(self._reflist)):
            ref_tuple = self.get_reflection_in_external_angles(n + 1)
            [h, k, l], externalAngles, energy, tag, _ = ref_tuple
            if tag is None:
                tag = ""
            format = ("  %2d %6.3f % 4.2f % 4.2f % 4.2f  " +
                      "% 8.4f " * len(axes) + " %s")
            values = (n + 1, energy, h, k, l) + externalAngles + (tag,)
            lines.append(format % values)
        return lines

    def getStateDict(self):
        """returns dict of form:
        {
        'ref_0' : reflectionDict0,
        'ref_1' : reflectionDict1 ...
        }
        """
        state = {}
        for n, ref in enumerate(self._reflist):
            state['ref_' + str(n)] = ref.getStateDict()
        return state

    def restoreFromStateDict(self, dictOfReflectionDicts):
        keys = dictOfReflectionDicts.keys()
        keys.sort()
        for key in keys:
            reflectionDict = dictOfReflectionDicts[key]
            reflectionDict['time'] = eval(reflectionDict['time'])
            self.add_reflection(**reflectionDict)
