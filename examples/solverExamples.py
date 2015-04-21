# -*- coding: utf-8 -*-
"""
simple_test_astra.py -- a simple test script

Copyright 2014, 2015 Holger Kohr

This file is part of RL.

RL is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RL is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RL.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division, print_function, unicode_literals, absolute_import
from future import standard_library
standard_library.install_aliases()


def landweberBase(operator, x, rhs, iterations=1, omega=1):
    """ Straightforward implementation of Landweber iteration
    """
    for _ in range(iterations):
        x = x - omega * operator.T(operator(x)-rhs)
        

def conjugateGradientBase(op, x, rhs, iterations=1):
    """ Non-optimized CGN
    """
    d = rhs - op(x)
    p = op.T(d)
    s = p.copy()

    for _ in range(iterations):
        q = op(p)                       
        norms2 = s.normSq()
        a = norms2 / q.normSq()
        x = x + a*p                    
        d = d - a*q                  
        s = op.T(d)
        b = s.normSq()/norms2
        p = s + b*p