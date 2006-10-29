from itertools import groupby

from magot.model import *
from magot.util import *


class StandardAccounts(object):
    """ Holds standard accounts : asset, expense, liability, income, equity, P&L and Net Assets. """

    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.stdAccounts = {}
        self.stdAccounts[TYPE_ASSET] = self.asset = self.createAccount(TYPE_ASSET)
        self.stdAccounts[TYPE_EXPENSE] = self.expense = self.createAccount(TYPE_EXPENSE)
        self.stdAccounts[TYPE_INCOME] = self.income = self.createAccount(TYPE_INCOME)
        self.stdAccounts[TYPE_LIABILITY] = self.liability = self.createAccount(TYPE_LIABILITY)
        self.stdAccounts[TYPE_EQUITY] = self.equity = self.createAccount(TYPE_EQUITY)
        self.stdAccounts[TYPE_PROFITS] = self.profits = self.createAccount(TYPE_PROFITS)
        self.stdAccounts[TYPE_NET_ASSETS] = self.netAssets = self.createAccount(TYPE_NET_ASSETS)

    def getAccountForType(self, accountType):
        return self.stdAccounts[accountType]
    
    def __repr__(self):
        return self.__class__.__name__+'('+self.name+')'
    
    __str__ = __repr__


class StandardRootAccount(StandardAccounts, RootAccount):
    """ Root account that holds standard sub-accounts. """

    accNames = {TYPE_ASSET:'Asset', TYPE_EXPENSE:'Expense', 
                TYPE_INCOME:'Income', TYPE_LIABILITY:'Liability', TYPE_EQUITY:'Equity', 
                TYPE_PROFITS:'Profits & Loss',TYPE_NET_ASSETS:'Net Assets'}

    def createAccount(self, accType):
        # All accounts have different names but are stored under a single parent.
        return Account(parent=self, name=self.accNames[accType], type=accType)


class PropertyScopedStandardAccounts(StandardAccounts):
    """ Holds standard accounts tied by a single property (vs a single parent account).
    The property may be anything that has a name : a dimension, a member, ... """

    def __init__(self, standardParent, scopingProperty):
        p = self.parent = standardParent
        self.accParents = {TYPE_ASSET:p.asset, TYPE_EXPENSE:p.expense, 
                           TYPE_INCOME:p.income, TYPE_LIABILITY:p.liability, TYPE_EQUITY:p.equity, 
                           TYPE_PROFITS:p.profits, TYPE_NET_ASSETS:p.netAssets}
        super(PropertyScopedStandardAccounts, self).__init__(scopingProperty.name)
        self.scopingProperty = scopingProperty

    def createAccount(self, accType):
        # All accounts have the same name but are stored under a different parent.
        return Account(parent=self.accParents[accType], name=self.name)


class KeepAccountsByDimensionVisitor(object):
    """ Visitor that keeps accounts having a provided dimension while traversing a hierarchy. """

    def __init__(self, dimensionsAndMembers):
        self.dimensionsAndMembers = set(dimensionsAndMembers)
        self.accounts = {}  # List of accounts, stored by account type.

    def __call__(self, account, depth):
        if account.hasAllDimensionAndMember(self.dimensionsAndMembers):
            self.accounts.setdefault(account.type, []).append(account)


class HierarchyViewer(object):
    """ Viewer that traverse a hierarchy and display accounts grouped by dimensions. """

    def __init__(self, root, endYear=Date.today()):
        self.originalRoot = root
        self.endYear = endYear

    def viewAccountsUnderDimensions(self, dimensions):
        # Create a root for the new account hierarchy in order to group accounts by dimensions.
        self.root= StandardRootAccount(name='Root for multi-dimension accounts')

        # Only keep accounts that have the requested dimensions.
        visitor = KeepAccountsByDimensionVisitor(dimensions)
        self.originalRoot.traverseHierarchy(visitor, False)

        print 'Grouping by',  ', '.join(map(str, dimensions))
        print "============================================================"

        # Group accounts by all dimensions hierarchically
        dimensions.reverse()
        keptAccounts = flatten(visitor.accounts.itervalues())
        self.groupAccountsByOneDimension(dimensions, keptAccounts, self.root, True)

        pprintHierarchy(self.root)

    def groupAccountsByOneDimension(self, dimensions, accounts, root, isFirstLevel=False):
        if not dimensions:
            for account in accounts:
                self.createAccountLikeOriginal(account, root.getAccountForType(account.type))

            r = self.root
            Transaction(self.endYear, 'Profit & Loss', r.equity, root.profits, 
                        root.income.balance - root.expense.balance)
            Transaction(self.endYear, 'Net Assets', r.equity, root.netAssets, 
                        root.profits.balance + root.equity.balance)
            return

        dimensionOrMember = dimensions.pop()
        keyFunc = dimensionOrMember.getMemberForAccount

        for dimMember, accountGroup in groupby(sorted(accounts, key=keyFunc), keyFunc):
            roots = PropertyScopedStandardAccounts(root, dimMember)
            self.groupAccountsByOneDimension(list(dimensions), accountGroup, roots)

    def createAccountLikeOriginal(self, original, parent):
        account = Account(parent, name=original.name, dimensionMembers=original.dimensionMembers)
        account.makeInitialTransaction(self.root.equity, original.balance)
