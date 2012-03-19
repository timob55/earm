# "embedded together" w earm1.0
from pysb import *
from pysbhelperfuncs import *


Model()
# Monomers for all modules (including imported modules)
# =====================================================
Monomer('L', ['bf']) # Ligand
Monomer('R', ['bf']) # Receptor
Monomer('DISC', ['bf']) # DISC
Monomer('flip', ['bf']) # flip
Monomer('C8', ['bf', 'state'], {'state':['pro', 'A']}) # Csp 8, states: pro, active
Monomer('BAR', ['bf']) # BAR
Monomer('Bid', ['bf', 'state'], {'state':['U', 'T', 'M']}) # Bid, states: Untruncated, Truncated, truncated+Membrane
Monomer('Bax', ['bf', 's1', 's2', 'state'], {'state':['C', 'M', 'A']}) # Bax, states: Cytoplasm, Mitochondria, Active
Monomer('Bak', ['bf', 's1', 's2', 'state'], {'state':['M', 'A']}) # Bax, states: inactive+Membrane, Active
Monomer('Bcl2', ['bf']) # Bcl2, states: Cytoplasm, Mitochondria
Monomer('BclxL', ['bf', 'state'], {'state':['C', 'M']}) # BclxL states: cytoplasm, mitochondris
Monomer('Mcl1', ['bf']) 
Monomer('Bad', ['bf', 'state'], {'state':['C', 'M']}) 
Monomer('NOXA', ['bf']) 
Monomer('CytoC', ['bf', 'state'], {'state':['M', 'C', 'A']})
Monomer('Smac', ['bf', 'state'], {'state':['M', 'C', 'A']})
Monomer('Apaf', ['bf', 'state'], {'state':['I', 'A']})
Monomer('Apop', ['bf'])
Monomer('C3', ['bf', 'state'], {'state':['pro', 'A', 'ub']}) # Csp 3, states: pro, active, ubiquitinated
Monomer('C6', ['bf', 'state'], {'state':['pro', 'A']}) # Csp 6, states: pro, active
Monomer('C9', ['bf'])
Monomer('PARP', ['bf', 'state'], {'state':['U', 'C']}) # PARP, states: uncleaved, cleaved
Monomer('XIAP', ['bf'])

# EARM 1.0 Parameters and Modules 
# ===============================
from earm_2_0_parms import parameter_dict as kd 
import earm_1_0modules # Must be called after the Monomers and Parameters are defined

# tBID to MOMP 
# ======================
# tBid and Bad spontaneously insert into the mito membrane
# --------------------------------------------------------
Rule('Bid_to_mem', Bid(bf = None, state = 'T') <> Bid(bf = None, state = 'M'), kd['BID_trans'][0],kd['BID_trans'][1])
Rule('Bad_to_mem', Bad(bf = None, state = 'C') <> Bad(bf = None, state = 'M'), kd['BAD_trans'][0],kd['BAD_trans'][1])

# tBid in the mitochondria activates Bax(C) and Bak(M)
#-----------------------------------------------------
two_step_mod(Bid(state = 'M'), Bax(state='C'), Bax(bf = None, state = 'A'), kd['BID_BAX'])
two_step_mod(Bid(state = 'M'), Bak(state='M'), Bak(bf = None, state = 'A'), kd['BID_BAK'])

# Autoactivation, Bax and Bak activate their own kind, but only when
# free (i.e. not part of a pore complex)
# ------------------------------------------------------------------
two_step_mod(Bax(state = 'A', s1=None, s2=None), Bax(state='C'), Bax(bf = None, state = 'A'), kd['BAX_BAX'])
two_step_mod(Bak(state = 'A', s1=None, s2=None), Bak(state='M'), Bak(bf = None, state = 'A'), kd['BAK_BAK'])

# ringp_assembly(Subunit, size, rates):
# ------------------------------------
ringp_assembly(Bax(bf=None, state='A'), 4, kd['BAX_PORE'])
ringp_assembly(Bak(bf=None, state='A'), 4, kd['BAK_PORE'])

# ------------------------------------
# MOMP Inhibition
# -----------------------------------------------------
# tBid and free Bax recruit Bcl-xL(C) and autoinhibit themselves
#        Bid/Bax + BclxL <> Bid/Bax:BclxL(C) >> Bid/Bax:BclxL(M)
#        Notice the product of this feeds into the product of the inh rxns
# ------------------------------------------------------------------------
two_step_mod(Bid(state = 'M'),BclxL(state='C'), BclxL(bf=None, state='M'), kd['Bid_BclxL_RA'])
two_step_mod(Bax(state = 'A', s1=None, s2=None), BclxL(state='C'), BclxL(bf=None, state='M'), kd['Bax_BclxL_RA'])


# Bcl2 inhibitors of Bax, Bak, and Bid
# a set of simple bind reactions:
#        Inh + Act <--> Inh:Act
# ------------------------------------
simple_bind_table([[                                            Bcl2,         BclxL,  Mcl1],
                   [                                              {}, {'state':'M'},    {}],
                   [Bid, {'state':'M'},                         True,          True,  True],
                   [Bax, {'s1':None, 's2':None, 'state':'A'},   True,          True, False],
                   [Bak, {'s1':None, 's2':None, 'state':'A'},  False,          True,  True]],
                  kd['BID_BAX_BAK_inh'], model)

# Sensitizers
# Bcl2 sensitizers bind through a simple bind resction: 
#        Inh + Act <--> Inh:Act
# This goes through the list in row-major order (as it should be)
# ---------------------------------------------------------------
simple_bind_table([[                      Bcl2,         BclxL,  Mcl1],
                   [                        {}, {'state':'M'},    {}],
                   [Bad,  {'state':'M'},  True,          True, False],
                   [NOXA, {},            False,         False,  True]], 
                  kd['BCLs_sens'], model)

# CytC, Smac release
# ----------------------
#        AMito + mCytoC <-->  AMito:mCytoC --> AMito + ACytoC  
#        ACytoC <-->  cCytoC
#        AMito + mSmac <-->  AMito:mSmac --> AMito + ASmac  
#        ASmac <-->  cSmac
# ----------------------
#ringp_transport(Subunit, Source, Dest, min_size, max_size, rates):
ringp_transport(Bax(bf=None), CytoC(state='M'), CytoC(state='C'), 4, 4, kd['BAX_CYTC']) 
ringp_transport(Bax(bf=None),  Smac(state='M'),  Smac(state='C'), 4, 4, kd['BAX_SMAC']) 
ringp_transport(Bak(bf=None), CytoC(state='M'), CytoC(state='C'), 4, 4, kd['BAK_CYTC'])
ringp_transport(Bak(bf=None),  Smac(state='M'),  Smac(state='C'), 4, 4, kd['BAK_SMAC'])

# --------------------------------------
# CytC and Smac activation after release
# --------------------------------------
Rule('act_cSmac',  Smac(bf=None, state='C') <> Smac(bf=None, state='A'), kd['SMAC_ACT'][0], kd['SMAC_ACT'][1])
Rule('act_cCytoC', CytoC(bf=None, state='C') <> CytoC(bf=None, state='A'), kd['CYTOC_ACT'][0], kd['CYTOC_ACT'][1])

# Import necessary modules
# ========================
# Generate the Receptor to Bid section from the EARM 1.0 module
earm_1_0modules.rec_to_bid(model, kd)
# Generate the Pore to MOMP section from the EARM 1.0 module
earm_1_0modules.pore_to_parp(model, kd)

# Initial non-zero species
# ========================
Initial(L(bf=None), L_0)
Initial(R(bf=None), R_0)
Initial(flip(bf=None), flip_0)
Initial(C8(bf=None, state='pro'), C8_0)
Initial(BAR(bf=None), BAR_0)
Initial(Bid(bf=None, state='U'), Bid_0)
Initial(Bax(bf=None, s1=None, s2=None, state='C'), Bax_0)
Initial(Bak(bf=None, s1=None, s2=None, state='M'), Bak_0)
Initial(Bcl2(bf=None), Bcl2_0)
Initial(BclxL (bf=None, state='C'), BclxL_0)
Initial(Mcl1(bf=None), Mcl1_0)
Initial(Bad(bf=None, state='C'), Bad_0)
Initial(NOXA(bf=None), NOXA_0)
Initial(CytoC(bf=None, state='M'), CytoC_0)
Initial(Smac(bf=None, state='M'), Smac_0)
Initial(Apaf(bf=None, state='I'), Apaf_0)
Initial(C3(bf=None, state='pro'), C3_0)
Initial(C6(bf=None, state='pro'), C6_0)
Initial(C9(bf=None), C9_0)
Initial(PARP(bf=None, state='U'), PARP_0)
Initial(XIAP(bf=None), XIAP_0)

# Observables
# ===========
# Fig 4B from Albeck observes these, normalizes and inverts them
# Observe('Bid',   Bid(bf=None, state='U'))
# Observe('PARP',  PARP(bf=None, state='U'))
# Observe('Smac',  Smac(bf=None, state='mito'))
# # This is what *should* be observed???
Observe('mBid',  Bid(state='M'))
Observe('cSmac', Smac(state='A'))
Observe('cPARP', PARP(state='C'))
