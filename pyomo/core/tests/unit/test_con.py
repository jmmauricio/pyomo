#  _________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright (c) 2014 Sandia Corporation.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  This software is distributed under the BSD License.
#  _________________________________________________________________________
#
# Unit Tests for Elements of a Model
#
# TestSimpleCon                Class for testing single constraint
# TestArrayCon                Class for testing array of constraint
#

import logging
import sys
import os
from os.path import abspath, dirname
currdir = dirname(abspath(__file__))+os.sep

import pyutilib.th as unittest

from pyomo.environ import *

from six import StringIO

class LogBuffer(object):

    def __init__(self, logger, logLevel=None):
        if isinstance(logger, logging.Logger):
            self.logger = logger
        else:
            self.logger = logging.getLogger(logger)
        self.buffer = StringIO()
        if logLevel is None:
            self.old_level = None
        else:
            self.old_level = self.logger.getEffectiveLevel()
            self.logger.setLevel(logLevel)

        self.logHandler = logging.StreamHandler(self.buffer)
        self.logger.addHandler(self.logHandler)

    def __del__(self):
        self.close()

    def close(self):
        if self.logger is None:
            return
        if self.old_level is not None:
            self.logger.setLevel(self.old_level)

        self.logger.removeHandler(self.logHandler)
        self.logHandler.flush()
        self.buffer.flush()
        self.logHandler = None
        self.logger = None

    def value(self):
        if self.logHandler is not None:
            self.logHandler.flush();
        self.buffer.flush()
        return self.buffer.getvalue()


class TestConstraintCreation(unittest.TestCase):

    def create_model(self,abstract=False):
        if abstract is True:
            model = AbstractModel()
        else:
            model = ConcreteModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        return model

    def test_tuple_construct_equality(self):
        model = self.create_model()
        def rule(model):
            return (0.0, model.x)
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         True)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.x)
        self.assertEqual(model.c.upper,             0)

        model = self.create_model()
        def rule(model):
            return (model.x, 0.0)
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         True)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.x)
        self.assertEqual(model.c.upper,             0)

    def test_tuple_construct_inf_equality(self):
        model = self.create_model(abstract=True)
        def rule(model):
            return (model.x, float('inf'))
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

        model = self.create_model(abstract=True)
        def rule(model):
            return (float('inf'), model.x)
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

    def test_tuple_construct_1sided_inequality(self):
        model = self.create_model()
        def rule(model):
            return (None, model.y, 1)
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             1)

        model = self.create_model()
        def rule(model):
            return (0, model.y, None)
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

    def test_tuple_construct_1sided_inf_inequality(self):
        model = self.create_model()
        def rule(model):
            return (float('-inf'), model.y, 1)
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             1)

        model = self.create_model()
        def rule(model):
            return (0, model.y, float('inf'))
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

    def test_tuple_construct_unbounded_inequality(self):
        model = self.create_model()
        def rule(model):
            return (None, model.y, None)
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

        model = self.create_model()
        def rule(model):
            return (float('-inf'), model.y, float('inf'))
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

    def test_tuple_construct_invalid_1sided_inequality(self):
        model = self.create_model(abstract=True)
        def rule(model):
            return (model.x, model.y, None)
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

        model = self.create_model(abstract=True)
        def rule(model):
            return (None, model.y, model.z)
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

    def test_tuple_construct_2sided_inequality(self):
        model = self.create_model()
        def rule(model):
            return (0, model.y, 1)
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             1)

    def test_tuple_construct_invalid_2sided_inequality(self):
        model = self.create_model(abstract=True)
        def rule(model):
            return (model.x, model.y, 1)
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

        model = self.create_model(abstract=True)
        def rule(model):
            return (0, model.y, model.z)
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

    def test_expr_construct_equality(self):
        model = self.create_model()
        def rule(model):
            return 0.0 == model.x
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         True)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.x)
        self.assertEqual(model.c.upper,             0)

        model = self.create_model()
        def rule(model):
            return model.x == 0.0
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         True)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.x)
        self.assertEqual(model.c.upper,             0)

    def test_expr_construct_inf_equality(self):
        model = self.create_model(abstract=True)
        def rule(model):
            return model.x == float('inf')
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

        model = self.create_model(abstract=True)
        def rule(model):
            return float('inf') == model.x
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

    def test_expr_construct_1sided_inequality(self):
        model = self.create_model()
        def rule(model):
            return model.y <= 1
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             1)

        model = self.create_model()
        def rule(model):
            return 0 <= model.y
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             0)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

        model = self.create_model()
        def rule(model):
            return model.y >= 1
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             1)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

        model = self.create_model()
        def rule(model):
            return 0 >= model.y
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             0)

    def test_expr_construct_unbounded_inequality(self):
        model = self.create_model()
        def rule(model):
            return model.y <= float('inf')
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

        model = self.create_model()
        def rule(model):
            return float('-inf') <= model.y
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

        model = self.create_model()
        def rule(model):
            return model.y >= float('-inf')
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

        model = self.create_model()
        def rule(model):
            return float('inf') >= model.y
        model.c = Constraint(rule=rule)

        self.assertEqual(model.c.equality,         False)
        self.assertEqual(model.c.lower,             None)
        self.assertIs   (model.c.body,              model.y)
        self.assertEqual(model.c.upper,             None)

    def test_expr_construct_invalid_unbounded_inequality(self):
        model = self.create_model(abstract=True)
        def rule(model):
            return model.y <= float('-inf')
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

        model = self.create_model(abstract=True)
        def rule(model):
            return float('inf') <= model.y
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

        model = self.create_model(abstract=True)
        def rule(model):
            return model.y >= float('inf')
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

        model = self.create_model(abstract=True)
        def rule(model):
            return float('-inf') >= model.y
        model.c = Constraint(rule=rule)
        self.assertRaises(ValueError, model.create_instance)

    # make sure we can use a mutable param that
    # has not been given a value in the upper bound
    # of an inequality constraint
    def test_mutable_novalue_param_lower_bound(self):
        model = ConcreteModel()
        model.x = Var()
        model.p = Param(mutable=True)
        model.p.value = None

        model.c = Constraint(expr=0 <= model.x - model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p <= model.x)
        self.assertTrue(model.c.lower is model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p <= model.x + 1)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p + 1 <= model.x)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.p + 1)**2 <= model.x)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p <= model.x <= model.p + 1)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x - model.p >= 0)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x >= model.p)
        self.assertTrue(model.c.lower is model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x + 1 >= model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x >= model.p + 1)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x >= (model.p + 1)**2)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p + 1 >= model.x >= model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.p, model.x, None))
        self.assertTrue(model.c.lower is model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.p, model.x + 1, None))
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.p + 1, model.x, None))
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.p, model.x, 1))
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

    # make sure we can use a mutable param that
    # has not been given a value in the lower bound
    # of an inequality constraint
    def test_mutable_novalue_param_upper_bound(self):
        model = ConcreteModel()
        model.x = Var()
        model.p = Param(mutable=True)
        model.p.value = None

        model.c = Constraint(expr=model.x - model.p <= 0)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x <= model.p)
        self.assertTrue(model.c.upper is model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x + 1 <= model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x <= model.p + 1)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x <= (model.p + 1)**2)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p + 1 <= model.x <= model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=0 >= model.x - model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p >= model.x)
        self.assertTrue(model.c.upper is model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p >= model.x + 1)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p + 1 >= model.x)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.p + 1)**2 >= model.x)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p >= model.x >= model.p + 1)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(None, model.x, model.p))
        self.assertTrue(model.c.upper is model.p)
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(None, model.x + 1, model.p))
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(None, model.x, model.p + 1))
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

        model.c = Constraint(expr=(1, model.x, model.p))
        self.assertEqual(model.c.equality, False)
        model.del_component(model.c)

    # make sure we can use a mutable param that
    # has not been given a value in the rhs of
    # of an equality constraint
    def test_mutable_novalue_param_equality(self):
        model = ConcreteModel()
        model.x = Var()
        model.p = Param(mutable=True)
        model.p.value = None

        model.c = Constraint(expr=model.x - model.p == 0)
        self.assertEqual(model.c.equality, True)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x == model.p)
        self.assertTrue(model.c.upper is model.p)
        self.assertEqual(model.c.equality, True)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x + 1 == model.p)
        self.assertEqual(model.c.equality, True)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x + 1 == (model.p + 1)**2)
        self.assertEqual(model.c.equality, True)
        model.del_component(model.c)

        model.c = Constraint(expr=model.x == model.p + 1)
        self.assertEqual(model.c.equality, True)
        model.del_component(model.c)

        model.c = Constraint(expr=model.p <= model.x <= model.p)
        self.assertTrue(model.c.upper is model.p)
        # GH: Not sure if we are supposed to detect equality
        #     in this situation. I would rather us not, for
        #     the sake of making the code less complicated.
        #     Either way, I am not going to test for it here.
        #self.assertEqual(model.c.equality, <blah>)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.x, model.p))
        self.assertTrue(model.c.upper is model.p)
        self.assertEqual(model.c.equality, True)
        model.del_component(model.c)

        model.c = Constraint(expr=(model.p, model.x))
        self.assertTrue(model.c.upper is model.p)
        self.assertEqual(model.c.equality, True)
        model.del_component(model.c)

class TestSimpleCon(unittest.TestCase):

    def test_set_expr_explicit_multivariate(self):
        """Test expr= option (multivariate expression)"""
        model = ConcreteModel()
        model.A = RangeSet(1,4)
        model.x = Var(model.A, initialize=2)
        ans=0
        for i in model.A:
            ans = ans + model.x[i]
        ans = ans >= 0
        ans = ans <= 1
        model.c = Constraint(expr=ans)

        self.assertEqual(model.c(), 8)
        self.assertEqual(model.c.body(), 8)
        self.assertEqual(value(model.c.body), 8)

    def test_set_expr_explicit_univariate(self):
        """Test expr= option (univariate expression)"""
        model = ConcreteModel()
        model.x = Var(initialize=2)
        ans = model.x >= 0
        ans = ans <= 1
        model.c = Constraint(expr=ans)

        self.assertEqual(model.c(), 2)
        self.assertEqual(model.c.body(), 2)
        self.assertEqual(value(model.c.body), 2)

    def test_set_expr_undefined_univariate(self):
        """Test expr= option (univariate expression)"""
        model = ConcreteModel()
        model.x = Var()
        ans = model.x >= 0
        ans = ans <= 1
        model.c = Constraint(expr=ans)

        #self.assertRaises(ValueError, model.c)
        self.assertEqual(model.c(),None)
        model.x = 2
        self.assertEqual(model.c(), 2)
        self.assertEqual(value(model.c.body), 2)

    def test_set_expr_inline(self):
        """Test expr= option (inline expression)"""
        model = ConcreteModel()
        model.A = RangeSet(1,4)
        model.x = Var(model.A,initialize=2)
        model.c = Constraint(expr=0 <= sum(model.x[i] for i in model.A) <= 1)

        self.assertEqual(model.c(), 8)
        self.assertEqual(value(model.c.body), 8)

    def test_rule1(self):
        """Test rule option"""
        model = ConcreteModel()
        model.B = RangeSet(1,4)
        def f(model):
            ans=0
            for i in model.B:
                ans = ans + model.x[i]
            ans = ans >= 0
            ans = ans <= 1
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(rule=f)

        self.assertEqual(model.c(), 8)
        self.assertEqual(value(model.c.body), 8)

    def test_rule2(self):
        """Test rule option"""
        model = ConcreteModel()
        model.B = RangeSet(1,4)
        def f(model):
            ans=0
            for i in model.B:
                ans = ans + model.x[i]
            return (0,ans,1)
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(rule=f)

        self.assertEqual(model.c(), 8)
        self.assertEqual(value(model.c.body), 8)

    def test_rule3(self):
        """Test rule option"""
        model = ConcreteModel()
        model.B = RangeSet(1,4)
        def f(model):
            ans=0
            for i in model.B:
                ans = ans + model.x[i]
            return (0,ans,None)
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(rule=f)

        self.assertEqual(model.c(), 8)
        self.assertEqual(value(model.c.body), 8)

    def test_rule4(self):
        """Test rule option"""
        model = ConcreteModel()
        model.B = RangeSet(1,4)
        def f(model):
            ans=0
            for i in model.B:
                ans = ans + model.x[i]
            return (None,ans,1)
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(rule=f)

        self.assertEqual(model.c(), 8)
        self.assertEqual(value(model.c.body), 8)

    def test_rule5(self):
        """Test rule option"""
        model = ConcreteModel()
        model.B = RangeSet(1,4)
        def f(model):
            ans=0
            for i in model.B:
                ans = ans + model.x[i]
            return (ans,1)
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(rule=f)

        self.assertEqual(model.c(), 8)
        self.assertEqual(value(model.c.body), 8)

    def test_dim(self):
        """Test dim method"""
        model = ConcreteModel()
        model.c = Constraint()

        self.assertEqual(model.c.dim(),0)

    def test_keys_empty(self):
        """Test keys method"""
        model = ConcreteModel()
        model.c = Constraint()

        self.assertEqual(list(model.c.keys()),[])

    def test_len_empty(self):
        """Test len method"""
        model = ConcreteModel()
        model.c = Constraint()

        self.assertEqual(len(model.c), 0)

    def test_None_key(self):
        """Test keys method"""
        model = ConcreteModel()
        model.x = Var()
        model.c = Constraint(expr=model.x == 1)
        self.assertEqual(list(model.c.keys()),[None])
        self.assertEqual(id(model.c),id(model.c[None]))

    def test_len(self):
        """Test len method"""
        model = AbstractModel()
        model.x = Var()
        model.c = Constraint(rule=lambda m: m.x == 1)
        self.assertEqual(len(model.c),0)
        inst = model.create_instance()
        self.assertEqual(len(inst.c),1)

class TestArrayCon(unittest.TestCase):

    def create_model(self):
        model = ConcreteModel()
        model.A = Set(initialize=[1,2,3,4])
        return model

    def test_rule_option1(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        def f(model, i):
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(model.c[2](), 16)
        self.assertEqual(len(model.c), 4)

    def test_old_rule_option1(self):
        """Test rule option"""
        model = self.create_model()
        buffer = LogBuffer('pyomo.core', logging.WARNING)
        model.B = RangeSet(1,4)
        def f(model, i):
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(model.c[2](), 16)
        self.assertEqual(len(model.c), 4)

    def test_rule_option2(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        def f(model, i):
            if i%2 == 0:
                return Constraint.Skip
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(len(model.c), 2)

    def test_rule_option3(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        def f(model, i):
            if i%2 == 0:
                return Constraint.Skip
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(len(model.c), 2)

    def test_rule_option2a(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        @simple_constraint_rule
        def f(model, i):
            if i%2 == 0:
                return None
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(len(model.c), 2)

    def test_rule_option3a(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        @simple_constraint_rule
        def f(model, i):
            if i%2 == 0:
                return None
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(len(model.c), 2)

    def test_dim(self):
        """Test dim method"""
        model = self.create_model()
        model.c = Constraint(model.A)

        self.assertEqual(model.c.dim(),1)

    def test_keys(self):
        """Test keys method"""
        model = self.create_model()
        model.c = Constraint(model.A)

        self.assertEqual(len(list(model.c.keys())),0)

    def test_len(self):
        """Test len method"""
        model = self.create_model()
        model.c = Constraint(model.A)
        self.assertEqual(len(model.c),0)

        model = self.create_model()
        model.B = RangeSet(1,4)
        """Test rule option"""
        def f(model):
            ans=0
            for i in model.B:
                ans = ans + model.x[i]
            ans = ans==2
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(rule=f)

        self.assertEqual(len(model.c),1)


class TestConList(unittest.TestCase):

    def create_model(self):
        model = ConcreteModel()
        model.A = Set(initialize=[1,2,3,4])
        return model

    #
    # Tests that adding Constraint.Skip increments
    # the internal counter but does not create an object
    #
    def test_conlist_skip(self):
        model = ConcreteModel()
        model.x = Var()
        model.c = ConstraintList()
        self.assertTrue(1 not in model.c)
        self.assertEqual(len(model.c), 0)
        model.c.add(Constraint.Skip)
        self.assertTrue(1 not in model.c)
        self.assertEqual(len(model.c), 0)
        model.c.add(model.x >= 1)
        self.assertTrue(1 not in model.c)
        self.assertTrue(2 in model.c)
        self.assertEqual(len(model.c), 1)

    def test_rule_option1(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        def f(model, i):
            if i > 4:
                return ConstraintList.End
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = ConstraintList(rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(model.c[2](), 16)
        self.assertEqual(len(model.c), 4)

    def test_rule_option2(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        def f(model, i):
            if i > 2:
                return ConstraintList.End
            i = 2*i - 1
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = ConstraintList(rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(len(model.c), 2)

    def test_rule_option1a(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        @simple_constraintlist_rule
        def f(model, i):
            if i > 4:
                return None
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = ConstraintList(rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(model.c[2](), 16)
        self.assertEqual(len(model.c), 4)

    def test_rule_option2a(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        @simple_constraintlist_rule
        def f(model, i):
            if i > 2:
                return None
            i = 2*i - 1
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = ConstraintList(rule=f)

        self.assertEqual(model.c[1](), 8)
        self.assertEqual(len(model.c), 2)

    def test_rule_option3(self):
        """Test rule option"""
        model = self.create_model()
        model.y = Var(initialize=2)
        def f(model):
            yield model.y <= 0
            yield 2*model.y <= 0
            yield 2*model.y <= 0
            yield ConstraintList.End
        model.c = ConstraintList(rule=f)
        self.assertEqual(len(model.c), 3)
        self.assertEqual(model.c[1](), 2)
        model.d = ConstraintList(rule=f(model))
        self.assertEqual(len(model.d), 3)
        self.assertEqual(model.d[1](), 2)

    def test_rule_option4(self):
        """Test rule option"""
        model = self.create_model()
        model.y = Var(initialize=2)
        model.c = ConstraintList(rule=((i+1)*model.y >= 0 for i in range(3)))
        self.assertEqual(len(model.c), 3)
        self.assertEqual(model.c[1](), 2)

    def test_dim(self):
        """Test dim method"""
        model = self.create_model()
        model.c = ConstraintList()

        self.assertEqual(model.c.dim(),1)

    def test_keys(self):
        """Test keys method"""
        model = self.create_model()
        model.c = ConstraintList()

        self.assertEqual(len(list(model.c.keys())),0)

    def test_len(self):
        """Test len method"""
        model = self.create_model()
        model.c = ConstraintList()

        self.assertEqual(len(model.c),0)


class Test2DArrayCon(unittest.TestCase):

    def create_model(self):
        model = ConcreteModel()
        model.A = Set(initialize=[1,2])
        return model

    def test_rule_option(self):
        """Test rule option"""
        model = self.create_model()
        model.B = RangeSet(1,4)
        def f(model, i, j):
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,model.A,rule=f)

        self.assertEqual(model.c[1,1](), 8)
        self.assertEqual(model.c[2,1](), 16)

    def test_old_rule_option(self):
        """Test rule option"""
        model = self.create_model()
        buffer = LogBuffer('pyomo.core', logging.WARNING)
        model.B = RangeSet(1,4)
        def f(model, i, j):
            ans=0
            for j in model.B:
                ans = ans + model.x[j]
            ans *= i
            ans = ans <= 0
            ans = ans >= 0
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(model.A,model.A,rule=f)

        self.assertEqual(model.c[1,1](), 8)
        self.assertEqual(model.c[2,1](), 16)

    def test_dim(self):
        """Test dim method"""
        model = self.create_model()
        model.c = Constraint(model.A,model.A)

        self.assertEqual(model.c.dim(),2)

    def test_keys(self):
        """Test keys method"""
        model = self.create_model()
        model.c = Constraint(model.A,model.A)

        self.assertEqual(len(list(model.c.keys())),0)

    def test_len(self):
        """Test len method"""
        model = self.create_model()
        model.c = Constraint(model.A,model.A)
        self.assertEqual(len(model.c),0)

        model = self.create_model()
        model.B = RangeSet(1,4)
        """Test rule option"""
        def f(model):
            ans=0
            for i in model.B:
                ans = ans + model.x[i]
            ans = ans==2
            return ans
        model.x = Var(model.B, initialize=2)
        model.c = Constraint(rule=f)

        self.assertEqual(len(model.c),1)

class MiscConTests(unittest.TestCase):

    def test_slack_methods(self):
        model = ConcreteModel()
        model.x = Var(initialize=2.0)
        L = -1.0
        U = 5.0
        model.cL = Constraint(expr=model.x**2 >= L)
        self.assertEqual(model.cL.lslack(), -5.0)
        self.assertEqual(model.cL.uslack(), float('inf'))
        model.cU = Constraint(expr=model.x**2 <= U)
        self.assertEqual(model.cU.lslack(), float('-inf'))
        self.assertEqual(model.cU.uslack(), 1.0)
        model.cR = Constraint(expr=L <= model.x**2 <= U)
        self.assertEqual(model.cR.lslack(), -5.0)
        self.assertEqual(model.cR.uslack(), 1.0)

    def test_constructor(self):
        a = Constraint(name="b")
        self.assertEqual(a.name,"b")
        try:
            a = Constraint(foo="bar")
            self.fail("Can't specify an unexpected constructor option")
        except ValueError:
            pass

    def test_contains(self):
        model=ConcreteModel()
        model.a=Set(initialize=[1,2,3])
        model.b=Constraint(model.a)

        self.assertEqual(2 in model.b,False)
        tmp=[]
        for i in model.b:
            tmp.append(i)
        self.assertEqual(len(tmp),0)

    def test_empty_singleton(self):
        a = Constraint()
        a.construct()
        #
        # Even though we construct a SimpleConstraint,
        # if it is not initialized that means it is "empty"
        # and we should encounter errors when trying to access the
        # _ConstraintData interface methods until we assign
        # something to the constraint.
        #
        self.assertEqual(a._constructed, True)
        self.assertEqual(len(a), 0)
        try:
            a()
            self.fail("Component is empty")
        except ValueError:
            pass
        try:
            a.body
            self.fail("Component is empty")
        except ValueError:
            pass
        try:
            a.lower
            self.fail("Component is empty")
        except ValueError:
            pass
        try:
            a.upper
            self.fail("Component is empty")
        except ValueError:
            pass
        try:
            a.equality
            self.fail("Component is empty")
        except ValueError:
            pass
        try:
            a.strict_lower
            self.fail("Component is empty")
        except ValueError:
            pass
        try:
            a.strict_upper
            self.fail("Component is empty")
        except ValueError:
            pass
        x = Var(initialize=1.0)
        x.construct()
        a.set_value(2 >= x >= 0)
        self.assertEqual(len(a), 1)
        self.assertEqual(a(), 1)
        self.assertEqual(a.body(), 1)
        self.assertEqual(a.lower(), 0)
        self.assertEqual(a.upper(), 2)
        self.assertEqual(a.equality, False)
        self.assertEqual(a.strict_lower, False)
        self.assertEqual(a.strict_upper, False)

    def test_unconstructed_singleton(self):
        a = Constraint()
        self.assertEqual(a._constructed, False)
        self.assertEqual(len(a), 0)
        try:
            a()
            self.fail("Component is unconstructed")
        except ValueError:
            pass
        try:
            a.body
            self.fail("Component is unconstructed")
        except ValueError:
            pass
        try:
            a.lower
            self.fail("Component is unconstructed")
        except ValueError:
            pass
        try:
            a.upper
            self.fail("Component is unconstructed")
        except ValueError:
            pass
        try:
            a.equality
            self.fail("Component is unconstructed")
        except ValueError:
            pass
        try:
            a.strict_lower
            self.fail("Component is unconstructed")
        except ValueError:
            pass
        try:
            a.strict_upper
            self.fail("Component is unconstructed")
        except ValueError:
            pass
        x = Var(initialize=1.0)
        x.construct()
        a.construct()
        a.set_value(2 >= x >= 0)
        self.assertEqual(len(a), 1)
        self.assertEqual(a(), 1)
        self.assertEqual(a.body(), 1)
        self.assertEqual(a.lower(), 0)
        self.assertEqual(a.upper(), 2)
        self.assertEqual(a.equality, False)
        self.assertEqual(a.strict_lower, False)
        self.assertEqual(a.strict_upper, False)

    def test_rule(self):
        def rule1(model):
            return Constraint.Skip
        model = ConcreteModel()
        try:
            model.o = Constraint(rule=rule1)
        except Exception:
            e = sys.exc_info()[1]
            self.fail("Failure to create empty constraint: %s" % str(e))
        #
        def rule1(model):
            return (0.0,model.x,2.0)
        model = ConcreteModel()
        model.x = Var(initialize=1.1)
        model.o = Constraint(rule=rule1)

        self.assertEqual(model.o(),1.1)
        #
        def rule1(model, i):
            return Constraint.Skip
        model = ConcreteModel()
        model.a = Set(initialize=[1,2,3])
        try:
            model.o = Constraint(model.a,rule=rule1)
        except Exception:
            self.fail("Error generating empty constraint")

        #
        def rule1(model):
            return (0.0,1.1,2.0,None)
        model = ConcreteModel()
        try:
            model.o = Constraint(rule=rule1)
            self.fail("Can only return tuples of length 2 or 3")
        except ValueError:
            pass

    def test_chainedInequalityError(self):
        m = ConcreteModel()
        m.x = Var()
        a = m.x <= 0
        if m.x <= 0:
            pass
        m.c = Constraint()
        self.assertRaisesRegexp(
            TypeError, "contains non-constant terms \(variables\) "
            "appearing in a Boolean context", m.c.set_value, a)

    def test_tuple_constraint_create(self):
        def rule1(model):
            return (0.0,model.x)
        model = ConcreteModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)

        #
        def rule1(model):
            return (model.y,model.x,model.z)
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(ValueError, model.create_instance)
        #

    def test_expression_constructor_coverage(self):
        def rule1(model):
            expr = model.x
            expr = expr == 0.0
            expr = expr >= 1.0
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(TypeError, model.create_instance)
        #
        def rule1(model):
            expr = model.U >= model.x
            expr = expr >= model.L
            return expr
        model = ConcreteModel()
        model.x = Var()
        model.L = Param(initialize=0)
        model.U = Param(initialize=1)
        model.o = Constraint(rule=rule1)

        #
        def rule1(model):
            expr = model.x <= model.z
            expr = expr >= model.y
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(ValueError, model.create_instance)
        #
        def rule1(model):
            expr = model.x >= model.z
            expr = model.y >= expr
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(ValueError, model.create_instance)
        #
        def rule1(model):
            expr = model.y <= model.x
            expr = model.y >= expr
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(ValueError, model.create_instance)
        #
        def rule1(model):
            expr = model.x >= model.L
            return expr
        model = ConcreteModel()
        model.x = Var()
        model.L = Param(initialize=0)
        model.o = Constraint(rule=rule1)

        #
        def rule1(model):
            expr = model.U >= model.x
            return expr
        model = ConcreteModel()
        model.x = Var()
        model.U = Param(initialize=0)
        model.o = Constraint(rule=rule1)

        #
        def rule1(model):
            expr=model.x
            expr = expr == 0.0
            expr = expr <= 1.0
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(TypeError, model.create_instance)
        #
        def rule1(model):
            expr = model.U <= model.x
            expr = expr <= model.L
            return expr
        model = ConcreteModel()
        model.x = Var()
        model.L = Param(initialize=0)
        model.U = Param(initialize=1)
        model.o = Constraint(rule=rule1)

        #
        def rule1(model):
            expr = model.x >= model.z
            expr = expr <= model.y
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(ValueError, model.create_instance)
        #
        def rule1(model):
            expr = model.x <= model.z
            expr = model.y <= expr
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.z = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(ValueError, model.create_instance)
        #
        def rule1(model):
            expr = model.y >= model.x
            expr = model.y <= expr
            return expr
        model = AbstractModel()
        model.x = Var()
        model.y = Var()
        model.o = Constraint(rule=rule1)
        self.assertRaises(ValueError, model.create_instance)
        #
        def rule1(model):
            expr = model.x <= model.L
            return expr
        model = ConcreteModel()
        model.x = Var()
        model.L = Param(initialize=0)
        model.o = Constraint(rule=rule1)

        #
        def rule1(model):
            expr = model.U <= model.x
            return expr
        model = ConcreteModel()
        model.x = Var()
        model.U = Param(initialize=0)
        model.o = Constraint(rule=rule1)

        #
        def rule1(model):
            return model.x+model.x
        model = ConcreteModel()
        model.x = Var()
        try:
            model.o = Constraint(rule=rule1)
            self.fail("Cannot return an unbounded expression")
        except ValueError:
            pass
        #

if __name__ == "__main__":
    unittest.main()
