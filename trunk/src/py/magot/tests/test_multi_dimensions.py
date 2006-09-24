"""Unit tests for multi-dimension analysis."""

from unittest import TestCase, makeSuite, TestSuite
import unittest

from magot.refdata import *
from magot.model import RootAccount, Account, Transaction, Dimension, DimensionMember


def makeAccounts(self):
    # create all accounts under the root account
    self.root = RootAccount(name='Accounts')
    
    # ===========================================================================
    # Define the "Location" Dimension for an apartment.
    # ===========================================================================
    self.LocationDim = LocationDim = Dimension(name="Location")

    # Add 2 members for this dimension
    puteaux = DimensionMember(code="Puteaux", desc="Puteaux")
    LocationDim.addMember(puteaux)
    issy = DimensionMember(code="Issy", desc="Issy")
    LocationDim.addMember(issy)


    # ===========================================================================
    # Define the "RoomNumber" Dimension for an apartment.
    # ===========================================================================
    self.RoomNumberDim = RoomNumberDim = Dimension(name="RoomNumber")

    # Add 2 members for this dimension
    R2 = DimensionMember(code="2-roomed", desc="2-roomed")
    RoomNumberDim.addMember(R2)
    R3 = DimensionMember(code="3-roomed", desc="3-roomed")
    RoomNumberDim.addMember(R3)


    # ===========================================================================
    # Define all dimensions for each apartment.
    # ===========================================================================
    A100 = [R2, puteaux]  # A100 is a 2-roomed apartment located at Puteaux.
    A200 = [R3, puteaux]
    A300 = [R2, issy]
    A400 = [R3, issy]

    
    # ===========================================================================
    # ASSETS
    # ===========================================================================
    self.asset = Account(parent=self.root, name='Asset', type=TYPE_ASSET)
    bank = self.bank = Account(parent=self.asset, name='Bank')
    
    # ===========================================================================
    # EXPENSES
    # ===========================================================================
    self.expense = Account(parent=self.root, name='Expense', type=TYPE_EXPENSE)

    warranty = Account(parent=self.expense, name='Warranty')
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensions=A100)
    warranty200 = self.warranty200 = Account(parent=warranty, name='Warranty 200', dimensions=A200)
    warranty300 = self.warranty300 = Account(parent=warranty, name='Warranty 300', dimensions=A300)
    warranty400 = self.warranty400 = Account(parent=warranty, name='Warranty 400', dimensions=A400)
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensions=A100)
    taxes200 = self.taxes200 = Account(parent=taxes, name='Taxes 200', dimensions=A200)
    taxes300 = self.taxes300 = Account(parent=taxes, name='Taxes 300', dimensions=A300)
    taxes400 = self.taxes400 = Account(parent=taxes, name='Taxes 400', dimensions=A400)

    # ===========================================================================
    # INCOMES
    # ===========================================================================
    self.income = Account(parent=self.root, name='Income', type=TYPE_INCOME)
    
    # ===========================================================================
    # LIABILITIES
    # ===========================================================================
    self.liability = Account(parent=self.root, name='Liability', type=TYPE_LIABILITY)
    
    # ===========================================================================
    # EQUITY
    # ===========================================================================
    self.equity = Account(parent=self.root, name='Equity', type=TYPE_EQUITY)


    # ===========================================================================
    # Make some expenses
    # ===========================================================================

    Transaction(Date(2005,1,4), 'pay 1 year warranty', warranty100, bank, 0.5)
    Transaction(Date(2005,1,4), 'pay 1 year property tax', taxes100, bank, 2)

    Transaction(Date(2005,1,4), 'pay 1 year warranty', warranty200, bank, 0.5)
    Transaction(Date(2005,1,4), 'pay 1 year property tax', taxes200, bank, 2)

    Transaction(Date(2005,1,4), 'pay 1 year warranty', warranty300, bank, 1)
    Transaction(Date(2005,1,4), 'pay 1 year property tax', taxes300, bank, 3)

    Transaction(Date(2005,1,4), 'pay 1 year warranty', warranty400, bank, 1)
    Transaction(Date(2005,1,4), 'pay 1 year property tax', taxes400, bank, 2)




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

        if self.dimension in account.dimensions:
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

    def test_real_estate(self):
        # Create a root for the new account hierarchy grouping accounts under their dimension.
        rootApart = MultiDimensionRootAccount(name='root for Apartment')
        endYear = Date(2006,12,31)
        
        for dimension in self.LocationDim.members:
            # Group accounts under the current dimension
            v = GroupAccountsUnderDimensionVisitor(dimension, rootApart)
            self.root.traverseHierarchy(v, False)

            # Finally, compute Profit & Loss and Net Assets for the current dimension.
            Transaction(endYear, 'Profit & Loss', 
                        v.equity.parent, v.profits, v.income.balance - v.expense.balance)
            Transaction(endYear, 'Net Assets', 
                        v.equity.parent, v.netAssets, v.profits.balance + v.equity.balance)

        print '================ View under the Apartment dimension ================'
        rootApart.traverseHierarchy(self.printAccount, False)


if __name__ == '__main__':
    unittest.main()
