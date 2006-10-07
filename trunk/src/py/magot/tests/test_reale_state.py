"""Unit tests for uni-dimension analysis."""

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
    self.apartmentDim = apartmentDim = Dimension(code="Apartment")
    
    # Add 2 members for this dimension
    A100 = self.A100 = DimensionMember(code="A100", desc="Apartment at adress 100", dimension=apartmentDim)
    A200 = self.A200 = DimensionMember(code="A200", desc="Apartment at adress 200", dimension=apartmentDim)
    

    # ===========================================================================
    # ASSETS
    # ===========================================================================
    self.asset = Account(parent=self.root, name='Asset', type=TYPE_ASSET)
    
    bank = self.bank = Account(parent=self.asset, name='Bank')
    
    apart = Account(parent=self.asset, name='All apartments')
    # This account deals with the 'apartmentDim' Dimension
    apart100 = self.apart100 = Account(parent=apart, name='Apartment 100', dimensionMembers=[A100])
    apart200 = self.apart200 = Account(parent=apart, name='Apartment 200', dimensionMembers=[A200])
    
    
    # ===========================================================================
    # EXPENSES
    # ===========================================================================
    self.expense = Account(parent=self.root, name='Expense', type=TYPE_EXPENSE)

    warranty = Account(parent=self.expense, name='Warranty')
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensionMembers=[A100])
    warranty200 = self.warranty200 = Account(parent=warranty, name='Warranty 200', dimensionMembers=[A200])
    
    interests = Account(parent=self.expense, name='Interests')
    interests100 = self.interests100 = Account(parent=interests, name='Interests 100', dimensionMembers=[A100])
    interests200 = self.interests200 = Account(parent=interests, name='Interests 200', dimensionMembers=[A200])
    
    syndic = Account(parent=self.expense, name='Syndic')
    syndic100 = self.syndic100 = Account(parent=syndic, name='Syndic 100', dimensionMembers=[A100])
    syndic200 = self.syndic200 = Account(parent=syndic, name='Syndic 200', dimensionMembers=[A200])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensionMembers=[A100])
    taxes200 = self.taxes200 = Account(parent=taxes, name='Taxes 200', dimensionMembers=[A200])
    
    imposition = self.imposition = Account(parent=self.expense, name='Imposition')
    imposition100 = self.imposition100 = Account(parent=self.imposition, name='Imposition 100', dimensionMembers=[A100])
    imposition200 = self.imposition200 = Account(parent=self.imposition, name='Imposition 200', dimensionMembers=[A200])


    # ===========================================================================
    # INCOMES
    # ===========================================================================
    self.income = Account(parent=self.root, name='Income', type=TYPE_INCOME)

    rent = Account(parent=self.income, name='Rent')
    rent100 = self.rent100 = Account(parent=rent, name='Rent 100', dimensionMembers=[A100])
    rent200 = self.rent200 = Account(parent=rent, name='Rent 200', dimensionMembers=[A200])
    
    gain = Account(parent=self.income, name='Gain')
    gain100 = self.gain100 = Account(parent=gain, name='Gain 100', dimensionMembers=[A100])
    gain200 = self.gain200 = Account(parent=gain, name='Gain 200', dimensionMembers=[A200])
      

    # ===========================================================================
    # LIABILITIES
    # ===========================================================================
    self.liability = Account(parent=self.root, name='Liability', type=TYPE_LIABILITY)
    
    loan = Account(parent=self.liability, name='Loan')
    loan100 = self.loan100 = Account(parent=loan, name='Loan 100', dimensionMembers=[A100])
    loan200 = self.loan200 = Account(parent=loan, name='Loan 200', dimensionMembers=[A200])


    # ===========================================================================
    # EQUITY
    # ===========================================================================
    equity = self.equity = Account(parent=self.root, name='Equity', type=TYPE_EQUITY)
    self.bank.makeInitialTransaction(self.equity, Money(200000), Date(2005,1,1))


    # ===========================================================================
    # Make transactions to buy and rent an apartment
    # ===========================================================================

    # 2005
    Transaction(Date(2005,1,2), 'contract a loan', bank, loan100, 150000)

    Transaction(Date(2005,1,3), 'buy an apartment', apart100, bank, 200000)
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
    
    Transaction(Date(2005,12,31), '1 year gain capital 5%', apart100, gain100, 200000*0.05)

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

    Transaction(Date(2006,1,2), 'contract a loan', bank, loan200, 150000)

    Transaction(Date(2006,1,3), 'buy an apartment', apart200, bank, 200000)
    Transaction(Date(2006,1,3), 'pay VAT', taxes200, bank, 14000)

    Transaction(Date(2006,1,4), 'pay 1 year warranty', warranty200, bank, 50)
    Transaction(Date(2006,1,4), 'pay 1 year property tax', taxes200, bank, 300)
    Transaction(Date(2006,1,4), 'profit 1 year imposition reduction', imposition200, taxes200, 5000)
    # This tx is not related to the apartment
    Transaction(Date(2006,1,4), 'pay 1 year imposition', imposition, bank, 10000)
    
    Transaction(Date(2006,1,5), 'pay loan interests', interests200, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay loan principal', loan200, bank, 500*12)
    Transaction(Date(2006,1,5), 'pay syndic', syndic200, bank, 100*12)
    Transaction(Date(2006,1,5), 'rent the appartment', bank, rent200, 600*12)

    Transaction(Date(2006,12,31), '1 year gain capital 5%', apart200, gain200, 200000*0.06)


class GroupAccountsUnderDimensionVisitor(object):
    """ Visitor that groups all accounts having the same dimension under a new hierarchy while it is
    visiting an original account hierarchy. 
    /expense/typeA/account_A_WithDimension1 ==> /expense/dimension1/account_A_WithDimension1
    /expense/typeB/account_B_WithDimension1 ==> /expense/dimension1/account_B_WithDimension1
    """

    def __init__(self, dimension, newroot):
        self.dimension = dimension
        self.root = newroot

        self.asset = Account(parent=newroot.asset, name=dimension.code)
        self.expense = Account(parent=newroot.expense, name=dimension.code)
        self.income = Account(parent=newroot.income, name=dimension.code)
        self.liability = Account(parent=newroot.liability, name=dimension.code)
        self.equity = Account(parent=newroot.equity, name=dimension.code)
        self.profits = Account(parent=newroot.profits, name=dimension.code)
        self.netAssets = Account(parent=newroot.netAssets, name=dimension.code)
        
        self.type2account = {TYPE_ASSET:self.asset, TYPE_EXPENSE:self.expense,
                             TYPE_INCOME:self.income, TYPE_LIABILITY:self.liability, 
                             TYPE_EQUITY:self.equity, TYPE_PROFITS:self.profits, 
                             TYPE_NET_ASSETS:self.netAssets}

    def __call__(self, account, depth):
        """ This method makes self acts as a function. It is called while visiting a tree account. """

        if self.dimension in account.dimensionMembers:
            self.addAccount(account)

    def addAccount(self, child):
        account = Account(self.type2account[child.type], name=child.name)
        account.makeInitialTransaction(self.equity.parent, child.balance)


class MultiDimensionRootAccount(RootAccount):

    def __init__(self, name=None, description=None):
        super(MultiDimensionRootAccount, self).__init__(name, description)

        self.asset = Account(parent=self, name='Asset', type=TYPE_ASSET)
        self.expense = Account(parent=self, name='Expense', type=TYPE_EXPENSE)
        self.income = Account(parent=self, name='Income', type=TYPE_INCOME)
        self.liability = Account(parent=self, name='Liability', type=TYPE_LIABILITY)
        self.equity = Account(parent=self, name='Equity', type=TYPE_EQUITY)
        self.profits = Account(parent=self, name='Profits & Loss', type=TYPE_EQUITY)
        self.netAssets = Account(parent=self, name='Net Assets', type=TYPE_EQUITY)


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)
        self.pp(self.root)

    def pp(self, root):
        root.traverseHierarchy(self.printAccount, False)

    def printAccount(self, account, depth):
        print '\t'*depth + str(account).ljust(20) + (str(account.balance)).rjust(40-4*depth)

    def sortSubAccounts(self, account, depth):
        aux = [(subAccount.balance, subAccount) for subAccount in account.subAccounts]
        aux.sort()
        aux.reverse()
        sortedSubAccounts = [subAccount for balance, subAccount in aux]
        account.setSubAccounts(sortedSubAccounts)
        
    def test_real_estate(self):
        # Create a root for the new account hierarchy grouping accounts under their dimension.
        rootApart = MultiDimensionRootAccount(name='root for Apartment')
        endYear = Date(2006,12,31)
        
        for dimension in [self.A100, self.A200]:
            # Group accounts under the current dimension
            v = GroupAccountsUnderDimensionVisitor(dimension, rootApart)
            self.root.traverseHierarchy(v, False)

            # Make expense and income accounts zero at the end year.
            #Transaction(endYear, 'year end', v.equity, v.expense, v.expense.balance)
            #Transaction(endYear, 'year end', v.income, v.equity, v.income.balance)
            
            # Finally, compute Profit & Loss and Net Assets for the current dimension.
            Transaction(endYear, 'Profit & Loss', 
                        v.equity.parent, v.profits, v.income.balance - v.expense.balance)
            Transaction(endYear, 'Net Assets', 
                        v.equity.parent, v.netAssets, v.profits.balance + v.equity.balance)

        rootApart.traverseHierarchy(self.sortSubAccounts, False)

        print '================ View under the Apartment dimension ================'
        rootApart.traverseHierarchy(self.printAccount, False)


if __name__ == '__main__':
    unittest.main()
