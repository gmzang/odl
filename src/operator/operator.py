# -*- coding: utf-8 -*-
"""
operator.py -- functional analytic operators

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

from __future__ import unicode_literals, print_function, division, absolute_import
from future.builtins import object
from future import standard_library
standard_library.install_aliases()

from numbers import Number
from abc import ABCMeta, abstractmethod, abstractproperty


class Operator(object):
    """Abstract operator
    """
    __metaclass__ = ABCMeta #Set as abstract

    @abstractmethod
    def applyImpl(self, rhs, out):
        """Apply the operator, abstract
        """

    @abstractproperty
    def domain(self):
        """Get the domain of the operator
        """

    @abstractproperty
    def range(self):
        """Get the range of the operator
        """

    def getDerivative(self, point):
        """ Get the derivative of this operator in some point
        """
        raise NotImplementedError("getDerivative not implemented for this operator ({})".format(self))
        
    #Implicitly defined operators
    def apply(self, rhs, out):
        if not self.domain.isMember(rhs): 
            raise TypeError('rhs ({}) is not in the domain of this operator ({})'.format(rhs, self))

        if not self.range.isMember(out): 
            raise TypeError('out ({}) is not in the range of this operator ({})'.format(out, self))
        
        if rhs is out:
            raise ValueError('rhs ({}) is the same as out ({}) operators do not permit aliased arguments'.format(rhs,out))

        self.applyImpl(rhs, out)

    def __call__(self, rhs):
        """Shorthand for self.apply(rhs)
        """
        tmp = self.range.empty()
        self.apply(rhs, tmp)
        return tmp

    def __add__(self, other):
        """Operator addition (pointwise)
        """

        if isinstance(other, Operator):
            return OperatorSum(self, other)
        else:
            raise TypeError('Expected an operator')

    def __mul__(self, other):
        """Left multiplication of operators with scalars (a*A)(x) = a*A(x)
        """

        if isinstance(other, Number):
            return OperatorLeftScalarMultiplication(self, other)
        else:
            raise TypeError('Expected a scalar')

    def __rmul__(self, other):
        """Right multiplication of operators with scalars (A*a)(x) = A(a*x)
        """

        if isinstance(other, Number):
            return OperatorRightScalarMultiplication(self, other)
        else:
            raise TypeError('Expected a scalar')

    def __str__(self):
        return "Operator " + self.__class__.__name__ + ": " + str(self.domain) + "->" + str(self.range)


class OperatorSum(Operator):
    """ Expression type for the sum of operators:

    OperatorSum(op1,op2)(x) = op1(x) + op2(x)
    """
    def __init__(self, op1, op2):
        if op1.range != op2.range:
            raise TypeError("Ranges ({}, {}) of operators are not equal".format(op1.range, op2.range))

        if op1.domain != op2.domain:
            raise TypeError("Domains ({}, {}) of operators are not equal".format(op1.domain, op2.domain))

        self.op1 = op1
        self.op2 = op2

    def applyImpl(self, rhs, out):
        tmp = self.range.empty()
        self.op1.applyImpl(rhs, out)
        self.op2.applyImpl(rhs, tmp)
        out += tmp

    @property
    def domain(self):
        return self.op1.domain

    @property
    def range(self):
        return self.op1.range

class OperatorComposition(Operator):
    """Expression type for the composition of operators

    OperatorComposition(left,right)(x) = left(right(x))
    """

    def __init__(self, left, right):
        if right.range != left.domain:
            raise TypeError("Range of right operator ({}) does not equal domain of left operator ({})".format(right.range,left.domain))

        self.left = left
        self.right = right

    def applyImpl(self, rhs, out):
        tmp = self.right.range.empty()
        self.right.applyImpl(rhs, tmp)
        self.left.applyImpl(tmp, out)
        
    @property
    def domain(self):
        return self.right.domain

    @property
    def range(self):
        return self.left.range

class OperatorPointwiseProduct(Operator):    
    """Pointwise multiplication of operators defined on Banach Algebras (with pointwise multiplication)
    
    OperatorPointwiseProduct(op1,op2)(x) = op1(x) * op2(x)
    """

    def __init__(self, op1, op2):
        if op1.range != op2.range:
            raise TypeError("Ranges ({}, {}) of operators are not equal".format(op1.range, op2.range))

        if op1.domain != op2.domain:
            raise TypeError("Domains ({}, {}) of operators are not equal".format(op1.domain, op2.domain))

        self.op1 = op1
        self.op2 = op2

    def applyImpl(self, rhs, out):
        tmp = self.op2.range.empty()
        self.op1.applyImpl(rhs, out)
        self.op2.applyImpl(rhs, tmp)
        out *= tmp

    @property
    def domain(self):
        return self.op1.domain

    @property
    def range(self):
        return self.op1.range

class OperatorLeftScalarMultiplication(Operator):
    """Expression type for the left multiplication of operators with scalars
    
    OperatorLeftScalarMultiplication(op,scalar)(x) = scalar * op(x)
    """

    def __init__(self, op, scalar):
        if not op.range.field.isMember(scalar):
            raise TypeError("Scalar ({}) not compatible with field of range ({}) of operator".format(scalar,op.range.field))

        self.op = op
        self.scalar = scalar

    def applyImpl(self, rhs, out):
        self.op.applyImpl(rhs, out)
        out *= self.scalar

    @property
    def domain(self):
        return self.op.domain

    @property
    def range(self):
        return self.op.range

class OperatorRightScalarMultiplication(Operator):
    """Expression type for the right multiplication of operators with scalars.

    Typically slower than left multiplication since this requires a copy

    OperatorRightScalarMultiplication(op,scalar)(x) = op(scalar * x)
    """

    def __init__(self, op, scalar):
        if not op.domain.field.isMember(scalar):
            raise TypeError("Scalar ({}) not compatible with field of domain ({}) of operator".format(scalar,op.domain.field))

        self.op = op
        self.scalar = scalar

    def applyImpl(self, rhs, out):
        tmp = rhs.copy()
        tmp *= self.scalar
        self.op.applyImpl(tmp, out)

    @property
    def domain(self):
        return self.op.domain

    @property
    def range(self):
        return self.op.range

    
class LinearOperator(Operator):
    """ Linear operator, satisfies A(ax+by)=a*A(x)+b*A(y)
    """
    
    @abstractmethod
    def applyAdjointImpl(self, rhs, out):
        """Apply the adjoint of the operator, abstract should be implemented by subclasses.

        Public callers should instead use applyAdjoint which provides type checking.
        """

    #Implicitly defined operators
    @property
    def T(self):
        return OperatorAdjoint(self)

    def getDerivative(self, point):
        """ Get the derivative of this operator in some point. The derivative of linear operators is the operator itself.
        """
        return self

    def applyAdjoint(self, rhs, out):
        if not self.range.isMember(rhs): 
            raise TypeError('rhs ({}) is not in the domain of this operators ({}) adjoint'.format(rhs,self))
        if not self.domain.isMember(out): 
            raise TypeError('out ({}) is not in the range of this operators ({}) adjoint'.format(out,self))
        if rhs is out:
            raise ValueError('rhs ({}) is the same as out ({}). Operators do not permit aliased arguments'.format(rhs,out))

        self.applyAdjointImpl(rhs, out)

    def __add__(self, other):
        """Operator addition

        (self + other)(x) = self(x) + other(x)
        """

        if isinstance(other, LinearOperator): #Specialization if both are linear
            return LinearOperatorSum(self, other)
        else:
            return Operator.__add__(self, other)

    def __mul__(self, other):
        """Multiplication of operators with scalars.
        
        (a*A)(x) = a*A(x)
        (A*a)(x) = a*A(x)
        """

        if isinstance(other, Number):
            return LinearOperatorScalarMultiplication(self, other)
        else:
            raise TypeError('Expected an operator or a scalar')

    __rmul__ = __mul__ #Should we have this?


class SelfAdjointOperator(LinearOperator):
    """ Special case of self adjoint operators where A(x) = A.T(x)
    """
    
    __metaclass__ = ABCMeta #Set as abstract

    def applyAdjointImpl(self, rhs, out):
        self.applyImpl(rhs, out)


class OperatorAdjoint(LinearOperator):
    """Expression type for the adjoint of an operator
    """

    def __init__(self, op):
        if not isinstance(op, LinearOperator):
            raise TypeError('op ({}) is not a LinearOperator. OperatorAdjoint is only defined for LinearOperators'.format(op))

        self.op = op

    def applyImpl(self, rhs, out):
        self.op.applyAdjointImpl(rhs, out)
    
    def applyAdjointImpl(self, rhs, out):
        self.op.applyImpl(rhs, out)

    @property
    def domain(self):
        return self.op.range

    @property
    def range(self):
        return self.op.domain


class LinearOperatorSum(OperatorSum, LinearOperator):
    """Expression type for the sum of linear operators
    """
    def __init__(self, op1, op2):
        if not isinstance(op1, LinearOperator):
            raise TypeError('op1 ({}) is not a LinearOperator. LinearOperatorSum is only defined for LinearOperators'.format(op1))
        if not isinstance(op2, LinearOperator):
            raise TypeError('op2 ({}) is not a LinearOperator. LinearOperatorSum is only defined for LinearOperators'.format(op2))

        OperatorSum.__init__(self, op1, op2)

    def applyAdjointImpl(self, rhs, out):
        tmp = self.domain.empty()
        self.op1.applyAdjointImpl(rhs, out)
        self.op2.applyAdjointImpl(rhs, tmp)
        out += tmp


class LinearOperatorComposition(OperatorComposition, LinearOperator):
    """Expression type for the composition of operators
    """

    def __init__(self, left, right):
        if not isinstance(left, LinearOperator):
            raise TypeError('left ({}) is not a LinearOperator. LinearOperatorComposition is only defined for LinearOperators'.format(left))
        if not isinstance(right, LinearOperator):
            raise TypeError('right ({}) is not a LinearOperator. LinearOperatorComposition is only defined for LinearOperators'.format(right))

        OperatorComposition.__init__(self, left, right)
    
    def applyAdjointImpl(self, rhs, out):
        tmp = self.left.domain.empty()
        self.left.applyAdjoint(rhs, tmp)
        self.right.applyAdjoint(tmp, out)


class LinearOperatorScalarMultiplication(OperatorLeftScalarMultiplication, LinearOperator):
    """Expression type for the multiplication of operators with scalars
    """

    def __init__(self, op, scalar):
        if not isinstance(op, LinearOperator):
            raise TypeError('op ({}) is not a LinearOperator. LinearOperatorScalarMultiplication is only defined for LinearOperators'.format(op))

        OperatorLeftScalarMultiplication.__init__(self, op, scalar)
    
    def applyAdjointImpl(self, rhs, out):
        self.op.applyAdjointImpl(rhs, out)
        out *= self.scalar
