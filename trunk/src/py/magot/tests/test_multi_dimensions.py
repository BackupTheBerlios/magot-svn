"""Unit tests for multi-dimension analysis."""

from itertools import groupby

from unittest import TestCase, makeSuite, TestSuite
import unittest

from magot.refdata import *
from magot.model import *

from peak.model import features, datatypes, elements


# 1- Define application dimensions

class RoomNumber(DimensionMember): pass
class Location(DimensionMember): pass
class Expense(DimensionMember): pass

class Apartment(DimensionMember):
    # Automatic settings of Super members.
    class location(DimensionAttribute):
        referencedType = Location
    
    class roomNb(DimensionAttribute):
        referencedType = RoomNumber



def makeAccounts(self):

    # create all accounts under the root account
    self.root = RootAccount(name='Accounts')

    # ===========================================================================
    # 2- Define dimension members for each dimension
    # ===========================================================================
    
    # ===========================================================================
    # Define the "RoomNumber" dimension members.
    # ===========================================================================
    self.R2 = R2 = RoomNumber(name="2-roomed", desc="2-roomed")
    self.R3 = R3 = RoomNumber(name="3-roomed", desc="3-roomed")

    # ===========================================================================
    # Define the "Location" dimension members.
    # ===========================================================================
    self.zoneA = zoneA = Location(name="zoneA", desc="zoneA")
    self.puteaux = puteaux = Location(name="Puteaux", desc="Puteaux")
    self.issy = issy = Location(name="Issy", desc="Issy")
    # Manual (vs automatic) settings of Super members (see Apartment class).
    puteaux.addSuperMember(zoneA)  # City 'puteaux' is in region 'zoneA'
    issy.addSuperMember(zoneA)

    # ===========================================================================
    # Define the "Apartment" dimension members.
    # ===========================================================================
    # Super members are automatically added due to DimensionAttribute in Apartment class.
    self.A100 = A100 = Apartment(name="A100", desc="Apartment 100", location=puteaux, roomNb=R2)
    self.A200 = A200 = Apartment(name="A200", desc="Apartment 200", location=puteaux, roomNb=R2)
    self.A300 = A300 = Apartment(name="A300", desc="Apartment 300", location=puteaux, roomNb=R3)
    self.A400 = A400 = Apartment(name="A400", desc="Apartment 400", location=issy, roomNb=R3)

    # ===========================================================================
    # Define the "Expense" dimension members.
    # ===========================================================================
    self.warrantyMember = warrantyMember = Expense(name="Warranty", desc="Warranty")
    self.taxesMember = taxesMember = Expense(name="Taxes", desc="Taxes")


    # ===========================================================================
    # 3- Define accounts and give them some dimension members.
    # ===========================================================================

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
    warranty100 = Account(parent=warranty, name='Warranty 100', dimensionMembers=[A100, warrantyMember])
    warranty200 = Account(parent=warranty, name='Warranty 200', dimensionMembers=[A200, warrantyMember])
    warranty300 = Account(parent=warranty, name='Warranty 300', dimensionMembers=[A300, warrantyMember])
    warranty400 = Account(parent=warranty, name='Warranty 400', dimensionMembers=[A400, warrantyMember])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = Account(parent=taxes, name='Taxes 100', dimensionMembers=[A100, taxesMember])
    taxes200 = Account(parent=taxes, name='Taxes 200', dimensionMembers=[A200, taxesMember])
    taxes300 = Account(parent=taxes, name='Taxes 300', dimensionMembers=[A300, taxesMember])
    taxes400 = Account(parent=taxes, name='Taxes 400', dimensionMembers=[A400, taxesMember])

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
    # 4- Post some transactions.
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


class SingleDimensionRoots(object):
    """ Container for principal roots (asset, expense, liability, ...) under a single dimension. """
    
    def __init__(self, multiDimensionRoot, name):
        r = self.root = multiDimensionRoot
        self.name = name
        self.subRoots = {}

        self.subRoots[TYPE_ASSET] = self.asset = Account(parent=r.asset, name=name)
        self.subRoots[TYPE_EXPENSE] = self.expense = Account(parent=r.expense, name=name)
        self.subRoots[TYPE_INCOME] = self.income = Account(parent=r.income, name=name)
        self.subRoots[TYPE_LIABILITY] = self.liability = Account(parent=r.liability, name=name)
        self.subRoots[TYPE_EQUITY] = self.equity = Account(parent=r.equity, name=name)
        self.subRoots[TYPE_PROFITS] = self.profits = Account(parent=r.profits, name=name)
        self.subRoots[TYPE_NET_ASSETS] = self.netAssets = Account(parent=r.netAssets, name=name)
        

class KeepAccountsByDimensionVisitor(object):

    def __init__(self, dimensionsAndMembers):
        self.dimensionsAndMembers = set(dimensionsAndMembers)
        self.accounts = {}  # List of accounts, stored by account type.

    def __call__(self, account, depth):
        if account.hasAllDimensionAndMember(self.dimensionsAndMembers):
            self.accounts.setdefault(account.type, []).append(account)


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)
        self.pprint(self.root)

    def pprint(self, root):
        def printAccount(account, depth):
            if account.balance.amount != 0:
                print '\t'*depth + str(account).ljust(20) + (str(account.balance)).rjust(40-4*depth)

        root.traverseHierarchy(printAccount, False)
        print "============================================================"

    def test_multi_dimension(self):
        # Group by dimension members
        self.viewAccountsUnderDimensions([self.A100])
        self.viewAccountsUnderDimensions([self.puteaux])
        self.viewAccountsUnderDimensions([self.zoneA])
        self.viewAccountsUnderDimensions([self.zoneA, self.R2, self.warrantyMember])

        # Group by dimensions only
        self.viewAccountsUnderDimensions([Location.dimension])
        self.viewAccountsUnderDimensions([Apartment.dimension])
        self.viewAccountsUnderDimensions([Location.dimension, Apartment.dimension])
        self.viewAccountsUnderDimensions([Location.dimension, RoomNumber.dimension])
        self.viewAccountsUnderDimensions([RoomNumber.dimension, Location.dimension])
        self.viewAccountsUnderDimensions([Location.dimension, RoomNumber.dimension, Apartment.dimension])

        # Group by a mix of dimensions and dimension members
        self.viewAccountsUnderDimensions([Apartment.dimension, self.R2])
        self.viewAccountsUnderDimensions([self.warrantyMember, Apartment.dimension])
        self.viewAccountsUnderDimensions([self.zoneA, RoomNumber.dimension])
        self.viewAccountsUnderDimensions([self.puteaux, self.R2, Apartment.dimension])

    def viewAccountsUnderDimensions(self, dimensions):
        endYear = self.endYear = Date(2006,12,31)

        # Create a root for the new account hierarchy grouping accounts by some dimensions.
        self.rootApart = MultiDimensionRootAccount(name='root for multi-dimension accounts')

        # Only keep accounts that have the requested dimensions only
        visitor = KeepAccountsByDimensionVisitor(dimensions)
        self.root.traverseHierarchy(visitor, False)

        print 'Reporting under',  ', '.join(map(str, dimensions))
        print "============================================================"

        # Group accounts by all dimensions hierarchically
        dimensions.reverse()
        from magot.util import flatten
        self.groupAccountsByOneDimension(dimensions, flatten(visitor.accounts.values()), 
                                         self.rootApart, True)

        self.pprint(self.rootApart)

    def groupAccountsByOneDimension(self, dimensions, accounts, root, isFirstLevel=False):
        if not dimensions:
            for account in accounts:
                self.createAccountLikeOriginal(account, root.subRoots[account.type])

            r = self.rootApart
            Transaction(self.endYear, 'Profit & Loss', r.equity, root.profits, 
                        root.income.balance - root.expense.balance)
            Transaction(self.endYear, 'Net Assets', r.equity, root.netAssets, 
                        root.profits.balance + root.equity.balance)
            return

        dimensionOrMember = dimensions.pop()
        keyFunc = dimensionOrMember.getMemberForAccount

        for dimMember, accountGroup in groupby(sorted(accounts, key=keyFunc), keyFunc):
            roots = SingleDimensionRoots(root, dimMember.name)
            self.groupAccountsByOneDimension(list(dimensions), accountGroup, roots)

    def createAccountLikeOriginal(self, original, parent):
        account = Account(parent, name=original.name, dimensionMembers=original.dimensionMembers)
        account.makeInitialTransaction(self.rootApart.equity, original.balance)


if __name__ == '__main__':
    unittest.main()
