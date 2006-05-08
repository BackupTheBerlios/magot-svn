"""Unit tests for transaction creation/modification."""
# -*- coding: iso-8859-1 -*-

from unittest import TestCase, makeSuite, TestSuite
import unittest

from magot.model2 import *
from magot.refdata import *

def makeAccounts(self):
    # create all accounts
    self.root = RootAccount(name='Accounts')
    self.checking = Account(parent=self.root, name='Checking', type=MovementType.DEBIT)
    self.axa = Account(parent=self.checking, name='Axa')
    
    self.income = Account(parent=self.root, name='Income', type=MovementType.CREDIT)
    self.jems = Account(parent=self.income, name='Jems')

    # set all initial balances
    self.checking.makeInitialTransaction(self.income, Money(1))
    self.axa.makeInitialTransaction(self.jems, Money(1000))
    self.checking.makeInitialTransaction(self.income, Money(2))
    self.axa.makeInitialTransaction(self.jems, Money(2000))


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)

    def test_account(self):
        assert self.checking.parent is self.income.parent is self.root
        b = self.checking.balance
        bp = self.checking.balance
        c = self.income.balance
        assert b == c
        d = self.checking.balanceMTD
        e = self.income.balanceMTD
        assert d == e == Money.Zero

if __name__ == '__main__':
    unittest.main()
