#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tristimulus Values
==================

Defines objects for tristimulus values computation from spectral data.

References
----------
.. [1]  ASTM International. (2011). ASTM E2022 – 11 - Standard Practice for
        Calculation of Weighting Factors for Tristimulus Integration, i, 1–10.
        doi:10.1520/E2022-11
.. [2]  ASTM International. (2015). ASTM E308–15 - Standard Practice for
        Computing the Colors of Objects by Using the CIE System, 1–47.
        doi:10.1520/E0308-15

See Also
--------
`Colour Matching Functions IPython Notebook
<http://nbviewer.ipython.org/github/colour-science/colour-ipython/\
blob/master/notebooks/colorimetry/cmfs.ipynb>`_
`Spectrum IPython Notebook
<http://nbviewer.ipython.org/github/colour-science/colour-ipython/\
blob/master/notebooks/colorimetry/spectrum.ipynb>`_
"""

from __future__ import division, unicode_literals

import numpy as np

from colour.algebra import (
    CubicSplineInterpolator,
    LinearInterpolator,
    PchipInterpolator,
    SpragueInterpolator,
    lagrange_coefficients)
from colour.colorimetry import STANDARD_OBSERVERS_CMFS, ones_spd
from colour.utilities import CaseInsensitiveMapping, is_string

__author__ = 'Colour Developers'
__copyright__ = 'Copyright (C) 2013 - 2015 - Colour Developers'
__license__ = 'New BSD License - http://opensource.org/licenses/BSD-3-Clause'
__maintainer__ = 'Colour Developers'
__email__ = 'colour-science@googlegroups.com'
__status__ = 'Production'

__all__ = ['lagrange_coefficients_ASTME202211',
           'tristimulus_weighting_factors_ASTME202211',
           'spectral_to_XYZ',
           'wavelength_to_XYZ']

_TRISTIMULUS_WEIGHTING_FACTORS_CACHE = None

_LAGRANGE_INTERPOLATING_COEFFICIENTS_CACHE = None


def lagrange_coefficients_ASTME202211(
        interval=10,
        interval_type='inner'):
    """
    Computes the *Lagrange Coefficients* for given interval size using
    *ASTM Designation: E2022 – 11* method [1]_.

    Parameters
    ----------
    interval : int
        Interval size in nm.
    interval_type : unicode, optional
        **{'inner', 'boundary'}**,
        If the interval is an *inner* interval *Lagrange Coefficients* are
        computed for degree 4. Degree 3 is used for a *boundary* interval.

    Returns
    -------
    ndarray
        *Lagrange Coefficients*.

    See Also
    --------
    colour.lagrange_coefficients

    Examples
    --------
    >>> lagrange_coefficients_ASTME202211(  # doctest: +ELLIPSIS
    ...     10, 'inner')
    array([[-0.028...,  0.940...,  0.104..., -0.016...],
           [-0.048...,  0.864...,  0.216..., -0.032...],
           [-0.059...,  0.773...,  0.331..., -0.045...],
           [-0.064...,  0.672...,  0.448..., -0.056...],
           [-0.062...,  0.562...,  0.562..., -0.062...],
           [-0.056...,  0.448...,  0.672..., -0.064...],
           [-0.045...,  0.331...,  0.773..., -0.059...],
           [-0.032...,  0.216...,  0.864..., -0.048...],
           [-0.016...,  0.104...,  0.940..., -0.028...]])
    >>> lagrange_coefficients_ASTME202211(  # doctest: +ELLIPSIS
    ...     10, 'boundary')
    array([[ 0.85...,  0.19..., -0.04...],
           [ 0.72...,  0.36..., -0.08...],
           [ 0.59...,  0.51..., -0.10...],
           [ 0.48...,  0.64..., -0.12...],
           [ 0.37...,  0.75..., -0.12...],
           [ 0.28...,  0.84..., -0.12...],
           [ 0.19...,  0.91..., -0.10...],
           [ 0.12...,  0.96..., -0.08...],
           [ 0.05...,  0.99..., -0.04...]])
    """

    global _LAGRANGE_INTERPOLATING_COEFFICIENTS_CACHE
    if _LAGRANGE_INTERPOLATING_COEFFICIENTS_CACHE is None:
        _LAGRANGE_INTERPOLATING_COEFFICIENTS_CACHE = CaseInsensitiveMapping()

    name_lica = ', '.join((str(interval), interval_type))
    if name_lica in _LAGRANGE_INTERPOLATING_COEFFICIENTS_CACHE:
        return _LAGRANGE_INTERPOLATING_COEFFICIENTS_CACHE[name_lica]

    r_n = np.linspace(1 / interval, 1 - (1 / interval), interval - 1)
    d = 3
    if interval_type.lower() == 'inner':
        r_n += 1
        d = 4

    lica = _LAGRANGE_INTERPOLATING_COEFFICIENTS_CACHE[name_lica] = (
        np.asarray([lagrange_coefficients(r, d) for r in r_n]))

    return lica


def tristimulus_weighting_factors_ASTME202211(cmfs, illuminant, shape):
    """
    Returns a table (array) of tristimulus weighting factors for given colour
    matching functions and illuminant using *ASTM Designation: E2022 – 11*
    method [1]_. The computed table of tristimulus weighting factors should be
    used with spectral data that have been corrected for bandpass dependence.

    Parameters
    ----------
    cmfs : XYZ_ColourMatchingFunctions
        Standard observer colour matching functions.
    illuminant : SpectralPowerDistribution
        Illuminant spectral power distribution.
    shape : SpectralShape
        Shape used to build the table, only the interval is needed.

    Returns
    -------
    ndarray
        Tristimulus weighting factors table.

    Raises
    ------
    ValueError
        If the colour matching functions or illuminant intervals are not equal
        to 1 nm.

    Notes
    -----
    -   Input colour matching functions and illuminant intervals are expected
        to be equal to 1 nm. If the illuminant data is not available at 1 nm
        interval, it needs to be interpolated using *CIE* recommendations:
        The method developed by Sprague (1880) should be used for interpolating
        functions having a uniformly spaced independent variable and a
        *Cubic Spline* method for non-uniformly spaced independent variable.

    Examples
    --------
    >>> from colour import (
    ...     CMFS,
    ...     CIE_standard_illuminant_A,
    ...     SpectralPowerDistribution,
    ...     SpectralShape)
    >>> cmfs = CMFS.get('CIE 1964 10 Degree Standard Observer')
    >>> wl = cmfs.shape.range()
    >>> A = SpectralPowerDistribution(
    ...     'A', dict(zip(wl, CIE_standard_illuminant_A(wl))))
    >>> tristimulus_weighting_factors_ASTME202211(  # doctest: +ELLIPSIS
    ...     cmfs, A, SpectralShape(360, 830, 10))
    array([[ -1.0719517...-06,  -1.1660160...-07,  -4.7170865...-06],
           [ -1.6610183...-05,  -1.7791561...-06,  -7.3807513...-05],
           [ -6.2653701...-05,  -5.9889621...-06,  -2.9593991...-04],
           [  1.7320251...-03,   1.9067027...-04,   7.5032932...-03],
           [  2.4621972...-02,   2.5822083...-03,   1.1002471...-01],
           [  1.3380791...-01,   1.3624926...-02,   6.1486115...-01],
           [  3.7667958...-01,   3.9389747...-02,   1.7923789...+00],
           [  6.8597339...-01,   8.4147602...-02,   3.3861349...+00],
           [  9.6392707...-01,   1.5560922...-01,   4.9435215...+00],
           [  1.0797441...+00,   2.5937514...-01,   5.8055450...+00],
           [  1.0059086...+00,   4.2435443...-01,   5.8119510...+00],
           [  7.3080636...-01,   6.9621402...-01,   4.9194629...+00],
           [  3.4300924...-01,   1.0820871...+00,   3.2999062...+00],
           [  7.8315111...-02,   1.6159479...+00,   1.9725469...+00],
           [  2.1947558...-02,   2.4221192...+00,   1.1516036...+00],
           [  2.1833481...-01,   3.5293583...+00,   6.5817751...-01],
           [  7.4977436...-01,   4.8396064...+00,   3.8208014...-01],
           [  1.6420587...+00,   6.0995285...+00,   2.1088812...-01],
           [  2.8415557...+00,   7.2496656...+00,   1.0170750...-01],
           [  4.3359962...+00,   8.1142034...+00,   3.1666531...-02],
           [  6.1997932...+00,   8.7583677...+00,   7.5804720...-04],
           [  8.2620985...+00,   8.9875492...+00,  -3.9172607...-04],
           [  1.0227021...+01,   8.7604326...+00,   0.0000000...+00],
           [  1.1944534...+01,   8.3036887...+00,   0.0000000...+00],
           [  1.2745682...+01,   7.4678092...+00,   0.0000000...+00],
           [  1.2337484...+01,   6.3229345...+00,   0.0000000...+00],
           [  1.0817409...+01,   5.0332742...+00,   0.0000000...+00],
           [  8.5603334...+00,   3.7443729...+00,   0.0000000...+00],
           [  6.0135969...+00,   2.5057274...+00,   0.0000000...+00],
           [  3.8874293...+00,   1.5602974...+00,   0.0000000...+00],
           [  2.3093096...+00,   9.1132438...-01,   0.0000000...+00],
           [  1.2760400...+00,   4.9928961...-01,   0.0000000...+00],
           [  6.6559109...-01,   2.5908943...-01,   0.0000000...+00],
           [  3.3564032...-01,   1.3039082...-01,   0.0000000...+00],
           [  1.6631372...-01,   6.4561641...-02,   0.0000000...+00],
           [  8.1522110...-02,   3.1665019...-02,   0.0000000...+00],
           [  4.0032152...-02,   1.5575028...-02,   0.0000000...+00],
           [  1.9765095...-02,   7.7076691...-03,   0.0000000...+00],
           [  9.8592739...-03,   3.8551866...-03,   0.0000000...+00],
           [  4.9881869...-03,   1.9564249...-03,   0.0000000...+00],
           [  2.5679173...-03,   1.0105825...-03,   0.0000000...+00],
           [  1.3395357...-03,   5.2911440...-04,   0.0000000...+00],
           [  7.0758907...-04,   2.8060305...-04,   0.0000000...+00],
           [  3.7977086...-04,   1.5123241...-04,   0.0000000...+00],
           [  2.0654348...-04,   8.2606406...-05,   0.0000000...+00],
           [  1.1163959...-04,   4.4844798...-05,   0.0000000...+00],
           [  7.0223750...-05,   2.8349796...-05,   0.0000000...+00],
           [  1.6142206...-05,   6.5433614...-06,   0.0000000...+00]])
    """

    if cmfs.shape.interval != 1:
        raise ValueError('"{0}" shape "interval" must be 1!'.format(cmfs))

    if illuminant.shape.interval != 1:
        raise ValueError(
            '"{0}" shape "interval" must be 1!'.format(illuminant))

    global _TRISTIMULUS_WEIGHTING_FACTORS_CACHE
    if _TRISTIMULUS_WEIGHTING_FACTORS_CACHE is None:
        _TRISTIMULUS_WEIGHTING_FACTORS_CACHE = CaseInsensitiveMapping()

    name_twf = ', '.join((cmfs.name, illuminant.name, str(shape)))
    if name_twf in _TRISTIMULUS_WEIGHTING_FACTORS_CACHE:
        return _TRISTIMULUS_WEIGHTING_FACTORS_CACHE[name_twf]

    Y = cmfs.values
    S = illuminant.values

    W = S[::shape.interval, np.newaxis] * Y[::shape.interval, :]

    # First and last measurement intervals *Lagrange Coefficients*.
    c_c = lagrange_coefficients_ASTME202211(shape.interval, 'boundary')
    # Intermediate measurement intervals *Lagrange Coefficients*.
    c_b = lagrange_coefficients_ASTME202211(shape.interval, 'inner')

    # Total wavelengths count.
    w_c = len(Y)
    # Measurement interval interpolated values count.
    r_c = c_b.shape[0]
    # Last interval first interpolated wavelength.
    w_lif = w_c - (w_c - 1) % shape.interval - 1 - r_c

    # Intervals count.
    i_c = W.shape[0]
    i_cm = i_c - 1

    for i in range(3):
        # First interval.
        for j in range(r_c):
            for k in range(3):
                W[k, i] = W[k, i] + c_c[j, k] * S[j + 1] * Y[j + 1, i]

        # Last interval.
        for j in range(r_c):
            for k in range(i_cm, i_cm - 3, -1):
                W[k, i] = (W[k, i] + c_c[r_c - j - 1, i_cm - k] *
                           S[j + w_lif] * Y[j + w_lif, i])

        # Intermediate intervals.
        for j in range(i_c - 3):
            for k in range(r_c):
                w_i = (r_c + 1) * (j + 1) + 1 + k
                W[j, i] = W[j, i] + c_b[k, 0] * S[w_i] * Y[w_i, i]
                W[j + 1, i] = W[j + 1, i] + c_b[k, 1] * S[w_i] * Y[w_i, i]
                W[j + 2, i] = W[j + 2, i] + c_b[k, 2] * S[w_i] * Y[w_i, i]
                W[j + 3, i] = W[j + 3, i] + c_b[k, 3] * S[w_i] * Y[w_i, i]

        # Extrapolation of incomplete interval.
        for j in range(int(w_c - ((w_c - 1) % shape.interval)), w_c, 1):
            W[i_cm, i] = W[i_cm, i] + S[j] * Y[j, i]

    W *= 100 / np.sum(W, axis=0)[1]

    _TRISTIMULUS_WEIGHTING_FACTORS_CACHE[name_twf] = W

    return W


def spectral_to_XYZ(spd,
                    cmfs=STANDARD_OBSERVERS_CMFS.get(
                        'CIE 1931 2 Degree Standard Observer'),
                    illuminant=None):
    """
    Converts given spectral power distribution to *CIE XYZ* tristimulus values
    using given colour matching functions and illuminant.

    Parameters
    ----------
    spd : SpectralPowerDistribution
        Spectral power distribution.
    cmfs : XYZ_ColourMatchingFunctions
        Standard observer colour matching functions.
    illuminant : SpectralPowerDistribution, optional
        *Illuminant* spectral power distribution.

    Returns
    -------
    ndarray, (3,)
        *CIE XYZ* tristimulus values.

    Warning
    -------
    The output domain of that definition is non standard!

    Notes
    -----
    -   Output *CIE XYZ* tristimulus values are in domain [0, 100].

    References
    ----------
    .. [3]  Wyszecki, G., & Stiles, W. S. (2000). Integration Replace by
            Summation. In Color Science: Concepts and Methods, Quantitative
            Data and Formulae (pp. 158–163). Wiley. ISBN:978-0471399186

    Examples
    --------
    >>> from colour import (
    ...     CMFS, ILLUMINANTS_RELATIVE_SPDS, SpectralPowerDistribution)
    >>> cmfs = CMFS.get('CIE 1931 2 Degree Standard Observer')
    >>> data = {380: 0.0600, 390: 0.0600}
    >>> spd = SpectralPowerDistribution('Custom', data)
    >>> illuminant = ILLUMINANTS_RELATIVE_SPDS.get('D50')
    >>> spectral_to_XYZ(spd, cmfs, illuminant)  # doctest: +ELLIPSIS
    array([  4.5764852...e-04,   1.2964866...e-05,   2.1615807...e-03])
    """

    shape = cmfs.shape
    if spd.shape != cmfs.shape:
        spd = spd.clone().zeros(shape)

    if illuminant is None:
        illuminant = ones_spd(shape)
    else:
        if illuminant.shape != cmfs.shape:
            illuminant = illuminant.clone().zeros(shape)

    spd = spd.values
    x_bar, y_bar, z_bar = (cmfs.x_bar.values,
                           cmfs.y_bar.values,
                           cmfs.z_bar.values)
    illuminant = illuminant.values

    x_products = spd * x_bar * illuminant
    y_products = spd * y_bar * illuminant
    z_products = spd * z_bar * illuminant

    normalising_factor = 100 / np.sum(y_bar * illuminant)

    XYZ = np.array([normalising_factor * np.sum(x_products),
                    normalising_factor * np.sum(y_products),
                    normalising_factor * np.sum(z_products)])

    return XYZ


def wavelength_to_XYZ(wavelength,
                      cmfs=STANDARD_OBSERVERS_CMFS.get(
                          'CIE 1931 2 Degree Standard Observer'),
                      method=None):
    """
    Converts given wavelength :math:`\lambda` to *CIE XYZ* tristimulus values
    using given colour matching functions.

    If the wavelength :math:`\lambda` is not available in the colour matching
    function, its value will be calculated using *CIE* recommendations:
    The method developed by Sprague (1880) should be used for interpolating
    functions having a uniformly spaced independent variable and a
    *Cubic Spline* method for non-uniformly spaced independent variable.

    Parameters
    ----------
    wavelength : numeric or array_like
        Wavelength :math:`\lambda` in nm.
    cmfs : XYZ_ColourMatchingFunctions, optional
        Standard observer colour matching functions.
    method : unicode, optional
        {None, 'Cubic Spline', 'Linear', 'Pchip', 'Sprague'},
        Enforce given interpolation method.

    Returns
    -------
    ndarray
        *CIE XYZ* tristimulus values.

    Raises
    ------
    RuntimeError
        If Sprague (1880) interpolation method is forced with a
        non-uniformly spaced independent variable.
    ValueError
        If the interpolation method is not defined or if wavelength
        :math:`\lambda` is not contained in the colour matching functions
        domain.

    Notes
    -----
    -   Output *CIE XYZ* tristimulus values are in domain [0, 1].
    -   If *scipy* is not unavailable the *Cubic Spline* method will fallback
        to legacy *Linear* interpolation.
    -   Sprague (1880) interpolator cannot be used for interpolating
        functions having a non-uniformly spaced independent variable.

    Warning
    -------
    -   If *scipy* is not unavailable the *Cubic Spline* method will fallback
        to legacy *Linear* interpolation.
    -   *Cubic Spline* interpolator requires at least 3 wavelengths
        :math:`\lambda_n` for interpolation.
    -   *Linear* interpolator requires at least 2 wavelengths :math:`\lambda_n`
        for interpolation.
    -   *Pchip* interpolator requires at least 2 wavelengths :math:`\lambda_n`
        for interpolation.
    -   Sprague (1880) interpolator requires at least 6 wavelengths
        :math:`\lambda_n` for interpolation.

    Examples
    --------
    Uniform data is using Sprague (1880) interpolation by default:

    >>> from colour import CMFS
    >>> cmfs = CMFS.get('CIE 1931 2 Degree Standard Observer')
    >>> wavelength_to_XYZ(480, cmfs)  # doctest: +ELLIPSIS
    array([ 0.09564  ,  0.13902  ,  0.812950...])
    >>> wavelength_to_XYZ(480.5, cmfs)  # doctest: +ELLIPSIS
    array([ 0.0914287...,  0.1418350...,  0.7915726...])

    Enforcing *Cubic Spline* interpolation:

    >>> wavelength_to_XYZ(480.5, cmfs, 'Cubic Spline')  # doctest: +ELLIPSIS
    array([ 0.0914288...,  0.1418351...,  0.7915729...])

    Enforcing *Linear* interpolation:

    >>> wavelength_to_XYZ(480.5, cmfs, 'Linear')  # doctest: +ELLIPSIS
    array([ 0.0914697...,  0.1418482...,  0.7917337...])

    Enforcing *Pchip* interpolation:

    >>> wavelength_to_XYZ(480.5, cmfs, 'Pchip')  # doctest: +ELLIPSIS
    array([ 0.0914280...,  0.1418341...,  0.7915711...])
    """

    cmfs_shape = cmfs.shape
    if (np.min(wavelength) < cmfs_shape.start or
            np.max(wavelength) > cmfs_shape.end):
        raise ValueError(
            '"{0} nm" wavelength is not in "[{1}, {2}]" domain!'.format(
                wavelength, cmfs_shape.start, cmfs_shape.end))

    if wavelength not in cmfs:
        wavelengths, values, = cmfs.wavelengths, cmfs.values

        if is_string(method):
            method = method.lower()

        is_uniform = cmfs.is_uniform()

        if method is None:
            if is_uniform:
                interpolator = SpragueInterpolator
            else:
                interpolator = CubicSplineInterpolator
        elif method == 'cubic spline':
            interpolator = CubicSplineInterpolator
        elif method == 'linear':
            interpolator = LinearInterpolator
        elif method == 'pchip':
            interpolator = PchipInterpolator
        elif method == 'sprague':
            if is_uniform:
                interpolator = SpragueInterpolator
            else:
                raise RuntimeError(
                    ('"Sprague" interpolator can only be used for '
                     'interpolating functions having a uniformly spaced '
                     'independent variable!'))
        else:
            raise ValueError(
                'Undefined "{0}" interpolator!'.format(method))

        interpolators = [interpolator(wavelengths, values[..., i])
                         for i in range(values.shape[-1])]

        XYZ = np.dstack([i(np.ravel(wavelength)) for i in interpolators])
    else:
        XYZ = cmfs.get(wavelength)

    XYZ = np.reshape(XYZ, np.asarray(wavelength).shape + (3,))

    return XYZ
