#  _________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright (c) 2014 Sandia Corporation.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  This software is distributed under the BSD License.
#  _________________________________________________________________________

import logging
from six import itervalues

from pyomo.core.base.plugin import alias
from pyomo.core.base import Transformation
from pyomo.core import *
from pyomo.dae import *
from pyomo.dae.misc import generate_finite_elements
from pyomo.dae.misc import update_contset_indexed_component
from pyomo.dae.misc import create_partial_expression
from pyomo.dae.misc import add_discretization_equations
from pyomo.dae.misc import block_fully_discretized

logger = logging.getLogger('pyomo.core')

def _central_transform(v,s):
    """
    Applies the Central Difference formula of order O(h^2) for first derivatives
    """
    def _ctr_fun(i):
        tmp = sorted(s)
        idx = tmp.index(i)
        if idx == 0: # Needed since '-1' is considered a valid index in Python
            raise IndexError("list index out of range")
        return 1/(tmp[idx+1]-tmp[idx-1])*(v(tmp[idx+1])-v(tmp[idx-1]))
    return _ctr_fun

def _central_transform_order2(v,s):
    """
    Applies the Central Difference formula of order O(h^2) for second derivatives
    """
    def _ctr_fun2(i):
        tmp = sorted(s)
        idx = tmp.index(i)
        if idx == 0: # Needed since '-1' is considered a valid index in Python
            raise IndexError("list index out of range")
        return 1/((tmp[idx+1]-tmp[idx])*(tmp[idx]-tmp[idx-1]))*(v(tmp[idx+1])-2*v(tmp[idx])+v(tmp[idx-1]))
    return _ctr_fun2

def _forward_transform(v,s):
    """
    Applies the Forward Difference formula of order O(h) for first derivatives
    """
    def _fwd_fun(i):
        tmp = sorted(s)
        idx = tmp.index(i)
        return 1/(tmp[idx+1]-tmp[idx])*(v(tmp[idx+1])-v(tmp[idx]))
    return _fwd_fun

def _forward_transform_order2(v,s):
    """
    Applies the Forward Difference formula of order O(h) for second derivatives
    """
    def _fwd_fun(i):
        tmp = sorted(s)
        idx = tmp.index(i)
        return 1/((tmp[idx+2]-tmp[idx+1])*(tmp[idx+1]-tmp[idx]))*(v(tmp[idx+2])-2*v(tmp[idx+1])+v(tmp[idx]))
    return _fwd_fun

def _backward_transform(v,s):
    """
    Applies the Backward Difference formula of order O(h) for first derivatives
    """
    def _bwd_fun(i):
        tmp = sorted(s)
        idx = tmp.index(i)
        if idx == 0: # Needed since '-1' is considered a valid index in Python
            raise IndexError("list index out of range")
        return 1/(tmp[idx]-tmp[idx-1])*(v(tmp[idx])-v(tmp[idx-1]))
    return _bwd_fun

def _backward_transform_order2(v,s):
    """
    Applies the Backward Difference formula of order O(h) for second derivatives
    """
    def _bwd_fun(i):
        tmp = sorted(s)
        idx = tmp.index(i)
        if idx == 0 or idx == 1: # Needed since '-1' is considered a valid index in Python
            raise IndexError("list index out of range")
        return 1/((tmp[idx-1]-tmp[idx-2])*(tmp[idx]-tmp[idx-1]))*(v(tmp[idx])-2*v(tmp[idx-1])+v(tmp[idx-2]))
    return _bwd_fun

class Finite_Difference_Transformation(Transformation):
    """
    Transformation that applies finite difference methods to
    DAE, ODE, or PDE models. 
    
    """
    alias('dae.finite_difference', doc="TODO")

    def __init__(self):
        super(Finite_Difference_Transformation, self).__init__()
        self._nfe = {}
        self.all_schemes = {
            'BACKWARD' : (_backward_transform, _backward_transform_order2),
            'CENTRAL' : (_central_transform, _central_transform_order2),
            'FORWARD' : (_forward_transform, _forward_transform_order2),
            }

    def _setup(self, instance):
        instance = instance.clone()
        instance.construct()
        return instance

    def _apply_to(self, instance, **kwds):
        """
        Applies the transformation to a modeling instance

        Keyword Arguments:
        nfe           The desired number of finite element points to be 
                      included in the discretization.
        wrt           Indicates which ContinuousSet the transformation 
                      should be applied to. If this keyword argument is not
                      specified then the same scheme will be applied to all
                      ContinuousSets.
        scheme        Indicates which finite difference method to apply. 
                      Options are BACKWARD, CENTRAL, or FORWARD. The default
                      scheme is the backward difference method
        """

        options = kwds.pop('options', {})

        tmpnfe = kwds.pop('nfe',10)
        tmpds = kwds.pop('wrt',None)
        tmpscheme = kwds.pop('scheme','BACKWARD')
        self._scheme_name = tmpscheme.upper()

        if tmpds is not None:
            if tmpds.type() is not ContinuousSet:
                raise TypeError("The component specified using the 'wrt' keyword "\
                     "must be a differential set")
            elif 'scheme' in tmpds.get_discretization_info():
                raise ValueError("The discretization scheme '%s' has already been applied "\
                     "to the ContinuousSet '%s'" %(tmpds.get_discretization_info()['scheme'],tmpds.cname(True)))

        if None in self._nfe:
            raise ValueError("A general discretization scheme has already been applied to "\
                    "to every differential set in the model. If you would like to specify a "\
                    "specific discretization scheme for one of the differential sets you must discretize "\
                    "each differential set individually. If you would like to apply a different "\
                    "discretization scheme to all differential sets you must declare a new Implicit_"\
                    "Euler object")

        if len(self._nfe) == 0 and tmpds is None:
            # Same discretization on all differentialsets
            self._nfe[None] = tmpnfe
            currentds = None
        else :
            self._nfe[tmpds.cname(True)]=tmpnfe
            currentds = tmpds.cname(True)

        self._scheme = self.all_schemes.get(self._scheme_name,None)
        if self._scheme is None:
            raise ValueError("Unknown finite difference scheme '%s' specified using the "\
                     "'scheme' keyword. Valid schemes are 'BACKWARD', 'CENTRAL', and "\
                     "'FORWARD'" %(tmpscheme))

        for block in instance.block_data_objects(active=True):
            self._transformBlock(block,currentds)

        return instance

    def _transformBlock(self, block, currentds):

        self._fe = {}
        for ds in itervalues(block.component_map(ContinuousSet)):
            if currentds is None or currentds == ds.cname(True):
                generate_finite_elements(ds,self._nfe[currentds])
                if not ds.get_changed():
                    if len(ds)-1 > self._nfe[currentds]:
                        print("***WARNING: More finite elements were found in ContinuousSet "\
                            "'%s' than the number of finite elements specified in apply. "\
                            "The larger number of finite elements will be used." %(ds.cname(True)))
                
                self._nfe[ds.cname(True)]=len(ds)-1
                self._fe[ds.cname(True)]=sorted(ds)
                # Adding discretization information to the differentialset object itself
                # so that it can be accessed outside of the discretization object
                disc_info = ds.get_discretization_info()
                disc_info['nfe']=self._nfe[ds.cname(True)]
                disc_info['scheme']=self._scheme_name + ' Difference'
                     
        # Maybe check to see if any of the ContinuousSets have been changed,
        # if they haven't then the model components need not be updated
        # or even iterated through

        for c in itervalues(block.component_map()):
            update_contset_indexed_component(c)

        for d in itervalues(block.component_map(DerivativeVar)):
            dsets = d.get_continuousset_list()
            for i in set(dsets):
                if currentds is None or i.cname(True) == currentds:
                    oldexpr = d.get_derivative_expression()
                    loc = d.get_state_var()._contset[i]
                    count = dsets.count(i)
                    if count >= 3:
                        raise DAE_Error(
                            "Error discretizing '%s' with respect to '%s'. Current implementation "\
                            "only allows for taking the first or second derivative with respect to "\
                            "a particular ContinuousSet" %(d.cname(True),i.cname(True)))
                    scheme = self._scheme[count-1]
                    newexpr = create_partial_expression(scheme,oldexpr,i,loc)
                    d.set_derivative_expression(newexpr)

            # Reclassify DerivativeVar if all indexing ContinuousSets have been discretized
            if d.is_fully_discretized():
                add_discretization_equations(block,d)
                block.reclassify_component_type(d,Var)

        # Reclassify Integrals if all ContinuousSets have been discretized       
        if block_fully_discretized(block):
            
            if block.contains_component(Integral):
                for i in itervalues(block.component_map(Integral)):
                    i.reconstruct()
                    block.reclassify_component_type(i,Expression)
                # If a model contains integrals they are most likely to appear in the objective
                # function which will need to be reconstructed after the model is discretized.
                for k in itervalues(block.component_map(Objective)):
                    k.reconstruct()
