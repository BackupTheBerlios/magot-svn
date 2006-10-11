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
    self.locationDim = locationDim = Dimension(code="Location")

    self.zoneA = zoneA = DimensionMember(code="zoneA", desc="zoneA", dimension=locationDim)
    self.puteaux = puteaux = DimensionMember(code="Puteaux", desc="Puteaux", dimension=locationDim)
    self.issy = issy = DimensionMember(code="Issy", desc="Issy", dimension=locationDim)

    puteaux.addSuperMember(zoneA)  # City 'Puteaux' is in region 'zoneA'
    issy.addSuperMember(zoneA)


    # ===========================================================================
    # Define the "RoomNumber" Dimension for an apartment with 2 members.
    # ===========================================================================
    self.roomNumberDim = roomNumberDim = Dimension(code="RoomNumber")

    self.R2 = R2 = DimensionMember(code="2-roomed", desc="2-roomed", dimension=roomNumberDim)
    self.R3 = R3 = DimensionMember(code="3-roomed", desc="3-roomed", dimension=roomNumberDim)


    # ===========================================================================
    # Define the "Apartment" Dimension with 4 members.
    # ===========================================================================
    self.apartmentDim = apartmentDim = Dimension(code="Apartment")

    self.A100 = A100 = DimensionMember(code="A100", desc="Apartment 100", dimension=apartmentDim)
    self.A200 = A200 = DimensionMember(code="A200", desc="Apartment 200", dimension=apartmentDim)
    self.A300 = A300 = DimensionMember(code="A300", desc="Apartment 300", dimension=apartmentDim)
    self.A400 = A400 = DimensionMember(code="A400", desc="Apartment 400", dimension=apartmentDim)

    A100.setSuperMembers([puteaux, R2])
    A200.setSuperMembers([puteaux, R3])
    A300.setSuperMembers([issy, R2])
    A400.setSuperMembers([issy, R3])


    # ===========================================================================
    # Define the "Expense" Dimension with 2 members.
    # ===========================================================================
    self.expenseDim = expenseDim = Dimension(code="Expense")

    self.warrantyMember = warrantyMember = DimensionMember(code="Warranty", desc="Warranty", dimension=expenseDim)
    self.taxesMember = taxesMember = DimensionMember(code="Taxes", desc="Taxes", dimension=expenseDim)


    # ===========================================================================
    # ASSETS
    # ===========================================================================
    self.asset = Account(parent=self.root, name='Asset', type=TYPE_ASSET)

    bank = Account(parent=self.asset, name='Bank')
    apart = Account(parent=self.asset, name='All apartments')
    apart100 = self.apart100 = Account(parent=apart, name='Apartment 100', dimensionMembers=[A100])

    
    # ===========================================================================
    # EXPENSES
    # ===========================================================================
    self.expense = Account(parent=self.root, name='Expense', type=TYPE_EXPENSE)

    warranty = Account(parent=self.expense, name='Warranty')
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensionMembers=[A100, warrantyMember])
    warranty200 = self.warranty200 = Account(parent=warranty, name='Warranty 200', dimensionMembers=[A200, warrantyMember])
    warranty300 = self.warranty300 = Account(parent=warranty, name='Warranty 300', dimensionMembers=[A300, warrantyMember])
    warranty400 = self.warranty400 = Account(parent=warranty, name='Warranty 400', dimensionMembers=[A400, warrantyMember])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensionMembers=[A100, taxesMember])
    taxes200 = self.taxes200 = Account(parent=taxes, name='Taxes 200', dimensionMembers=[A200, taxesMember])
    taxes300 = self.taxes300 = Account(parent=taxes, name='Taxes 300', dimensionMembers=[A300, taxesMember])
    taxes400 = self.taxes400 = Account(parent=taxes, name='Taxes 400', dimensionMembers=[A400, taxesMember])


    # ===========================================================================
    # INCOMES
    # ===========================================================================
    self.income = Account(parent=self.root, name='Income', type=TYPE_INCOME)

    rent = Account(parent=self.income, name='Rent')
    rent100 = self.rent100 = Account(parent=rent, name='Rent 100', dimensionMembers=[A100])

    
    # ===========================================================================
    # LIABILITIES
    # ===========================================================================
    self.liability = Account(parent=self.root, name='Liability', type=TYPE_LIABILITY)

    loan = Account(parent=self.liability, name='Loan')
    loan100 = self.loan100 = Account(parent=loan, name='Loan 100', dimensionMembers=[A100])

    
    # ===========================================================================
    # EQUITY
    # ===========================================================================
    self.equity = Account(parent=self.root, name='Equity', type=TYPE_EQUITY)
    bank.makeInitialTransaction(self.equity, Money(200000), Date(2005,1,1))

    equity100 = self.equity100 = Account(parent=self.equity, name='Equity 100', dimensionMembers=[A100])
    bank.makeInitialTransaction(self.equity100, Money(20000), Date(2005,1,1))


    # ===========================================================================
    # Make some transactions
    # ===========================================================================

    Transaction(Date(2005,1,2), 'contract a loan', bank, loan100, 150000)
    Transaction(Date(2005,1,3), 'buy an apartment', apart100, bank, 200000)
    Transaction(Date(2005,1,4), 'pay 1 year warranty', warranty100, bank, 0.5)
    Transaction(Date(2005,1,4), 'pay 1 year property tax', taxes100, bank, 2)
    Transaction(Date(2005,1,5), 'rent the appartment', bank, rent100, 600*12)

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

    def __init__(self, dimensionsAndMembers):
        self.dimensionsAndMembers = set(dimensionsAndMembers)
        self.accounts = {}  # Accounts that are kept, by account type.

    def __call__(self, account, depth):
        if account.hasAllDimensionAndMember(self.dimensionsAndMembers):
            self.accounts.setdefault(account.type, []).append(account)


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
        # Group by dimension members
        self.viewAccountsUnderDimensions([self.A100])
        #self.viewAccountsUnderDimensions([self.A100, self.A200])
        #self.viewAccountsUnderDimensions([self.puteaux])
        #self.viewAccountsUnderDimensions([self.zoneA])
        #self.viewAccountsUnderDimensions([self.puteaux, self.warrantyMember])

        ## Group by dimensions
        #self.viewAccountsUnderDimensions([self.locationDim])
        #self.viewAccountsUnderDimensions([self.apartmentDim, self.expenseDim])
        #self.viewAccountsUnderDimensions([self.roomNumberDim, self.locationDim])
        #self.viewAccountsUnderDimensions([self.locationDim, self.roomNumberDim])
        #self.viewAccountsUnderDimensions([self.expenseDim, self.locationDim, self.roomNumberDim])

        ## Group by mix of dimensions and dimension members
        #self.viewAccountsUnderDimensions([self.apartmentDim, self.R2])
        #self.viewAccountsUnderDimensions([self.warrantyMember, self.apartmentDim])
        #self.viewAccountsUnderDimensions([self.zoneA, self.roomNumberDim])

    def viewAccountsUnderDimensions(self, dimensions):
        # Create a root for the new account hierarchy grouping accounts by some dimensions.
        r = self.rootApart = MultiDimensionRootAccount(name='root for Apartment')
        endYear = Date(2006,12,31)

        # Only keep accounts that have the requested dimensions
        visitor = KeepAccountsByDimensionVisitor(dimensions)
        self.root.traverseHierarchy(visitor, False)

        # Group accounts by all dimensions hierarchically
        dimensions.reverse()
        parentByType = {TYPE_ASSET:r.asset, TYPE_EXPENSE:r.expense, TYPE_LIABILITY:r.liability, 
                        TYPE_INCOME:r.income, TYPE_EQUITY:r.equity}

        subRoots = self.subRootByType = {}
        
        for type, parent in parentByType.iteritems():
            self.groupByOneDimension(list(dimensions), visitor.accounts[type], parent)

        Transaction(endYear, 'Profit & Loss', 
            r.equity, r.profits, subRoots[TYPE_INCOME].balance - subRoots[TYPE_EXPENSE].balance)
        Transaction(endYear, 'Net Assets', 
                    r.equity, r.netAssets, r.profits.balance + subRoots[TYPE_EQUITY].balance)

        self.pprint(self.rootApart)

    def groupByOneDimension(self, dimensions, accounts, parent):
        if not dimensions:
            for account in accounts:
                self.createAccount(account, parent)
            return

        dimension = dimensions.pop()
        keyFunc = dimension.getMemberForAccount

        for dimMember, accountGroup in groupby(sorted(accounts, key=keyFunc), keyFunc):
            newRoot = Account(parent, name=dimMember.code)
            self.subRootByType.setdefault(newRoot.type, newRoot)
            self.groupByOneDimension(list(dimensions), list(accountGroup), newRoot)

    def createAccount(self, child, parent):
        account = Account(parent, name=child.name, dimensionMembers=child.dimensionMembers)
        account.makeInitialTransaction(self.rootApart.equity, child.balance)


if __name__ == '__main__':
    unittest.main()
