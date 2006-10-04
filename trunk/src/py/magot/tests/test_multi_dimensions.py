"""Unit tests for multi-dimension analysis."""

from itertools import groupby

from unittest import TestCase, makeSuite, TestSuite
import unittest

from magot.refdata import *
from magot.model import RootAccount, Account, Transaction, Dimension, DimensionMember


def makeAccounts(self):

    # create all accounts under the root account
    self.root = RootAccount(name='Accounts')
    
    # ===========================================================================
    # Define the "Location" Dimension for an apartment with 4 dimension members.
    # ===========================================================================
    self.locationDim = locationDim = Dimension(name="Location")

    zoneA = DimensionMember(code="zoneA", desc="zoneA", dimension=locationDim)
    zoneB = DimensionMember(code="zoneB", desc="zoneB", dimension=locationDim)
    puteaux = DimensionMember(code="Puteaux", desc="Puteaux", dimension=locationDim)
    issy = DimensionMember(code="Issy", desc="Issy", dimension=locationDim)

    puteaux.addSuperLevel(zoneA)  # City 'Puteaux' is in region 'zoneA'
    issy.addSuperLevel(zoneB)


    # ===========================================================================
    # Define the "RoomNumber" Dimension for an apartment with 2 members.
    # ===========================================================================
    self.roomNumberDim = roomNumberDim = Dimension(name="RoomNumber")

    R2 = DimensionMember(code="2-roomed", desc="2-roomed", dimension=roomNumberDim)
    R3 = DimensionMember(code="3-roomed", desc="3-roomed", dimension=roomNumberDim)


    # ===========================================================================
    # Define the "Apartment" Dimension with 4 members.
    # ===========================================================================
    self.apartmentDim = apartmentDim = Dimension(name="Apartment")

    A100 = DimensionMember(code="A100", desc="Apartment 100", dimension=apartmentDim)
    A200 = DimensionMember(code="A200", desc="Apartment 200", dimension=apartmentDim)
    A300 = DimensionMember(code="A300", desc="Apartment 300", dimension=apartmentDim)
    A400 = DimensionMember(code="A400", desc="Apartment 400", dimension=apartmentDim)

    A100.setSuperLevels([puteaux, R2])
    A200.setSuperLevels([puteaux, R3])
    A300.setSuperLevels([issy, R2])
    A400.setSuperLevels([issy, R3])


    # ===========================================================================
    # Define the "Expense" Dimension with 2 members.
    # ===========================================================================
    self.expenseDim = expenseDim = Dimension(name="Expense")

    warrantyMember = DimensionMember(code="Warranty", desc="Warranty", dimension=expenseDim)
    taxesMember = DimensionMember(code="Taxes", desc="Taxes", dimension=expenseDim)


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
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensions=[A100, warrantyMember])
    warranty200 = self.warranty200 = Account(parent=warranty, name='Warranty 200', dimensions=[A200, warrantyMember])
    warranty300 = self.warranty300 = Account(parent=warranty, name='Warranty 300', dimensions=[A300, warrantyMember])
    warranty400 = self.warranty400 = Account(parent=warranty, name='Warranty 400', dimensions=[A400, warrantyMember])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensions=[A100, taxesMember])
    taxes200 = self.taxes200 = Account(parent=taxes, name='Taxes 200', dimensions=[A200, taxesMember])
    taxes300 = self.taxes300 = Account(parent=taxes, name='Taxes 300', dimensions=[A300, taxesMember])
    taxes400 = self.taxes400 = Account(parent=taxes, name='Taxes 400', dimensions=[A400, taxesMember])


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


class KeepAccountsByDimensionVisitor(object):

    def __init__(self, dimensions):
        self.dimensions = set(dimensions)
        self.accounts = []

    def __call__(self, account, depth):
        for dimension in self.dimensions:
            if account.getMemberForDimension(dimension) is not None:
                self.accounts.append(account)
                break
                

class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)
        self.pprint(self.root)

    def pprint(self, root):
        def printAccount(account, depth):
            print '\t'*depth + str(account).ljust(20) + (str(account.balance)).rjust(40-4*depth)

        root.traverseHierarchy(printAccount, False)
        print "============================================================"


    def test_multi_dimension(self):
        self.viewAccountsUnderDimensions([self.locationDim])
        self.viewAccountsUnderDimensions([self.apartmentDim, self.expenseDim])
        self.viewAccountsUnderDimensions([self.roomNumberDim, self.locationDim])
        self.viewAccountsUnderDimensions([self.locationDim, self.roomNumberDim])
        self.viewAccountsUnderDimensions([self.expenseDim, self.locationDim, self.roomNumberDim])
        
    def viewAccountsUnderDimensions(self, dimensions):
        # Create a root for the new account hierarchy grouping accounts under their dimension.
        self.rootApart = MultiDimensionRootAccount(name='root for Apartment')
        endYear = Date(2006,12,31)

        # Only keep accounts that have the requested dimensions
        v = KeepAccountsByDimensionVisitor(dimensions)
        self.root.traverseHierarchy(v, False)

        # Group accounts by dimension hierarchically
        dimensions.reverse()
        self.oneDimension(dimensions, v.accounts, self.rootApart.expense)
                
        self.pprint(self.rootApart)
                
    def createAccount(self, child, parent):
        account = Account(parent, name=child.name, dimensions=child.dimensions)
        account.makeInitialTransaction(self.rootApart.equity, child.balance)

    def oneDimension(self, dimensions, accounts, parent):
        if not dimensions:
            for account in accounts:
                self.createAccount(account, parent)
            return

        dimension = dimensions.pop()
        keyFunc = dimension.getMemberForAccount

        for dimMember, accountGroup in groupby(sorted(accounts, key=keyFunc), keyFunc):
            newRoot = Account(parent, name=dimMember.code)
            self.oneDimension(list(dimensions), list(accountGroup), newRoot)
        

if __name__ == '__main__':
    unittest.main()
