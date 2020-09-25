r"""

.. autofunction:: openpnm.models.physics.hydraulic_conductance.hagen_poiseuille
.. autofunction:: openpnm.models.physics.hydraulic_conductance.hagen_poiseuille_2D
.. autofunction:: openpnm.models.physics.hydraulic_conductance.hagen_poiseuille_power_law

"""
import numpy as _np


def hagen_poiseuille(target, pore_area="pore.area",
                     throat_area="throat.area",
                     pore_viscosity="pore.viscosity",
                     throat_viscosity="throat.viscosity",
                     conduit_lengths="throat.conduit_lengths",
                     conduit_shape_factors="throat.flow_shape_factors"):
    r"""
    Calculate the hydraulic conductance of conduits in network, where a
    conduit is ( 1/2 pore - full throat - 1/2 pore ). See the notes section.

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.
    pore_area : string
        Dictionary key of the pore area values
    throat_area : string
        Dictionary key of the throat area values
    pore_viscosity : string
        Dictionary key of the pore viscosity values
    throat_viscosity : string
        Dictionary key of the throat viscosity values
    conduit_lengths : string
        Dictionary key of the conduit length values
    conduit_shape_factors : string
        Dictionary key of the conduit DIFFUSION shape factor values

    Returns
    -------
    g : ndarray
        Array containing hydraulic conductance values for conduits in the
        geometry attached to the given physics object.

    Notes
    -----
    - This function calculates the specified property for the *entire*
    network then extracts the values for the appropriate throats at the end.

    - This function assumes cylindrical throats with constant cross-section
    area. Corrections for different shapes and variable cross-section area can
    be imposed by passing the proper conduit_shape_factors argument.

    - ``shape_factor`` depends on the physics of the problem, i.e. diffusion-like
    processes and fluid flow need different shape factors.

    """
    network = target.project.network
    throats = network.map_throats(throats=target.Ts, origin=target)
    phase = target.project.find_phase(target)
    cn = network["throat.conns"][throats]
    # Getting equivalent areas
    A1 = network[pore_area][cn[:, 0]]
    At = network[throat_area][throats]
    A2 = network[pore_area][cn[:, 1]]
    # Getting conduit lengths
    L1 = network[conduit_lengths + ".pore1"][throats]
    Lt = network[conduit_lengths + ".throat"][throats]
    L2 = network[conduit_lengths + ".pore2"][throats]
    # Preallocating g
    g1, g2, gt = _np.zeros((3, len(Lt)))
    # Setting g to inf when Li = 0 (ex. boundary pores)
    # INFO: This is needed since area could also be zero, which confuses NumPy
    m1, m2, mt = [Li != 0 for Li in [L1, L2, Lt]]
    g1[~m1] = g2[~m2] = gt[~mt] = _np.inf
    # Getting shape factors
    try:
        SF1 = phase[conduit_shape_factors + ".pore1"][throats]
        SFt = phase[conduit_shape_factors + ".throat"][throats]
        SF2 = phase[conduit_shape_factors + ".pore2"][throats]
    except KeyError:
        SF1 = SF2 = SFt = 1.0
    Dt = phase[throat_viscosity][throats]
    D1, D2 = phase[pore_viscosity][cn].T
    # Find g for half of pore 1, throat, and half of pore 2
    g1[m1] = A1[m1] ** 2 / (8 * _np.pi * D1 * L1)[m1]
    g2[m2] = A2[m2] ** 2 / (8 * _np.pi * D2 * L2)[m2]
    gt[mt] = At[mt] ** 2 / (8 * _np.pi * Dt * Lt)[mt]
    # Apply shape factors and calculate the final conductance
    return (1/gt/SFt + 1/g1/SF1 + 1/g2/SF2) ** (-1)


def hagen_poiseuille_2D(target,
                        pore_diameter="pore.diameter",
                        throat_diameter="throat.diameter",
                        pore_viscosity="pore.viscosity",
                        throat_viscosity="throat.viscosity",
                        conduit_lengths="throat.conduit_lengths",
                        conduit_shape_factors="throat.flow_shape_factors"):
    r"""
    Calculate the hydraulic conductance of conduits in a 2D network, where a
    conduit is ( 1/2 pore - full throat - 1/2 pore ). See the notes section.

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.
    pore_area : string
        Dictionary key of the pore area values
    throat_area : string
        Dictionary key of the throat area values
    pore_viscosity : string
        Dictionary key of the pore viscosity values
    throat_viscosity : string
        Dictionary key of the throat viscosity values
    conduit_lengths : string
        Dictionary key of the conduit length values
    conduit_shape_factors : string
        Dictionary key of the conduit flow shape factor values

    Returns
    -------
    g : ndarray
        Array containing hydraulic conductance values for conduits in the
        geometry attached to the given physics object.

    Notes
    -----
    - This function calculates the specified property for the *entire*
    network then extracts the values for the appropriate throats at the end.

    - This function assumes rectangular (2D) throats. Corrections for
    different shapes and variable cross-section area can be imposed by passing
    the proper flow_shape_factor argument.

    """
    network = target.project.network
    throats = network.map_throats(throats=target.Ts, origin=target)
    phase = target.project.find_phase(target)
    cn = network["throat.conns"][throats]
    # Getting pore/throat diameters
    D1 = network[pore_diameter][cn[:, 0]]
    Dt = network[throat_diameter][throats]
    D2 = network[pore_diameter][cn[:, 1]]
    # Getting conduit lengths
    L1 = network[conduit_lengths + ".pore1"][throats]
    Lt = network[conduit_lengths + ".throat"][throats]
    L2 = network[conduit_lengths + ".pore2"][throats]
    # Getting shape factors
    try:
        SF1 = phase[conduit_shape_factors + ".pore1"][throats]
        SFt = phase[conduit_shape_factors + ".throat"][throats]
        SF2 = phase[conduit_shape_factors + ".pore2"][throats]
    except KeyError:
        SF1 = SF2 = SFt = 1.0
    # Getting viscosity values
    mut = phase[throat_viscosity][throats]
    mu1, mu2 = phase[pore_viscosity][cn].T
    # Find g for half of pore 1, throat, and half of pore 2
    g1 = D1 ** 3 / (12 * mu1 * L1)
    g2 = D2 ** 3 / (12 * mu2 * L2)
    gt = Dt ** 3 / (12 * mut * Lt)

    return (1/gt/SFt + 1/g1/SF1 + 1/g2/SF2) ** (-1)


def conical_frustrum(target,
                     pore_area="pore.area",
                     throat_area="throat.area",
                     conduit_lengths="throat.conduit_lengths",
                     conduit_shape_factors="throat.flow_shape_factors",
                     pore_viscosity='pore.viscosity',
                     throat_viscosity='throat.viscosity',
                     conduit_viscosity=None):
    r"""
    Calculate the hydraulic conductance of conduits in network (assuming a non
    Newtonian fluid whose viscosity obeys a power law), where a
    conduit is ( 1/2 pore - full throat - 1/2 pore ). See the notes section.

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.
    pore_area : string
        Dictionary key of the pore area values
    throat_area : string
        Dictionary key of the throat area values
    pore_viscosity : string
        Dictionary key of the pore viscosity values
    throat_viscosity : string
        Dictionary key of the throat viscosity values.
    conduit_viscosity : string
        Dictionary key of the conduit viscosity values.  If this is provded
        then both the pore and throat viscosity arguments are ignored.

    Returns
    -------
    g : ndarray
        Array containing hydraulic conductance values for conduits in the
        geometry attached to the given physics object.

    Notes
    -----
    blah

    """
    network = target.project.network
    throats = network.map_throats(throats=target.Ts, origin=target)
    phase = target.project.find_phase(target)
    cn = network["throat.conns"][throats]
    # Getting equivalent areas
    A1 = network[pore_area][cn[:, 0]]
    At = network[throat_area][throats]
    A2 = network[pore_area][cn[:, 1]]
    # Getting conduit lengths
    L1 = network[conduit_lengths + ".pore1"][throats]
    Lt = network[conduit_lengths + ".throat"][throats]
    L2 = network[conduit_lengths + ".pore2"][throats]
    # Getting viscosity
    if conduit_viscosity is not None:
        mu1 = phase[conduit_viscosity + '.pore1']
        mut = phase[conduit_viscosity + '.throat']
        mu2 = phase[conduit_viscosity + '.pore2']
    else:
        mu1, mu2 = phase[pore_viscosity][network.conns]
        mut = phase[throat_viscosity]

    # Preallocating g
    g1, g2, gt = _np.zeros((3, len(Lt)))
    # Setting g to inf when Li = 0 (ex. boundary pores)
    # INFO: This is needed since area could also be zero, which confuses NumPy
    m1, m2, mt = [Li != 0 for Li in [L1, L2, Lt]]
    g1[~m1] = g2[~m2] = gt[~mt] = _np.inf
    # Getting shape factors
    try:
        SF1 = phase[conduit_shape_factors + ".pore1"][throats]
        SFt = phase[conduit_shape_factors + ".throat"][throats]
        SF2 = phase[conduit_shape_factors + ".pore2"][throats]
    except KeyError:
        SF1 = SF2 = SFt = 1.0

    R1 = (A1/_np.pi)**0.5
    R2 = (A2/_np.pi)**0.5
    Rt_orig = (At/_np.pi)**0.5

    Rt = Rt_orig
    mask = R1 == Rt_orig
    Rt[mask] *= 0.99
    alpha1 = (R1-Rt)[m1]/L1[m1]
    beta1 = 1 / (1/(Rt**3) - 1/(R1**3))

    Rt = Rt_orig
    mask = R2 == Rt_orig
    Rt[mask] *= 0.99
    alpha2 = (R2-Rt)[m2]/L2[m2]
    beta2 = 1 / (1/(Rt**3) - 1/(R2**3))

    g1[m1] = (3 * alpha1 * _np.pi / (8 * mu1[m1])) * beta1[m1]
    g2[m2] = (3 * alpha2 * _np.pi / (8 * mu2[m2])) * beta2[m2]
    gt[mt] = At[mt] ** 2 / (8 * _np.pi * mut * Lt)[mt]

    # Apply shape factors and calculate the final conductance
    return (1/gt/SFt + 1/g1/SF1 + 1/g2/SF2) ** (-1)


def valvatne_blunt(
    target,
    pore_viscosity="pore.viscosity",
    throat_viscosity="throat.viscosity",
    pore_shape_factor="pore.shape_factor",
    throat_shape_factor="throat.shape_factor",
    pore_area="pore.area",
    throat_area="throat.area",
    conduit_lengths="throat.conduit_lengths",
):
    r"""
    Calculate the single phase hydraulic conductance of conduits in network,
    where a conduit is ( 1/2 pore - full throat - 1/2 pore ) according to [1].
    Function has been adapted for use with the Statoil imported networks and
    makes use of the shape factor in these networks to apply Hagen-Poiseuille
    flow for conduits of different shape classes: Triangular, Square and
    Circular [2].

    Parameters
    ----------
    target : OpenPNM Object
        The object which this model is associated with. This controls the
        length of the calculated array, and also provides access to other
        necessary properties.

    pore_viscosity : string
        Dictionary key of the pore viscosity values

    throat_viscosity : string
        Dictionary key of the throat viscosity values

    pore_shape_factor : string
        Dictionary key of the pore geometric shape factor values

    throat_shape_factor : string
        Dictionary key of the throat geometric shape factor values

    pore_area : string
        Dictionary key of the pore area values. The pore area is calculated
        using following formula:
            pore_area = (pore_radius ** 2) / (4 * pore_shape_factor)
        Where theoratical value of pore_shape_factor in circular tube is
        calculated using following formula:
            pore_shape_factor = pore_area / perimeter **2 = 1/4π

    throat_area : string
        Dictionary key of the throat area values. The throat area is calculated
        using following formula:
            throat_area = (throat_radius ** 2) / (4 * throat_shape_factor)
        Where theoratical value of throat_shape_factor in circular tube is
        calculated using following formula:
            throat_shape_factor = throat_area / perimeter **2 = 1/4π

    conduit_lengths : string
        Dictionary key of the throat conduit lengths

    Returns
    -------
    g : ND-array
        Array containing hydraulic conductance values for conduits in the
        geometry attached to the given physics object.

    References
    ----------
    [1] Valvatne, Per H., and Martin J. Blunt. "Predictive pore‐scale modeling
    of two‐phase flow in mixed wet media." Water Resources Research 40,
    no. 7 (2004).
    [2] Patzek, T. W., and D. B. Silin (2001), Shape factor and hydraulic
    conductance in noncircular capillaries I. One-phase creeping flow,
    J. Colloid Interface Sci., 236, 295–304.
    """
    network = target.project.network
    mu_p = target[pore_viscosity]
    try:
        mu_t = target[throat_viscosity]
    except KeyError:
        mu_t = target.interpolate_data(pore_viscosity)
    # Throat Portion
    Gt = network[throat_shape_factor]
    tri = Gt <= _np.sqrt(3) / 36.0
    circ = Gt >= 0.07
    square = ~(tri | circ)
    ntri = _np.sum(tri)
    nsquare = _np.sum(square)
    ncirc = _np.sum(circ)
    kt = _np.ones_like(Gt)
    kt[tri] = 3.0 / 5.0
    kt[square] = 0.5623
    kt[circ] = 0.5
    # Pore Portions
    Gp = network[pore_shape_factor]
    tri = Gp <= _np.sqrt(3) / 36.0
    circ = Gp >= 0.07
    square = ~(tri | circ)
    ntri += _np.sum(tri)
    nsquare += _np.sum(square)
    ncirc += _np.sum(circ)
    kp = _np.ones_like(Gp)
    kp[tri] = 3.0 / 5.0
    kp[square] = 0.5623
    kp[circ] = 0.5
    gp = kp * (network[pore_area] ** 2) * Gp / mu_p
    gt = kt * (network[throat_area] ** 2) * Gt / mu_t
    conns = network["throat.conns"]
    l1 = network[conduit_lengths + ".pore1"]
    lt = network[conduit_lengths + ".throat"]
    l2 = network[conduit_lengths + ".pore2"]
    # Resistors in Series
    value = l1 / gp[conns[:, 0]] + lt / gt + l2 / gp[conns[:, 1]]
    return 1 / value


def classic_hagen_poiseuille(
    target,
    pore_diameter="pore.diameter",
    pore_viscosity="pore.viscosity",
    throat_length="throat.length",
    throat_diameter="throat.diameter",
    shape_factor="throat.shape_factor",
    **kwargs
):
    r"""
    Calculates the hydraulic conductivity of throat assuming cylindrical
    geometry using the Hagen-Poiseuille model

    Parameters
    ----------
    network : OpenPNM Network Object

    phase : OpenPNM Phase Object

    Notes
    -----
    This function calculates the specified property for the *entire* network
    then extracts the values for the appropriate throats at the end.

    """
    network = target.project.network
    throats = network.map_throats(throats=target.Ts, origin=target)
    # Get Nt-by-2 list of pores connected to each throat
    Ps = network["throat.conns"]
    # Get properties in every pore in the network
    phase = target.project.find_phase(target)
    mut = phase.interpolate_data(propname=pore_viscosity)[throats]
    pdia = network[pore_diameter]
    # Get pore lengths
    plen1 = 0.5 * pdia[Ps[:, 0]]
    plen2 = 0.5 * pdia[Ps[:, 1]]
    # Remove any non-positive lengths
    plen1[plen1 <= 1e-12] = 1e-12
    plen2[plen2 <= 1e-12] = 1e-12
    # Find g for half of pore 1
    gp1 = _np.pi * (pdia[Ps[:, 0]]) ** 4 / (128 * plen1 * mut)
    gp1[_np.isnan(gp1)] = _np.inf
    gp1[~(gp1 > 0)] = _np.inf  # Set 0 conductance pores (boundaries) to inf

    # Find g for half of pore 2
    gp2 = _np.pi * (pdia[Ps[:, 1]]) ** 4 / (128 * plen2 * mut)
    gp2[_np.isnan(gp2)] = _np.inf
    gp2[~(gp2 > 0)] = _np.inf  # Set 0 conductance pores (boundaries) to inf
    # Find g for full throat
    tdia = network[throat_diameter]
    tlen = network[throat_length]
    # Remove any non-positive lengths
    tlen[tlen <= 0] = 1e-12
    # Get shape factor
    try:
        sf = network[shape_factor]
    except KeyError:
        sf = _np.ones(network.num_throats())
    sf[_np.isnan(sf)] = 1.0
    gt = (1 / sf) * _np.pi * (tdia) ** 4 / (128 * tlen * mut)
    gt[~(gt > 0)] = _np.inf  # Set 0 conductance pores (boundaries) to inf
    value = (1 / gt + 1 / gp1 + 1 / gp2) ** (-1)
    return value
