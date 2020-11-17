import numpy as np
from openpnm.algorithms import ReactiveTransport
from openpnm.utils import logging, Docorator, GenericSettings
docstr = Docorator()
logger = logging.getLogger(__name__)


@docstr.get_sectionsf('AdvectionDiffusionSettings',
                      sections=['Parameters', 'Other Parameters'])
@docstr.dedent
class AdvectionDiffusionSettings(GenericSettings):
    r"""
    Parameters
    ----------
    %(ReactiveTransportSettings.parameters)s
    quantity : str
        The name of the physical quantity to be calculated. The default
        value is 'pore.concentration'.
    conductance : str
        The name of the advective-diffusive conductance model to use for
        calculating the transport conductance used by the algorithm. The
        default value is 'throat.ad_dif_conductance'.
    diffusive_conductance : str
        The name of the diffusive conductance values to be used by the
        specified ``conductance`` model to find the advective-diffusive
        conductance. The default value is 'throat.diffusive_conductance'.
    hydraulic_conductance : str, optional
        The name of the hydraulic conductance values to be used by the
        specified ``conductance`` model to find the advective-diffusive
        conductance. The default value is 'throat.hydraulic_conductance'.
    pressure : str, optional
        The name of the pressure values calculated by the ``StokesFlow``
        algorithm. The default value is 'pore.pressure'.

    ----

    **The following parameters pertain to the ReactiveTransport class**

    %(ReactiveTransportSettings.other_parameters)s

    ----

    **The following parameters pertain to the GenericTransport class**

    %(GenericTransportSettings.other_parameters)s

    """

    quantity = 'pore.concentration'
    conductance = 'throat.ad_dif_conductance'
    diffusive_conductance = 'throat.diffusive_conductance'
    hydraulic_conductance = 'throat.hydraulic_conductance'
    pressure = 'pore.pressure'


class AdvectionDiffusion(ReactiveTransport):
    r"""
    A subclass of ReactiveTransport to simulate advection-diffusion
    """

    def __init__(self, settings={}, **kwargs):
        super().__init__(**kwargs)
        self.settings._update_settings_and_docs(AdvectionDiffusionSettings())
        self.settings.update(settings)

    def setup(
            self,
            phase=None,
            quantity='',
            conductance='',
            diffusive_conductance='',
            hydraulic_conductance='',
            pressure='',
            **kwargs
    ):
        r"""
        Setup method for setting/modifying algorithm settings.
        """
        if phase:
            self.settings['phase'] = phase.name
        if quantity:
            self.settings['quantity'] = quantity
        if conductance:
            self.settings['conductance'] = conductance
        if diffusive_conductance:
            self.settings['diffusive_conductance'] = diffusive_conductance
        if hydraulic_conductance:
            self.settings['hydraulic_conductance'] = hydraulic_conductance
        if pressure:
            self.settings['pressure'] = pressure
        super().setup(**kwargs)

    def set_outflow_BC(self, pores, mode='merge'):
        r"""
        Adds outflow boundary condition to the selected pores.

        Notes
        -----
        Outflow condition simply means that the gradient of the solved
        quantity does not change, i.e. is 0.

        """
        # Hijack the parse_mode function to verify mode/pores argument
        allowed_modes = ['merge', 'overwrite', 'remove']
        mode = self._parse_mode(mode, allowed=allowed_modes, single=True)
        pores = self._parse_indices(pores)

        # Calculating A[i,i] values to ensure the outflow condition
        network = self.project.network
        phase = self.project.phases()[self.settings['phase']]
        throats = network.find_neighbor_throats(pores=pores)
        C12 = network.conns[throats]
        P12 = phase[self.settings['pressure']][C12]
        gh = phase[self.settings['hydraulic_conductance']][throats]
        Q12 = -gh * np.diff(P12, axis=1).squeeze()
        Qp = np.zeros(self.Np)
        np.add.at(Qp, C12[:, 0], -Q12)
        np.add.at(Qp, C12[:, 1], Q12)

        # Store boundary values
        if ('pore.bc_outflow' not in self.keys()) or (mode == 'overwrite'):
            self['pore.bc_outflow'] = np.nan
        self['pore.bc_outflow'][pores] = Qp[pores]

    def _apply_BCs(self):
        r"""
        Applies Dirichlet, Neumann, and outflow BCs in order
        """
        # Apply Dirichlet and rate BCs
        ReactiveTransport._apply_BCs(self)
        if 'pore.bc_outflow' not in self.keys():
            return
        # Apply outflow BC
        diag = self.A.diagonal()
        ind = np.isfinite(self['pore.bc_outflow'])
        diag[ind] += self['pore.bc_outflow'][ind]
        self.A.setdiag(diag)
