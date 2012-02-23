from diffcalc.utils import DiffcalcException
from diffcalc.hardware.plugin import HardwareMonitorPlugin


class ScannableHardwareMonitorPlugin(HardwareMonitorPlugin):

    _name = "DummyHarwdareMonitor"

    def __init__(self, diffractometerScannable, energyScannable,
                 energyScannableMultiplierToGetKeV=1):
        input_names = diffractometerScannable.getInputNames()
        HardwareMonitorPlugin.__init__(self, input_names)
        self.diffhw = diffractometerScannable
        self.energyhw = energyScannable
        self.energyScannableMultiplierToGetKeV = \
            energyScannableMultiplierToGetKeV

# Required methods

    def getPosition(self):
        """
        pos = getDiffractometerPosition() -- returns the current physical
        diffractometer position as a list in degrees
        """
        return self.diffhw.getPosition()

    def getEnergy(self):
        """energy = getEnergy() -- returns energy in kEv (NOT eV!) """
        multiplier = self.energyScannableMultiplierToGetKeV
        energy = self.energyhw.getPosition() * multiplier
        if energy is None:
            raise DiffcalcException("Energy has not been set")
        return energy

    def getWavelength(self):
        """wavelength = getWavelength() -- returns wavelength in Angstroms"""
        energy = self.getEnergy()
        return 12.39842 / energy

    def getDiffHardwareName(self):
        return self.diffhw.getName()
