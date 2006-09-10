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
    
    # Add 2 members for this dimension
    A100 = self.A100 = DimensionMember(code="A100", desc="Apartment at adress 100")
    apartmentDim.addMember(A100)
    A200 = self.A200 = DimensionMember(code="A200", desc="Apartment at adress 200")
    apartmentDim.addMember(A200)
    

    # ===========================================================================
    # ASSETS
    # ===========================================================================
    self.asset = Account(parent=self.root, name='Asset', type=TYPE_ASSET)
    
    bank = self.bank = Account(parent=self.asset, name='Bank')
    
    apart = Account(parent=self.asset, name='All apartments')
    # This account deals with the 'apartmentDim' Dimension
    apart100 = self.apart100 = Account(parent=apart, name='Apartment 100', dimensions=[A100])
    apart200 = self.apart200 = Account(parent=apart, name='Apartment 200', dimensions=[A200])
    
    
    # ===========================================================================
    # EXPENSES
    # ===========================================================================
    self.expense = Account(parent=self.root, name='Expense', type=TYPE_EXPENSE)

    warranty = Account(parent=self.expense, name='Warranty')
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensions=[A100])
    warranty200 = self.warranty200 = Account(parent=warranty, name='Warranty 200', dimensions=[A200])
    
    interests = Account(parent=self.expense, name='Interests')
    interests100 = self.interests100 = Account(parent=interests, name='Interests 100', dimensions=[A100])
    interests200 = self.interests200 = Account(parent=interests, name='Interests 200', dimensions=[A200])
    
    syndic = Account(parent=self.expense, name='Syndic')
    syndic100 = self.syndic100 = Account(parent=syndic, name='Syndic 100', dimensions=[A100])
    syndic200 = self.syndic200 = Account(parent=syndic, name='Syndic 200', dimensions=[A200])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensions=[A100])
    taxes200 = self.taxes200 = Account(parent=taxes, name='Taxes 200', dimensions=[A200])
    
    imposition = self.imposition = Account(parent=self.expense, name='Imposition')


    # ===========================================================================
    # INCOMES
    # ===========================================================================
    self.income = Account(parent=self.root, name='Income', type=TYPE_INCOME)
    
    rent = Account(parent=self.income, name='Rent')
    rent100 = self.rent100 = Account(parent=rent, name='Rent 100', dimensions=[A100])
    rent200 = self.rent200 = Account(parent=rent, name='Rent 200', dimensions=[A200])
    
    gain = Account(parent=self.income, name='Gain')
    gain100 = self.gain100 = Account(parent=gain, name='Gain 100', dimensions=[A100])
    gain200 = self.gain200 = Account(parent=gain, name='Gain 200', dimensions=[A200])
      

    # ===========================================================================
    # LIABILITIES
    # ===========================================================================
    self.liability = Account(parent=self.root, name='Liability', type=TYPE_LIABILITY)
    
    loan = Account(parent=self.liability, name='Loan')
    loan100 = self.loan100 = Account(parent=loan, name='Loan 100', dimensions=[A100])
    loan200 = self.loan200 = Account(parent=loan, name='Loan 200', dimensions=[A200])


    # ===========================================================================
    # EQUITY
    # ===========================================================================
    equity = self.equity = Account(parent=self.root, name='Equity', type=TYPE_EQUITY)
    self.bank.makeInitialTransaction(self.equity, Money(200000), Date(2005,1,1))


    # ===========================================================================
    # Make transactions as of 2005 to buy and rent an apartment
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


    # ===========================================================================
    # Make transactions as of 2006 to buy and rent another apartment
    # ===========================================================================

    Transaction(Date(2006,1,2), 'contract a loan', bank, loan200, 150000)

    Transaction(Date(2006,1,3), 'buy an apartment', apart200, bank, 200000)
    Transaction(Date(2006,1,3), 'pay VAT', taxes200, bank, 14000)

    Transaction(Date(2006,1,4), 'pay 1 year warranty', warranty200, bank, 50)
    Transaction(Date(2006,1,4), 'pay 1 year property tax', taxes200, bank, 300)
    Transaction(Date(2006,1,4), 'profit 1 year imposition reduction', imposition, taxes200, 5000)
    # This tx is not related to the apartment
    Transaction(Date(2006,1,4), 'pay 1 year imposition', imposition, bank, 10000)
    
    Transaction(Date(2006,1,5), 'pay loan interests', interests200, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay loan principal', loan200, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay syndic', syndic200, bank, 100*12)
    Transaction(Date(2006,1,5), 'rent the appartment', bank, rent200, 600*12)
    
    Transaction(Date(2006,12,31), '1 year gain capital 5%', apart200, gain200, 200000*0.05)


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)
        self.pp(self.root)

    def printAccount(self, account, depth):
        print '\t'*depth, account, '=', '\t', account.balance

    def pp(self, root):
        root.traverseHierarchy(self.printAccount, False)

    def test_real_estate(self):
        root = self.rootForApartment = RootAccount(name='root for A100')

        asset = Account(parent=root, name='Asset', type=TYPE_ASSET)
        expense = Account(parent=root, name='Expense', type=TYPE_EXPENSE)
        income = Account(parent=root, name='Income', type=TYPE_INCOME)
        liability = Account(parent=root, name='Liability', type=TYPE_LIABILITY)
        equity = Account(parent=root, name='Equity', type=TYPE_EQUITY)

        self.assetA = Account(parent=asset, name='A100')
        self.expenseA = Account(parent=expense, name='A100')
        self.incomeA = Account(parent=income, name='A100')
        self.liabilityA = Account(parent=liability, name='A100')
        self.equityA = Account(parent=equity, name='A100')
        self.dimension = self.A100
        self.root.traverseHierarchy(self.viewUnderDimension, False)
        Transaction(Date.today(), 'year end', self.equityA, self.expenseA, Money(16550))
        Transaction(Date.today(), 'year end', self.incomeA, self.equityA, Money(19200))

        self.assetA = Account(parent=asset, name='A200')
        self.expenseA = Account(parent=expense, name='A200')
        self.incomeA = Account(parent=income, name='A200')
        self.liabilityA = Account(parent=liability, name='A200')
        self.equityA = Account(parent=equity, name='A200')
        self.dimension = self.A200
        self.root.traverseHierarchy(self.viewUnderDimension, False)
        Transaction(Date.today(), 'year end', self.equityA, self.expenseA, Money(16550))
        Transaction(Date.today(), 'year end', self.incomeA, self.equityA, Money(17200))

        print '================ View under the Apartment dimension ================'
        self.rootForApartment.traverseHierarchy(self.printAccount, False)

    def viewUnderDimension(self, account, depth):
        if self.dimension in account.dimensions:
            self.addSubAccount(self.rootForApartment, account)

    def addSubAccount(self, root, child):
        if child.type == TYPE_ASSET:
            account = Account(self.assetA, name=child.name)
        if child.type == TYPE_EXPENSE:
            account = Account(self.expenseA, name=child.name)
        if child.type == TYPE_INCOME:
            account = Account(self.incomeA, name=child.name)
        if child.type == TYPE_LIABILITY:
            account = Account(self.liabilityA, name=child.name)
            
        account.makeInitialTransaction(self.equityA, child.balance)
            

if __name__ == '__main__':
    unittest.main()
