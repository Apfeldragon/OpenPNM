import numpy as np
from openpnm.topotools import trim
from openpnm.utils import logging
from openpnm.io import GenericIO, Pandas
from openpnm.network import GenericNetwork
from pathlib import Path
from pandas import DataFrame
logger = logging.getLogger(__name__)


class Statoil(GenericIO):
    r"""
    The StatOil format is used by the Maximal Ball network extraction code of
    the Imperial College London group

    This class can be used to load and work with those networks. Numerous
    datasets are available for download from the group's
    `website <http://tinyurl.com/zurko4q>`_.

    The 'Statoil' format consists of 4 different files in a single
    folder. The data is stored in columns with each corresponding to a
    specific property. Headers are not provided in the files, so one must
    refer to various theses and documents to interpret their meaning.
    """

    @classmethod
    def export_data(cls, filename, network):
        dfp, dft = Pandas.to_dataframe(network=network, delim='.')

        # Write Link 1 file
        dft_ind = DataFrame()
        dft_ind[0] = network.Ts + 1
        a = 'network.' + network.name + '.throat.conns[0]'
        b = 'network.' + network.name + '.throat.conns[1]'
        c = 'network.' + network.name + '.throat.diameter'
        d = 'network.' + network.name + '.throat.shape_factor'
        e = 'network.' + network.name + '.throat.length'
        dft_temp = dft_ind.join(dft[[a, b, c, e]])
        temp = dft_temp.T
        temp.insert(0, 'top row', network.Nt)
        dft_temp = temp.T
        dft_temp = dft_temp.astype({a: int, b: int, 0: int})
        with open(filename + '_link1.dat', 'wt') as f:
            f.write(str(network.Nt) + '\n')
            for row in network.Ts:
                s = ''
                for col in dft_temp.keys():
                    val = dft_temp[col][row]
                    if isinstance(val, float):
                        val = np.format_float_scientific(val, precision=6,
                                                         exp_digits=3,
                                                         trim='k',
                                                         unique=False)
                    s = s + str(val) + '\t'
                s = s[:-1] + '\n'  # Remove trailing tab and a new line
                f.write(s)

        # Write Link 2 file
        a = 'network.' + network.name + '.throat.conns[0]'
        b = 'network.' + network.name + '.throat.conns[1]'
        c = 'network.' + network.name + '.throat.conduit_lengths.pore1'
        d = 'network.' + network.name + '.throat.conduit_lengths.pore2'
        e = 'network.' + network.name + '.throat.conduit_lengths.throat'
        f = 'network.' + network.name + '.throat.volume'
        g = 'network.' + network.name + '.throat.clay_volume'
        dft_temp = DataFrame()
        dft_temp['index'] = network.Ts + 1
        for item in [a, b, c, d, e, f, g]:
            try:
                dft_temp[item] = dft[item]
            except KeyError:
                dft_temp[item] = np.zeros([network.Nt, ])
        dft_temp[c] = dft_temp[c]/2
        dft_temp[d] = dft_temp[d]/2
        with open(filename + '_link2.dat', 'wt') as f:
            for row in network.Ts:
                s = ''
                for col in dft_temp.keys():
                    val = dft_temp[col][row]
                    if col == 'index':
                        # Original file has 6 spaces for index, but this is
                        # not enough for networks with > 1 million pores so
                        # I have bumped it to 9.  I'm not sure if this will
                        # still work with the ICL binaries.
                        s = s + '{:>9}'.format(str(val))
                        continue
                    if 'throat.conns[' in col:
                        # Original file has 7 spaces for pore indicdes, but
                        # this is not enough for networks with > 1 million
                        # pores so  I have bumped it to 9.  I'm not sure if
                        # this will still work with the ICL binaries.
                        s = s + '{:>9}'.format(str(val))
                        continue
                    if isinstance(val, float):
                        val = np.format_float_scientific(val, precision=6,
                                                         exp_digits=3,
                                                         trim='k',
                                                         unique=False)
                    s = s + '{:>15}'.format(str(val))
                s = s + '\n'  # Remove trailing tab and a new line
                f.write(s)

        # Write Node 1 file
        a = 'network.' + network.name + '.pore.coords[0]'
        b = 'network.' + network.name + '.pore.coords[1]'
        c = 'network.' + network.name + '.pore.coords[2]'
        dfp_temp = dft_ind.join(dfp[[a, b, c]])
        with open(filename + '_node1.dat', 'wt') as f:
            f.write(str(network.Np) + '\n')
            for row in network.Ps:
                s = ''
                for col in dfp_temp.keys():
                    val = dfp_temp[col][row]
                    if isinstance(val, float):
                        val = np.format_float_scientific(val, precision=6,
                                                         exp_digits=3,
                                                         trim='k',
                                                         unique=False)
                    s = s + '{:>15}'.format(str(val))
                s = s + '\n'  # Remove trailing tab and a new line
                f.write(s)

        # Write Node 2 file
        a = 'network.' + network.name + '.pore.volume'
        b = 'network.' + network.name + '.pore.diameter'
        c = 'network.' + network.name + '.pore.shape_factor'
        d = 'network.' + network.name + '.pore.clay_volume'
        dfp_temp = DataFrame()
        dfp_temp['index'] = network.Ps + 1
        for item in [a, b, c, d]:
            try:
                dfp_temp[item] = dfp[item][:network.Np]
            except KeyError:
                dfp_temp[item] = np.zeros([network.Np, ])
        dfp_temp[b] = dfp_temp[b]/2
        with open(filename + '_node2.dat', 'wt') as f:
            for row in network.Ps:
                s = ''
                for col in dfp_temp.keys():
                    val = dfp_temp[col][row]
                    if col == 'index':
                        # Original file has 6 spaces for index, but this is
                        # not enough for networks with > 1 million pores so
                        # I have bumped it to 9.  I'm not sure if this will
                        # still work with the ICL binaries.
                        s = s + '{:>9}'.format(str(val))
                        continue
                    if isinstance(val, float):
                        val = np.format_float_scientific(val, precision=6,
                                                         exp_digits=3,
                                                         trim='k',
                                                         unique=False)
                        # The original file has a spacing of 14, but this
                        # does not leave room for negative numbers, so I
                        # have bumped it by 1.  I'm not sure if this will
                        # still work with the ICL binaries.
                        s = s + '{:>15}'.format(str(val))
                s = s + '\n'  # Remove trailing tab and a new line
                f.write(s)

    @classmethod
    def load(cls, *args, **kwargs):
        r"""
        This method is being deprecated.  Use ``import_data`` instead.
        """
        return cls.import_data(*args, **kwargs)

    @classmethod
    def import_data(cls, path, prefix, network=None):
        r"""
        Load data from the \'dat\' files located in specified folder.

        Parameters
        ----------
        path : string
            The full path to the folder containing the set of \'dat\' files.

        prefix : string
            The file name prefix on each file. The data files are stored
            as \<prefix\>_node1.dat.

        network : OpenPNM Network Object
            If given then the data will be loaded on it and returned.  If not
            given, a Network will be created and returned.

        Returns
        -------
        An OpenPNM Project containing a GenericNetwork holding all the data

        """
        from pandas import read_table, DataFrame

        net = {}

        # Parse the link1 file
        path = Path(path)
        filename = Path(path.resolve(), prefix+'_link1.dat')
        with open(filename, mode='r') as f:
            link1 = read_table(filepath_or_buffer=f,
                               header=None,
                               skiprows=1,
                               sep=' ',
                               skipinitialspace=True,
                               index_col=0)
        link1.columns = ['throat.pore1', 'throat.pore2', 'throat.radius',
                         'throat.shape_factor', 'throat.total_length']
        # Add link1 props to net
        net['throat.conns'] = np.vstack((link1['throat.pore1']-1,
                                         link1['throat.pore2']-1)).T
        net['throat.conns'] = np.sort(net['throat.conns'], axis=1)
        net['throat.radius'] = np.array(link1['throat.radius'])
        net['throat.shape_factor'] = np.array(link1['throat.shape_factor'])
        net['throat.total_length'] = np.array(link1['throat.total_length'])

        filename = Path(path.resolve(), prefix+'_link2.dat')
        with open(filename, mode='r') as f:
            link2 = read_table(filepath_or_buffer=f,
                               header=None,
                               sep=' ',
                               skipinitialspace=True,
                               index_col=0)
        link2.columns = ['throat.pore1', 'throat.pore2',
                         'throat.pore1_length', 'throat.pore2_length',
                         'throat.length', 'throat.volume',
                         'throat.clay_volume']
        # Add link2 props to net
        cl_t = np.array(link2['throat.length'])
        net['throat.length'] = cl_t
        net['throat.conduit_lengths.throat'] = cl_t
        net['throat.volume'] = np.array(link2['throat.volume'])
        cl_p1 = np.array(link2['throat.pore1_length'])
        net['throat.conduit_lengths.pore1'] = cl_p1
        cl_p2 = np.array(link2['throat.pore2_length'])
        net['throat.conduit_lengths.pore2'] = cl_p2
        net['throat.clay_volume'] = np.array(link2['throat.clay_volume'])
        # ---------------------------------------------------------------------
        # Parse the node1 file
        filename = Path(path.resolve(), prefix+'_node1.dat')
        with open(filename, mode='r') as f:
            row_0 = f.readline().split()
            num_lines = int(row_0[0])
            array = np.ndarray([num_lines, 6])
            for i in range(num_lines):
                row = f.readline()\
                       .replace('\t', ' ').replace('\n', ' ').split()
                array[i, :] = row[0:6]
        node1 = DataFrame(array[:, [1, 2, 3, 4]])
        node1.columns = ['pore.x_coord', 'pore.y_coord', 'pore.z_coord',
                         'pore.coordination_number']
        # Add node1 props to net
        net['pore.coords'] = np.vstack((node1['pore.x_coord'],
                                        node1['pore.y_coord'],
                                        node1['pore.z_coord'])).T
        # ---------------------------------------------------------------------
        # Parse the node1 file
        filename = Path(path.resolve(), prefix+'_node2.dat')
        with open(filename, mode='r') as f:
            node2 = read_table(filepath_or_buffer=f,
                               header=None,
                               sep=' ',
                               skipinitialspace=True,
                               index_col=0)
        node2.columns = ['pore.volume', 'pore.radius', 'pore.shape_factor',
                         'pore.clay_volume']
        # Add node2 props to net
        net['pore.volume'] = np.array(node2['pore.volume'])
        net['pore.radius'] = np.array(node2['pore.radius'])
        net['pore.shape_factor'] = np.array(node2['pore.shape_factor'])
        net['pore.clay_volume'] = np.array(node2['pore.clay_volume'])
        net['throat.area'] = ((net['throat.radius']**2)
                              / (4.0*net['throat.shape_factor']))
        net['pore.area'] = ((net['pore.radius']**2)
                            / (4.0*net['pore.shape_factor']))

        if network is None:
            network = GenericNetwork()
        network = cls._update_network(network=network, net=net)

        # Use OpenPNM Tools to clean up network
        # Trim throats connected to 'inlet' or 'outlet' reservoirs
        trim1 = np.where(np.any(net['throat.conns'] == -1, axis=1))[0]
        # Apply 'outlet' label to these pores
        outlets = network['throat.conns'][trim1, 1]
        network['pore.outlets'] = False
        network['pore.outlets'][outlets] = True
        trim2 = np.where(np.any(net['throat.conns'] == -2, axis=1))[0]
        # Apply 'inlet' label to these pores
        inlets = network['throat.conns'][trim2, 1]
        network['pore.inlets'] = False
        network['pore.inlets'][inlets] = True
        # Now trim the throats
        to_trim = np.hstack([trim1, trim2])
        trim(network=network, throats=to_trim)

        return network.project


def get_domain_shape(network, pore_diameter='pore.diameter'):
    xmin, ymin, zmin = np.amin(network['pore.coords'], axis=0)
    xmax, ymax, zmax = np.amax(network['pore.coords'], axis=0)
    mins = []
    for axis, val in enumerate([xmin, ymin, zmin]):
        inds = np.where(network['pore.coords'][:, axis] == val)
        Rp = np.amax(network[pore_diameter][inds])/2
        mins.append(val - Rp)
    maxes = []
    for axis, val in enumerate([xmax, ymax, zmax]):
        inds = np.where(network['pore.coords'][:, axis] == val)
        Rp = np.amax(network[pore_diameter][inds])/2
        maxes.append(val + Rp)
    shape = np.array(maxes) - np.array(mins)
    return shape
