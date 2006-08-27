"""Unit tests for multi-dimension analysis."""

from unittest import TestCase, makeSuite, TestSuite
import unittest

from magot.refdata import *
from magot.model import RootAccount, Account, Transaction, Dimension, DimensionMember


def makeAccounts(self):
    # create all accounts under the root account
    self.root = RootAccount(name='Accounts')
    
    # ===========================================================================
    # Define the "Apartment" Dimension in order to track all transactions dealing with apartments.
    # ===========================================================================
    apartmentDim = Dimension(name="Apartment")
    
    # Add 1 member for this dimension
    A100 = self.A100 = DimensionMember(code="A100", desc="Apartment at adress 100")
    apartmentDim.addMember(A100)
    

    # ===========================================================================
    # ASSETS
    # ===========================================================================
    self.asset = Account(parent=self.root, name='Asset', type=MovementType.DEBIT)
    
    bank = self.bank = Account(parent=self.asset, name='Bank')
    
    apart = Account(parent=self.asset, name='All apartments')
    # This account deals with the 'apartmentDim' Dimension
    apart100 = self.apart100 = Account(parent=apart, name='Apartment 100', dimensions=[A100])
    
    
    # ===========================================================================
    # EXPENSES
    # ===========================================================================
    self.expense = Account(parent=self.root, name='Expense', type=MovementType.DEBIT)   

    warranty = Account(parent=self.expense, name='Warranty')
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensions=[A100])
    
    interests = Account(parent=self.expense, name='Interests')
    interests100 = self.interests100 = Account(parent=interests, name='Interests 100', dimensions=[A100])
    
    syndic = Account(parent=self.expense, name='Syndic')
    syndic100 = self.syndic100 = Account(parent=syndic, name='Syndic 100', dimensions=[A100])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensions=[A100])
    
    imposition = self.imposition = Account(parent=self.expense, name='Imposition')


    # ===========================================================================
    # INCOMES
    # ===========================================================================
    self.income = Account(parent=self.root, name='Income', type=MovementType.CREDIT)
    
    rent = Account(parent=self.income, name='Rent')
    rent100 = self.rent100 = Account(parent=rent, name='Rent 100', dimensions=[A100])
    
    gain = Account(parent=self.income, name='Gain')
    gain100 = self.gain100 = Account(parent=gain, name='Gain 100', dimensions=[A100])
      

    # ===========================================================================
    # LIABILITIES
    # ===========================================================================
    self.liability = Account(parent=self.root, name='Liability', type=MovementType.CREDIT)
    
    loan = Account(parent=self.liability, name='Loan')
    loan100 = self.loan100 = Account(parent=loan, name='Loan 100', dimensions=[A100])


    # ===========================================================================
    # EQUITY
    # ===========================================================================
    equity = self.equity = Account(parent=self.root, name='Equity', type=MovementType.CREDIT)  
    self.bank.makeInitialTransaction(self.equity, Money(100000), Date(2005,1,1))


    # ===========================================================================
    # Make transactions to buy and rent an apartment
    # ===========================================================================

    Transaction(Date(2005,1,2), 'contract a loan', bank, loan100, 150000)

    Transaction(Date(2005,1,3), 'buy an apartment', apart100, bank, 200000)
    Transaction(Date(2005,1,3), 'pay VAT', taxes100, bank, 14000)
    
    Transaction(Date(2005,1,4), 'pay 1 year warranty', warranty100, bank, 50)
    Transaction(Date(2005,1,4), 'pay 1 year property tax', taxes100, bank, 300)
    Transaction(Date(2005,1,4), 'profit 1 year imposition reduction', imposition, taxes100, 5000)
    # This tx is not related to the apartment
    Transaction(Date(2005,1,4), 'pay 1 year imposition', imposition, bank, 10000)
    
    Transaction(Date(2005,1,5), 'pay loan interests', interests100, bank, 500*12)
    Transaction(Date(2005,1,5), 'pay loan principal', loan100, bank, 500*12)
    Transaction(Date(2005,1,5), 'pay syndic', syndic100, bank, 100*12)
    Transaction(Date(2005,1,5), 'rent the appartment', bank, rent100, 600*12)
    
    Transaction(Date(2005,12,31), '1 year gain capital 6%', apart100, gain100, 200000*0.06)


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)
        self.pp()

    def test_real_estate(self):
        self.root.traverseHierarchy(self.viewUnderDimension, False)

    def viewUnderDimension(self, account, depth):
        if self.A100 in account.dimensions:
            self.printAccount(account, depth)
    
    def printAccount(self, account, depth):
        print '\t'*depth, account

    def pp(self):           
        self.root.traverseHierarchy(self.printAccount, False)
        

if __name__ == '__main__':
    unittest.main()
