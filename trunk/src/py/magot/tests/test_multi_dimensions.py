"""Unit tests for multi-dimension analysis."""

from unittest import TestCase, makeSuite, TestSuite
import unittest

from magot.refdata import *
from magot.model import RootAccount, Account, Transaction, Dimension, DimensionMember


def makeAccounts(self):

    # create all accounts under the root account
    self.root = RootAccount(name='Accounts')
    
    # ===========================================================================
    # Define the "Location" Dimension for an apartment with 2 members.
    # ===========================================================================
    self.locationDim = locationDim = Dimension(name="Location")
    puteaux = DimensionMember(code="Puteaux", desc="Puteaux")
    locationDim.addMember(puteaux)
    issy = DimensionMember(code="Issy", desc="Issy")
    locationDim.addMember(issy)


    # ===========================================================================
    # Define the "RoomNumber" Dimension for an apartment with 2 members.
    # ===========================================================================
    self.roomNumberDim = roomNumberDim = Dimension(name="RoomNumber")
    R2 = DimensionMember(code="2-roomed", desc="2-roomed")
    roomNumberDim.addMember(R2)
    R3 = DimensionMember(code="3-roomed", desc="3-roomed")
    roomNumberDim.addMember(R3)


    # ===========================================================================
    # Define the "Apartment" Dimension with 4 members.
    # ===========================================================================
    self.apartmentDim = apartmentDim = Dimension(name="Apartment")

    A100 = self.A100 = DimensionMember(code="A100", desc="Apartment 100", subLevels=[puteaux, R2])
    apartmentDim.addMember(A100)
    A200 = self.A200 = DimensionMember(code="A200", desc="Apartment 200", subLevels=[puteaux, R3])
    apartmentDim.addMember(A200)
    A300 = self.A300 = DimensionMember(code="A300", desc="Apartment 300", subLevels=[issy, R2])
    apartmentDim.addMember(A300)
    A400 = self.A400 = DimensionMember(code="A400", desc="Apartment 400", subLevels=[issy, R3])
    apartmentDim.addMember(A400)


    # ===========================================================================
    # Define the "Expense" Dimension with 2 members.
    # ===========================================================================
    self.expenseDim = expenseDim = Dimension(name="Expense")

    warrantyDim = self.warrantyDim = DimensionMember(code="Warranty", desc="Warranty")
    expenseDim.addMember(warrantyDim)
    taxesDim = self.taxesDim = DimensionMember(code="Taxes", desc="Taxes")
    expenseDim.addMember(taxesDim)


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
    warranty100 = self.warranty100 = Account(parent=warranty, name='Warranty 100', dimensions=[A100, warrantyDim])
    warranty200 = self.warranty200 = Account(parent=warranty, name='Warranty 200', dimensions=[A200, warrantyDim])
    warranty300 = self.warranty300 = Account(parent=warranty, name='Warranty 300', dimensions=[A300, warrantyDim])
    warranty400 = self.warranty400 = Account(parent=warranty, name='Warranty 400', dimensions=[A400, warrantyDim])
    
    taxes = Account(parent=self.expense, name='Taxes')
    taxes100 = self.taxes100 = Account(parent=taxes, name='Taxes 100', dimensions=[A100, taxesDim])
    taxes200 = self.taxes200 = Account(parent=taxes, name='Taxes 200', dimensions=[A200, taxesDim])
    taxes300 = self.taxes300 = Account(parent=taxes, name='Taxes 300', dimensions=[A300, taxesDim])
    taxes400 = self.taxes400 = Account(parent=taxes, name='Taxes 400', dimensions=[A400, taxesDim])

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


class GroupAccountsUnderDimensionVisitor(object):
    """ Visitor that groups all accounts having the same dimension under a new hierarchy while it is
    visiting an original account hierarchy. 
    /expense/typeA/account_A_WithDimension1 ==> /expense/dimension1/account_A_WithDimension1
    /expense/typeB/account_B_WithDimension1 ==> /expense/dimension1/account_B_WithDimension1
    """

    def __init__(self, dimensions, newroot):
        self.root = newroot
        self.parent = self.root
        self.dimensions = dimensions
        self.member2Acc = {}
        self.firstDimension = True

        for dimension in dimensions:
            save = self.member2Acc.copy()
            self.member2Acc = {}
            for member in dimension.members:
                parent = self.findParent(member, save)
                self.member2Acc[member] = Account(parent=parent, name=member.code, 
                                                       dimensions=[member])
            self.firstDimension = False

    def findParent(self, member, member2Acc):
        if self.firstDimension:
            return self.parent.expense

        for m in member2Acc:
            if m.isInPath([member]):
                return member2Acc[m]
        assert "Parent not found"
        
                             
    def __call__(self, account, depth):
        """ This method makes self acts as a function. It is called while visiting a tree account. """
        if not account.dimensions or account.subAccounts:
            return
        
        keys = self.member2Acc.keys()
        for m in account.dimensions:
            if m.isInPath(keys):
                parent = self.member2Acc[m]
                self.createAccount(account, parent)

    def createAccount(self, child, parent):
        account = Account(parent, name=child.name, dimensions=child.dimensions)
        account.makeInitialTransaction(self.root.equity, child.balance)
        

class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)
        self.pp(self.root)

    def pp(self, root):
        def printAccount(account, depth):
            print '\t'*depth + str(account).ljust(20) + (str(account.balance)).rjust(40-4*depth)

        root.traverseHierarchy(printAccount, False)
        print "==============================================="


    def test_multi_dimension(self):
        # Create a root for the new account hierarchy grouping accounts under their dimension.
        rootApart = MultiDimensionRootAccount(name='root for Apartment')
        endYear = Date(2006,12,31)

        # Group accounts under each apartment dimension
        v = GroupAccountsUnderDimensionVisitor([self.locationDim, self.apartmentDim], rootApart)
        self.root.traverseHierarchy(v, False)

        self.pp(rootApart)


if __name__ == '__main__':
    unittest.main()
