from unittest import TestCase, makeSuite, TestSuite
import unittest
from peak.api import *
from peak.tests import testRoot
from peak.util import fmtparse

class Thing(model.Element):

    class subexpr(model.Collection):
        referencedType = 'Thing'
        separator = ','
        lowerBound = 1

    mdl_syntax = fmtparse.Alternatives(
        'X',
        fmtparse.Sequence('(', subexpr, ')')
    )

class Expression(model.Element):

    class terms(model.Collection):
        lowerBound = 1
        referencedType = 'Term'
        separator = '+'

    mdl_syntax = fmtparse.Sequence(terms)

class Term(model.Element):

    class factors(model.Collection):
        lowerBound = 1
        referencedType = 'Factor'
        separator = '*'

    mdl_syntax = fmtparse.Sequence(factors)

class Factor(model.Element):

    class constant(model.Attribute):
        referencedType = model.Integer

    class subexpr(model.Attribute):
        referencedType = Expression

    mdl_syntax = fmtparse.Alternatives(
        constant, fmtparse.Sequence('(',subexpr,')')
    )

class XX(model.Element):

    class yy(model.Sequence):
        referencedType = model.Integer
        separator = ','

class parseFmtTest(TestCase):

    def test_SimpleParse(self):
        e = Thing.mdl_fromString('(X,((X)),(X,X,(X)))')
        str(e)
        e = Expression.mdl_fromString('1+2+3')
        assert len(e.terms) == 3
##~         e = Expression.mdl_fromString('11*3+22*2+3')
##~         print Expression.mdl_toString(e)


    def test_FeatureParse(self):
        self.assertEqual( [1,2,3], XX.yy.parse('1,2,3') )

    def test_FeatureFormat(self):
        self.assertEqual( '1,2,3', XX.yy.format([1,2,3]) )

if __name__ == '__main__':
    unittest.main()
