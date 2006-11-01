"""Unit tests for uni-dimension analysis."""

import cPickle
from unittest import TestCase, makeSuite, TestSuite, main

from magot.refdata import *
from magot.model import *
from magot.dimension import *
from test_multi_dimensions import makeDimensionMembers


def makeAccounts(self):

    makeDimensionMembers(self)
    A100 = self.A100
    A400 = self.A400
    
    # create all accounts under the root account
    self.root = RootAccount(name='Accounts')

    # ===========================================================================
    # ASSETS
    # ===========================================================================
    self.asset = Account(parent=self.root, name='Asset', type=TYPE_ASSET)
    
    bank = self.bank = Account(parent=self.asset, name='Bank')
    
    apart = Account(parent=self.asset, name='All apartments')
    # This account deals with the 'apartmentDim' Dimension
    apart100 = self.apart100 = Account(parent=apart, name='Apartment 100', dimensionMembers=[A100])
    apart400 = self.apart400 = Account(parent=apart, name='Apartment 400', dimensionMembers=[A400])

    
    # ===========================================================================
    # EXPENSES
    # ===========================================================================
    self.expense = Account(parent=self.root, name='Expense', type=TYPE_EXPENSE)

    warranty = Account(parent=self.expense, name='Warranty')
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensionMembers=[A100])
    warranty400 = self.warranty400 = Account(parent=warranty, name='Warranty 400', dimensionMembers=[A400])
    
    interests = Account(parent=self.expense, name='Interests')
    interests100 = self.interests100 = Account(parent=interests, name='Interests 100', dimensionMembers=[A100])
    interests400 = self.interests400 = Account(parent=interests, name='Interests 400', dimensionMembers=[A400])
    
    syndic = Account(parent=self.expense, name='Syndic')
    syndic100 = self.syndic100 = Account(parent=syndic, name='Syndic 100', dimensionMembers=[A100])
    syndic400 = self.syndic400 = Account(parent=syndic, name='Syndic 400', dimensionMembers=[A400])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensionMembers=[A100])
    taxes400 = self.taxes400 = Account(parent=taxes, name='Taxes 400', dimensionMembers=[A400])
    
    imposition = self.imposition = Account(parent=self.expense, name='Imposition')
    imposition100 = self.imposition100 = Account(parent=self.imposition, name='Imposition 100', dimensionMembers=[A100])
    imposition400 = self.imposition400 = Account(parent=self.imposition, name='Imposition 400', dimensionMembers=[A400])


    # ===========================================================================
    # INCOMES
    # ===========================================================================
    self.income = Account(parent=self.root, name='Income', type=TYPE_INCOME)

    rent = Account(parent=self.income, name='Rent')
    rent100 = self.rent100 = Account(parent=rent, name='Rent 100', dimensionMembers=[A100])
    rent400 = self.rent400 = Account(parent=rent, name='Rent 400', dimensionMembers=[A400])
    
    gain = Account(parent=self.income, name='Gain')
    gain100 = self.gain100 = Account(parent=gain, name='Gain 100', dimensionMembers=[A100])
    gain400 = self.gain400 = Account(parent=gain, name='Gain 400', dimensionMembers=[A400])
      

    # ===========================================================================
    # LIABILITIES
    # ===========================================================================
    self.liability = Account(parent=self.root, name='Liability', type=TYPE_LIABILITY)
    
    loan = Account(parent=self.liability, name='Loan')
    loan100 = self.loan100 = Account(parent=loan, name='Loan 100', dimensionMembers=[A100])
    loan400 = self.loan400 = Account(parent=loan, name='Loan 400', dimensionMembers=[A400])


    # ===========================================================================
    # EQUITY
    # ===========================================================================
    equity = self.equity = Account(parent=self.root, name='Equity', type=TYPE_EQUITY)
    self.bank.makeInitialTransaction(self.equity, Money(400000), Date(2005,1,1))


    # ===========================================================================
    # Make transactions to buy and rent an apartment
    # ===========================================================================

    # 2005
    Transaction(Date(2005,1,2), 'contract a loan', bank, loan100, 150000)

    Transaction(Date(2005,1,3), 'buy an apartment', apart100, bank, 400000)
    Transaction(Date(2005,1,3), 'pay VAT', taxes100, bank, 14000)
    
    Transaction(Date(2005,1,4), 'pay 1 year warranty', warranty100, bank, 60)
    Transaction(Date(2005,1,4), 'pay 1 year property tax', taxes100, bank, 300)
    Transaction(Date(2005,1,4), 'profit 1 year imposition reduction', imposition100, taxes100, 5000)
    # This tx is not related to the apartment
    Transaction(Date(2005,1,4), 'pay 1 year imposition', imposition, bank, 10000)
    
    Transaction(Date(2005,1,5), 'pay loan interests', interests100, bank, 500*12)
    Transaction(Date(2005,1,5), 'pay loan principal', loan100, bank, 500*12)
    Transaction(Date(2005,1,5), 'pay syndic', syndic100, bank, 100*12)
    Transaction(Date(2005,1,5), 'rent the appartment', bank, rent100, 600*12)
    
    Transaction(Date(2005,12,31), '1 year gain capital 5%', apart100, gain100, 400000*0.05)

    # 2006
    Transaction(Date(2006,1,4), 'pay 1 year warranty', warranty100, bank, 60)
    Transaction(Date(2006,1,4), 'pay 1 year property tax', taxes100, bank, 300)
    Transaction(Date(2006,1,4), 'profit 1 year imposition reduction', imposition100, taxes100, 5000)
    
    Transaction(Date(2006,1,4), 'pay 1 year imposition', imposition, bank, 10000)
    
    Transaction(Date(2006,1,5), 'pay loan interests', interests100, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay loan principal', loan100, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay syndic', syndic100, bank, 100*12)
    Transaction(Date(2006,1,5), 'rent the appartment', bank, rent100, 600*12)
    
    Transaction(Date(2006,12,31), '1 year gain capital 6%', apart100, gain100, 210000*0.06)

    # ===========================================================================
    # Make transactions as of 2006 to buy and rent another apartment
    # ===========================================================================

    Transaction(Date(2006,1,2), 'contract a loan', bank, loan400, 150000)

    Transaction(Date(2006,1,3), 'buy an apartment', apart400, bank, 400000)
    Transaction(Date(2006,1,3), 'pay VAT', taxes400, bank, 14000)

    Transaction(Date(2006,1,4), 'pay 1 year warranty', warranty400, bank, 50)
    Transaction(Date(2006,1,4), 'pay 1 year property tax', taxes400, bank, 300)
    Transaction(Date(2006,1,4), 'profit 1 year imposition reduction', imposition400, taxes400, 5000)
    # This tx is not related to the apartment
    Transaction(Date(2006,1,4), 'pay 1 year imposition', imposition, bank, 10000)
    
    Transaction(Date(2006,1,5), 'pay loan interests', interests400, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay loan principal', loan400, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay syndic', syndic400, bank, 100*12)
    Transaction(Date(2006,1,5), 'rent the appartment', bank, rent400, 600*12)

    Transaction(Date(2006,12,31), '1 year gain capital 5%', apart400, gain400, 400000*0.06)


class TestTransaction(TestCase):

    def setUp(self):
        makeAccounts(self)
        print "============================================================"
        print "Original account hierarchy"
        print "============================================================"
        pprintHierarchy(self.root)

    def test_real_estate(self):
        viewer = HierarchyViewer(self.root, Date(2006,12,31))
        viewer.viewAccountsUnderDimensions([self.A100])
        viewer.viewAccountsUnderDimensions([self.R2])


def makeDB(filename):
    class A: pass
    a = A()
    makeAccounts(a)
    cPickle.dump(a.root, open(filename,'w'))


if __name__ == '__main__':
    makeDB('tt')
    main()
