"""Unit tests for transaction creation/modification."""
# -*- coding: iso-8859-1 -*-

from unittest import TestCase, makeSuite, TestSuite
import unittest
from datetime import *
import datetime

from magot.model2 import *
from magot.refdata import *

def makeAccounts(self):
    # create all accounts
    self.root = Account(name='Accounts')
    self.checking = EntryAccount(parent=self.root, name='Checking', type=MovementType.DEBIT)
    self.income = EntryAccount(parent=self.root, name='Income', type=MovementType.CREDIT)

    # set all initial balances
    self.checking.makeInitialTransaction(self.income, Money(1))
    self.checking.makeInitialTransaction(self.income, Money(2))


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)

    def test_account(self):
        assert self.checking.parent is self.income.parent is self.root
        b = self.checking.balance
        c = self.income.balance
        assert b == c
        d = self.checking.balanceMTD
        e = self.income.balanceMTD
        assert d == e == Money.ZERO

if __name__ == '__main__':
    unittest.main()
