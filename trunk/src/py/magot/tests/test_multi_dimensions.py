"""Unit tests for multidimensional analysis."""

from unittest import TestCase, makeSuite, TestSuite, main

from magot.refdata import *
from magot.model import *
from magot.dimension import *


# ===========================================================================
# 1- Define domain dimensions.
# ===========================================================================

class RoomNumber(DimensionMember): pass
class Location(DimensionMember): pass
class Expense(DimensionMember): pass

class Apartment(DimensionMember):
    # Automatic settings of Super members.
    class location(DimensionAttribute):
        referencedType = Location
    
    class roomNb(DimensionAttribute):
        referencedType = RoomNumber


# ===========================================================================
# 2- Define dimension members for each dimension.
# ===========================================================================
def makeDimensionMembers(self):

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
    self.A100 = Apartment(name="A100", desc="Apartment 100", location=puteaux, roomNb=R2)
    self.A200 = Apartment(name="A200", desc="Apartment 200", location=puteaux, roomNb=R2)
    self.A300 = Apartment(name="A300", desc="Apartment 300", location=puteaux, roomNb=R3)
    self.A400 = Apartment(name="A400", desc="Apartment 400", location=issy, roomNb=R3)

    # ===========================================================================
    # Define the "Expense" dimension members.
    # ===========================================================================
    self.warrantyMember = Expense(name="Warranty", desc="Warranty")
    self.taxesMember = Expense(name="Taxes", desc="Taxes")
    self.impositionMember = Expense(name="Imposition", desc="Imposition")
    self.syndicMember = Expense(name="Syndic", desc="Syndic")
    self.interestsMember = Expense(name="Interests", desc="Interests")


# ===========================================================================
# 3- Define accounts and give them some dimension members.
# ===========================================================================
def makeAccounts(self):

    makeDimensionMembers(self)

    # Create all accounts under the root account.
    self.root = RootAccount(name='Accounts')

    # ===========================================================================
    # ASSETS
    # ===========================================================================
    self.asset = Account(parent=self.root, name='Asset', type=TYPE_ASSET)

    bank = Account(parent=self.asset, name='Bank')
    apart = Account(parent=self.asset, name='All apartments')
    apart100 = self.apart100 = Account(parent=apart, name='Apartment 100', dimensionMembers=[self.A100])

    # ===========================================================================
    # EXPENSES
    # ===========================================================================
    self.expense = Account(parent=self.root, name='Expense', type=TYPE_EXPENSE)

    warranty = Account(parent=self.expense, name='Warranty')
    warranty100 = Account(parent=warranty, name='Warranty 100', dimensionMembers=[self.A100, self.warrantyMember])
    warranty200 = Account(parent=warranty, name='Warranty 200', dimensionMembers=[self.A200, self.warrantyMember])
    warranty300 = Account(parent=warranty, name='Warranty 300', dimensionMembers=[self.A300, self.warrantyMember])
    warranty400 = Account(parent=warranty, name='Warranty 400', dimensionMembers=[self.A400, self.warrantyMember])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = Account(parent=taxes, name='Taxes 100', dimensionMembers=[self.A100, self.taxesMember])
    taxes200 = Account(parent=taxes, name='Taxes 200', dimensionMembers=[self.A200, self.taxesMember])
    taxes300 = Account(parent=taxes, name='Taxes 300', dimensionMembers=[self.A300, self.taxesMember])
    taxes400 = Account(parent=taxes, name='Taxes 400', dimensionMembers=[self.A400, self.taxesMember])

    # ===========================================================================
    # INCOMES
    # ===========================================================================
    self.income = Account(parent=self.root, name='Income', type=TYPE_INCOME)

    rent = Account(parent=self.income, name='Rent')
    rent100 = self.rent100 = Account(parent=rent, name='Rent 100', dimensionMembers=[self.A100])

    # ===========================================================================
    # LIABILITIES
    # ===========================================================================
    self.liability = Account(parent=self.root, name='Liability', type=TYPE_LIABILITY)

    loan = Account(parent=self.liability, name='Loan')
    loan100 = self.loan100 = Account(parent=loan, name='Loan 100', dimensionMembers=[self.A100])
    
    # ===========================================================================
    # EQUITY
    # ===========================================================================
    self.equity = Account(parent=self.root, name='Equity', type=TYPE_EQUITY)
    bank.makeInitialTransaction(self.equity, Money(200000), Date(2005,1,1))

    equity100 = self.equity100 = Account(parent=self.equity, name='Equity 100', dimensionMembers=[self.A100])
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


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)
        print "============================================================"
        print "Original account hierarchy"
        print "============================================================"
        pprintHierarchy(self.root)

    def test_multi_dimensions(self):
        viewer = HierarchyViewer(self.root, Date(2006,12,31))

        # Group by dimension members
        viewer.viewAccountsUnderDimensions([self.A100])
        assert viewer.root.netAssets.balance == Money("27197.5")
        viewer.viewAccountsUnderDimensions([self.puteaux])
        assert viewer.root.netAssets.balance == Money("27191")
        viewer.viewAccountsUnderDimensions([self.zoneA])
        assert viewer.root.netAssets.balance == Money("27188")
        viewer.viewAccountsUnderDimensions([self.zoneA, self.R2, self.warrantyMember])
        assert viewer.root.netAssets.balance == Money("-1")

        # Group by dimensions only
        viewer.viewAccountsUnderDimensions([Location.dimension])
        assert viewer.root.netAssets.balance == Money("27188")
        viewer.viewAccountsUnderDimensions([Apartment.dimension])
        assert viewer.root.netAssets.balance == Money("27188")
        viewer.viewAccountsUnderDimensions([RoomNumber.dimension, Location.dimension])
        assert viewer.root.netAssets.balance == Money("27188")
        viewer.viewAccountsUnderDimensions([Location.dimension, RoomNumber.dimension])
        assert viewer.root.netAssets.balance == Money("27188")
        viewer.viewAccountsUnderDimensions([Location.dimension, Apartment.dimension])
        assert viewer.root.netAssets.balance == Money("27188")
        viewer.viewAccountsUnderDimensions([Location.dimension, RoomNumber.dimension, Apartment.dimension])
        assert viewer.root.netAssets.balance == Money("27188")

        # Group by a mix of dimensions and dimension members
        viewer.viewAccountsUnderDimensions([self.R2, Apartment.dimension])
        assert viewer.root.netAssets.balance == Money("27195")
        viewer.viewAccountsUnderDimensions([self.puteaux, self.R2, Apartment.dimension])
        assert viewer.root.netAssets.balance == Money("27195")
        viewer.viewAccountsUnderDimensions([self.warrantyMember, Apartment.dimension])
        assert viewer.root.netAssets.balance == Money("-3")
        viewer.viewAccountsUnderDimensions([self.zoneA, RoomNumber.dimension, Apartment.dimension])
        assert viewer.root.netAssets.balance == Money("27188")


if __name__ == '__main__':
    main()
