from diffcalc.configurelogging import logging
from diffcalc.hkl.calcbase import HklCalculatorBase
from diffcalc.ub.calculation import PaperSpecificUbCalcStrategy
from diffcalc.utils import bound, AbstractPosition, DiffcalcException
from math import pi, asin, acos, atan2, sin, cos, sqrt
from numpy import matrix, identity

try:
    from Jama import Matrix
except ImportError:
    from diffcalc.npadaptor import Matrix

logger = logging.getLogger("diffcalc.hkl.willmot.calcwill")

CHOOSE_POSITIVE_GAMMA = True

TORAD = pi / 180
TODEG = 180 / pi
I = identity(3, float)
SMALL = 1e-10


def x_rotation(th):
    return matrix(((1, 0, 0), (0, cos(th), -sin(th)), (0, sin(th), cos(th))))


def y_rotation(th):
    return matrix(((cos(th), 0, sin(th)), (0, 1, 0), (-sin(th), 0, cos(th))))


def z_rotation(th):
    return matrix(((cos(th), -sin(th), 0), (sin(th), cos(th), 0), (0, 0, 1)))


def create_matrices(delta, gamma, omegah, phi):
    return (calc_DELTA(delta), calc_GAMMA(gamma), calc_OMEGAH(omegah),
            calc_PHI(phi))


def calc_DELTA(delta):
    return x_rotation(delta)                                             # (39)


def calc_GAMMA(gamma):
    return z_rotation(gamma)                                             # (40)


def calc_OMEGAH(omegah):
    return x_rotation(omegah)                                            # (41)


def calc_PHI(phi):
    return z_rotation(phi)                                               # (42)


def angles_to_hkl_phi(delta, gamma, omegah, phi):
    """Calculate hkl matrix in phi frame in units of 2*pi/lambda"""
    DELTA, GAMMA, OMEGAH, PHI = create_matrices(delta, gamma, omegah, phi)
    H_lab = (GAMMA * DELTA - I) * matrix([[0], [1], [0]])                # (43)
    H_phi = PHI.I * OMEGAH.I * H_lab                                     # (44)
    return H_phi


def angles_to_hkl(delta, gamma, omegah, phi, wavelength, UB):
    """Calculate hkl matrix in reprical lattice space in units of 1/Angstrom"""
    H_phi = angles_to_hkl_phi(delta, gamma, omegah, phi) * 2 * pi / wavelength
    hkl = UB.I * H_phi                                                    # (5)
    return hkl


class WillmottHorizontalPosition(AbstractPosition):

    def __init__(self, delta=None, gamma=None, omegah=None, phi=None):
        self.delta = delta
        self.gamma = gamma
        self.omegah = omegah
        self.phi = phi

    def clone(self):
        return WillmottHorizontalPosition(self.delta, self.gamma, self.omegah,
                                          self.phi)

    def changeToRadians(self):
        self.delta *= TORAD
        self.gamma *= TORAD
        self.omegah *= TORAD
        self.phi *= TORAD

    def changeToDegrees(self):
        self.delta *= TODEG
        self.gamma *= TODEG
        self.omegah *= TODEG
        self.phi *= TODEG

    def totuple(self):
        return (self.delta, self.gamma, self.omegah, self.phi)

    def __str__(self):
        return ('WillmottHorizontalPosition('
                'delta: %.4f gamma: %.4f omegah: %.4f phi: %.4f)' %
                (self.delta, self.gamma, self.omegah, self.phi))


class WillmottHorizontalUbCalcStrategy(PaperSpecificUbCalcStrategy):

    def calculate_q_phi(self, pos):
        H_phi = angles_to_hkl_phi(*pos.totuple())
        return Matrix(H_phi.tolist())


class WillmottHorizontalCalculator(HklCalculatorBase):

    def __init__(self, ubcalc, geometry, hardware, constraints,
                  raiseExceptionsIfAnglesDoNotMapBackToHkl=True):
        """"
        Where constraints.reference is a one element dict with the key
        either ('betain', 'betaout' or 'equal') and the value a number or None
        for 'betain_eq_betaout'
        """

        HklCalculatorBase.__init__(self, ubcalc, geometry, hardware,
                                   raiseExceptionsIfAnglesDoNotMapBackToHkl)

        self.constraints = constraints

    @property
    def _UB(self):
        return matrix(self._ubcalc.getUBMatrix().array)  # Jama to numpy matrix

    def _anglesToHkl(self, pos, wavelength):
        """
        Calculate miller indices from position in radians.
        """
        return angles_to_hkl(pos.delta, pos.gamma, pos.omegah, pos.phi,
                             wavelength, self._UB)

    def _anglesToVirtualAngles(self, pos, wavelength):
        """
        Calculate virtual-angles in radians from position in radians.

        Return theta, alpha, and beta in a dictionary.
        """

        betain = pos.omegah                                              # (52)

        hkl = angles_to_hkl(pos.delta, pos.gamma, pos.omegah, pos.phi,
                              wavelength, self._UB)
        H_phi = self._UB * hkl
        H_phi = H_phi / (2 * pi / wavelength)
        l_phi = H_phi[2, 0]
        sin_betaout = l_phi - sin(betain)
        betaout = asin(bound(sin_betaout))                               # (54)

        cos_2theta = cos(pos.delta) * cos(pos.gamma)
        theta = acos(bound(cos_2theta)) / 2.

        return {'theta': theta, 'betain': betain, 'betaout': betaout}

    def _hklToAngles(self, h, k, l, wavelength):
        """
        Calculate position and virtual angles in radians for a given hkl.
        """

        H_phi = self._UB * matrix([[h], [k], [l]])  # units: 1/Angstrom
        H_phi = H_phi / (2 * pi / wavelength)       # units: 2*pi/wavelength
        h_phi = H_phi[0, 0]
        k_phi = H_phi[1, 0]
        l_phi = H_phi[2, 0]                                               # (5)

        ### determine betain (omegah) and betaout ###

        ref_name, ref_value = self.constraints.reference.items()[0]
        if ref_name == 'betain':
            betain = ref_value
            betaout = asin(bound(l_phi - sin(betain)))                   # (53)
        elif ref_name == 'betaout':
            betaout = ref_value
            betain = asin(bound(l_phi - sin(betaout)))                   # (54)
        elif ref_name == 'betain_eq_betaout':
            betain = betaout = asin(bound(l_phi / 2))                    # (55)
        else:
            raise ValueError("Unexpected constraint name'%s'." % ref_name)

        if abs(betain) < SMALL:
            raise DiffcalcException('required betain was 0 degrees (requested '
                                    'q is perpendicular to surface normal)')
        if betain < -SMALL:
            raise DiffcalcException("betain was -ve (%.4f)" % betain)
        logger.info('betain = %.4f, betaout = %.4f',
                    betain * TODEG, betaout * TODEG)
        omegah = betain                                                  # (52)

        ### determine H_lab (X, Y and Z) ###

        Y = -(h_phi ** 2 + k_phi ** 2 + l_phi ** 2) / 2                  # (45)

        Z = (sin(betaout) + sin(betain) * (Y + 1)) / cos(omegah)         # (47)

        X_squared = (h_phi ** 2 + k_phi ** 2 -
                    ((cos(betain) * Y + sin(betain) * Z) ** 2))          # (48)
        if (X_squared < 0) and (abs(X_squared) < SMALL):
            X_squared = 0
        Xpositive = sqrt(X_squared)
        if CHOOSE_POSITIVE_GAMMA:
            X = -Xpositive
        else:
            X = Xpositive
        logger.info('H_lab (X,Y,Z) = [%.4f, %.4f, %.4f]', X, Y, Z)
        ### determine diffractometer angles ###

        gamma = atan2(-X, Y + 1)                                         # (49)
        if (abs(gamma) < SMALL):
            # degenerate case, only occurs when q || z
            delta = 2 * omegah
        else:
            delta = atan2(Z * sin(gamma), -X)                            # (50)
        M = cos(betain) * Y + sin(betain) * Z
        phi = atan2(h_phi * M - k_phi * X, h_phi * X + k_phi * M)        # (51)

        pos = WillmottHorizontalPosition(delta, gamma, omegah, phi)
        virtual_angles = {'betain': betain, 'betaout': betaout}
        return pos, virtual_angles
