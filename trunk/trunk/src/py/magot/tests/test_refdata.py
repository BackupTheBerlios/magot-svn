"""Unit tests for reference data."""

from unittest import TestCase, makeSuite, TestSuite
import unittest
from magot.refdata import *

class TestMoney(TestCase):
   
    def test_money(self):
        a = Money()
        assert a.amount == 0
        self.failUnless(a != 0)
        a = Money.mdl_fromString('100.256')
        b = Money(100.256)
        assert a == b
        self.failUnless(a != 0)
        assert a.amount == 100.256


if __name__ == '__main__':
    unittest.main()
