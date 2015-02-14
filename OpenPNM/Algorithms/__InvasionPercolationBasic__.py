# -*- coding: utf-8 -*-
"""
===============================================================================
InvasionPercolationBasic: Simple IP
===============================================================================

"""

import scipy as sp
import bisect
from collections import deque
from OpenPNM.Algorithms import GenericAlgorithm
from OpenPNM.Base import logging
logger = logging.getLogger(__name__)

class InvasionPercolationBasic(GenericAlgorithm):
    r"""
    A classic/basic invasion percolation algorithm optimized for speed

    Parameters
    ----------
    network : OpenPNM Network object
        The Network upon which the invasion should occur
    
    Notes
    ----
    n/a

    """

    def __init__(self,**kwargs):
        r'''

        '''
        super(InvasionPercolationBasic,self).__init__(**kwargs)

    def run(self,phase,inlets,throat_prop='throat.capillary_pressure'):
        r'''
        Perform the algorithm
        
        Parameters
        ----------
        phase : OpenPNM Phase object
            The phase to be injected into the Network.  The Phase must have the
            capillary entry pressure values for the system.
            
        inlets : array_like
            The list of inlet pores from which the Phase can enter the Network
            
        throat_prop : string
            The name of the throat property containing the capillary entry
            pressure.  The default is 'throat.capillary_pressure'
        

        '''
        queue = []
        self._phase = phase
        net = self._net
        # Setup arrays and info
        t_entry = phase[throat_prop]
        t_sorted = sp.argsort(t_entry,axis=0)  # Indices into t_entry giving a sorted list
        t_order = sp.zeros_like(t_sorted)
        t_order[t_sorted] = sp.arange(0,net.Nt)  # Location in sorted list
        t_inv = -sp.ones_like(net.Ts)  # List for tracking throat invasion order
        t_seq = -sp.ones_like(net.Ts)  # List for recreating invasion sequence
        p_inv = -sp.ones_like(net.Ps)  # List for tracking pore invasion order
        p_seq = -sp.ones_like(net.Ps)  # List for recreating invasion sequence
        p_inv[inlets] = 0  # Set inlet pores to invaded
        # Perform initial analysis on input pores
        Ts = net.find_neighbor_throats(pores=inlets)
        [bisect.insort(queue,T) for T in t_order[Ts]]  # Using binary search tree for sorting
        tcount = 0
        pcount = 0
        while len(queue) > 0:
            t = queue.pop(0)  # Find throat at the top of the queue
            t_next = t_sorted[t]  # Extract actual throat number
            t_inv[t_next] = tcount  # Note invasion sequence
            t_seq[tcount] = t_next
            while (len(queue)>0) and (queue[0] == t):  # Ensure throat is not duplicated
                t = queue.pop(0)  # Note: Preventing duplicate entries below might save some time here
            Ps = net['throat.conns'][t_next]  # Find pores connected to newly invaded throat
            Ps = Ps[p_inv[Ps]<0]  # Remove already invaded pores from Ps
            if len(Ps)>0:
                pcount += 1
                p_inv[Ps] = pcount  # Note invasion sequence
                p_seq[pcount] = Ps
                Ts = net.find_neighbor_throats(pores=Ps)  # Find connected throats
                Ts = Ts[t_inv[Ts]<0]  # Remove already invaded throats from Ts
                [bisect.insort(queue,T) for T in t_order[Ts]]  # Add new throats to queue
            tcount += 1
        self['throat.invasion_sequence'] = t_inv
        self['pore.invasion_sequence'] = p_inv

    def return_results(self,pores=[],throats=[]):
        r'''
        Places the results of the IP simulation into the Phase object.
        
        Parameters
        ----------
        pores and throats : array_like
            The list of pores and throats whose values should be returned to
            the Phase object.  Default is all of them.
        
        '''
        pores = sp.array(pores)
        if sp.shape(pores)[0] == 0:
            pores = self.Ps
        self._phase['throat.invasion_sequence'] = self['throat.invasion_sequence']
        self._phase['pore.invasion_sequence'] = self['pore.invasion_sequence']



if __name__ == '__main__':
    print('no tests yet')
