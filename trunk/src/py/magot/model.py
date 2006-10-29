""" Domain model for basic accounting and multidimensional analysis. """

from magot.refdata import *
from magot.util import *

from peak.model import features, datatypes, elements
from peak.events import sources



class Dimension(elements.Element):
    """ A Dimension for which an Account may have one of its members. 
    Ex: dimension = Dimension(Location), member = Location(CityA), account = Account(Sales100)
    ==> dimension.getMemberForAccount(account) == member if Sales100 is located in CityA.
    """

    class name(features.Attribute):
        referencedType = datatypes.String

    class desc(features.Attribute):
        referencedType = datatypes.String

    def getMemberForAccount(self, account):
        return account.getMemberForDimension(self)

    def __eq__(self, other):
        return self.name == other.name
        
    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.__class__.__name__+'('+self.name+')'

    __str__ = __repr__


class MemberClass(elements.ElementClass):

    def __new__(cls, name, bases, cdict):
        member = super(MemberClass, cls).__new__(cls, name, bases, cdict)
        # A single Dimension instance for all member instances having the same dimension.
        member.dimension = Dimension(name=name, desc=name)
        return member


class DimensionMember(Dimension):

    __metaclass__ = MemberClass

    class dimension(features.Attribute):
        referencedType = Dimension

    class superMembers(features.Collection):
        """ Define a 'container' or 'wrapping' relationship.
        ex1: The dimension member 'CityA' has the super member 'RegionA'.
        ex2: The dimension member 'apartment100' has super members '2-roomed' and 'CityA'. """
        referencedType = 'DimensionMember'
        singularName = 'superMember'

    def getMemberForAccount(self, account):
        """ Redefined from Dimension class. """
        if account.hasMember(self):
            return self
        else:
            return None

    def getMemberForDimension(self, dimension):
        """ Return the member having the given dimension from itself or all super members. """
        if self.dimension == dimension:
            return self

        for member in self.superMembers:
            m = member.getMemberForDimension(dimension)
            if m is not None:
                return m
        return None


class DimensionAttribute(features.Attribute):
    """ Attribute that is used in a dimension member. """

    def _onLink(attr, member, superMember, posn):
        member.addSuperMember(superMember)

    def _onUnlink(attr, member, superMember, posn):
        member.removeSuperMember(superMember)





class Entry(elements.Element):

    class description(features.Attribute):
        referencedType = datatypes.String
        defaultValue = ''
        def get(self, entry):
            if not entry.transaction.isSplit:
                return entry.transaction.description
            else:
                return self

        def set(self, entry, value):
            if not entry.transaction.isSplit:
                entry.transaction.description = value
            else:
                self = value

    class isDebit(features.Attribute):
        """ It's a debit or credit entry? """
        referencedType = datatypes.Boolean

        def _onLink(self, entry, item, posn):
            entry.account.balance_dirty = True

    class amount(features.Attribute):
        referencedType = Money

        def _onLink(self, entry, item, posn):
            entry.account.balance_dirty = True

    class date(features.DerivedFeature):
        referencedType = Date

        def get(feature, element):
            return element.transaction.date

    class account(features.Attribute):
        referencedType = 'Account'
        referencedEnd = 'entries'

    class transaction(features.Attribute):
        referencedType = 'Transaction'
        referencedEnd = 'entries'
        # todo isChangeable = False ???

    class isReconciled(features.Attribute):
        referencedType = datatypes.Boolean
        defaultValue = False

    class balance(DerivedAndCached):
        """ Account balance after the addition of this entry in the account. """
        referencedType = Money

        def compute(self, entry):
            # Entry balance is set by calling account.balance if not already set.
            entry.account.balance
            return self.get(entry)

    class number(features.DerivedFeature):
        referencedType = datatypes.String

        def get(self, entry):
            return getattr(entry.transaction, 'number', None)

    class siblings(features.DerivedFeature):
        """ List of other entries contained in the same transaction. """
        def get(self, entry):
            entries = list(entry.transaction.entries)
            entries.remove(entry)
            return entries

    class oppositeEntry(features.DerivedFeature):
        """ The first sibling entry contained in the same transaction. """
        def get(self, entry):
            return entry.siblings[0]

    def __init__(self, isDebit, transaction, account, amount=0):
        super(Entry, self).__init__(transaction=transaction)
        account.addEntry(self)
        self.amount = amount
        self.isDebit = isDebit

    def __str__(self):
        return "%s\t%s\t%s\t%s" % (str(self.date), str(self.isDebit), 
                                   str(self.amount), str(self.balance))
    def _changeIsDebit(self):
        self.isDebit = not self.isDebit
        
    def _update(self, account=None, isDebit=None, amount=None, desc=None, isReconciled=None):
        """ Update entry  attributes. """
        if account is not None:
            self.account.removeEntry(self)
            account.addEntry(self)
        if isDebit is not None:
            self._changeIsDebit()
            self.oppositeEntry._changeIsDebit()
        if amount is not None:
            self.amount = amount
        if desc is not None:
            self.description = desc
        if isReconciled is not None:
            self.isReconciled = isReconciled
  
    def getProxy(self):
        return Proxy(self)

    def getOriginalObject(self):
        return self


class AccountAttribute(DerivedAndCached):
    """ Attribute derived from account entries plus all sub-account entries.

        Sub-classes MUST define getOriginalEntryField and setDerivedEntryField methods.
        Default period is NONE i.e. this attribute is computed over all account entries. """

    def compute(self, account):
        # todo cache this computed local value?
        totalValue = self.__computeLocalValue(account)

        for subAccount in account.subAccounts:
            totalValue += self.get(subAccount)
        return totalValue

    def getPeriod(self):
        return None

    def _onUnlink(self, account, item, posn):
        """ Unset this account attribute on all parent accounts so that they can be recomputed. """
        parent = account.parent
        while isinstance(parent, Account):
            self.unset(parent)
            parent = parent.parent

    def __computeLocalValue(self, account):
        entries = account.entries
        period = self.getPeriod()
        if period:
            entries = (e for e in entries if period.contains(e.date))

        result = Money.Zero
        for entry in entries:
            if account.isDebit is entry.isDebit:
                result += self.getOriginalEntryField(entry)
            else:
                result -= self.getOriginalEntryField(entry)

            # Set derived field for the current entry.
            if self.setDerivedEntryField:
                self.setDerivedEntryField(entry, result)

        return result


class RootAccount(elements.Element):
    """ Root Account without parent nor entries. """

    isRoot = True

    class name(features.Attribute):
        referencedType = datatypes.String

    class description(features.Attribute):
        referencedType = datatypes.String
        defaultValue = ''

    class subAccounts(features.Collection):
        referencedType = 'Account'
        referencedEnd = 'parent'
        singularName = 'subAccount'

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    def traverseHierarchy(self, func, funcStartNode=True):
        """ Apply func to each account in the hierarchy, beginning with self if requested. """

        def traverseAux(account, depth, func):
            for child in account.subAccounts:
                func(child, depth)
                traverseAux(child, depth + 1, func)

        if funcStartNode:
            func(self, 0)
        traverseAux(self, 1, func)


class Account(RootAccount):
    
    isRoot = False

    """ Event source to notify any views interested in account hierarchy changes. """
    hierarchyChanged = sources.Broadcaster()

    class type(features.Attribute):
        """ One of : Asset, Expense, Income, Liability, Equity. """
        referencedType = AccountType
        
        def _onLink(self, account, accountType, posn):
            account.isDebit = accountType.isDebit

    class isDebit(features.Attribute):
        """ It's a debit or credit account? """
        referencedType = datatypes.Boolean
    
    class commodity(features.Attribute):
        referencedType = Currency
        defaultValue = Currency.EUR
        # todo derived from parent if not set?

    class parent(features.Attribute):
        """ The parent account in a hierarchy of accounts. """
        referencedType = 'RootAccount'
        referencedEnd = 'subAccounts'
        defaultValue = None

    class entries(features.Sequence):
        """ Ordered by entry date. """
        referencedType = Entry
        referencedEnd = 'account'
        singularName = 'entry'

        def add(self, account, entry):
            date = entry.date
            positions = [i for i,e in enumerate(account.entries) if e.date <= date]
            self._notifyLink(account, entry, len(positions))

        def _onLink(self, account, entry, posn):
            account.balance_dirty = True

        def _onUnlink(self, account, entry, posn):
            account.balance_dirty = True

    class dimensionMembers(features.Collection):
        """ Collection of DimensionMembers : used to group accounts by. """
        referencedType = DimensionMember
        singularName = 'dimensionMember'

        # Use an internal dictionary {Dimension:DimensionMember} dealing with all super members.
        def _onLink(self, account, member, posn):
            if not member.dimension in account._dimensionToMember:
                account._dimensionToMember[member.dimension] = [member]
                for m in member.superMembers:
                    self._onLink(account, m, posn)
            else:
                account._dimensionToMember[member.dimension].append(member)
                
        def _onUnlink(self, account, member, posn):
            if member.dimension in account._dimensionToMember:
                del account._dimensionToMember[member.dimension]
                for m in member.superMembers:
                    self._onUnlink(account, m, posn)

    def getMemberForDimension(self, dimension):
        """ Return the dimension member having the given dimension if account has it or None else. """
        return self._dimensionToMember.get(dimension, None)[0]

    def hasMember(self, member):
        return member in flatten(self._dimensionToMember.values())

    def hasAllDimensionAndMember(self, dimensionsAndMembers):
        if self._dimensionToMember:
            temp = self._dimensionToMember.keys() + flatten(self._dimensionToMember.values())
            return dimensionsAndMembers.issubset(temp)
        else:
            return False

    def hasAnyDimensionAndMember(self, dimensionsAndMembers):
        if self._dimensionToMember:
            temp = self._dimensionToMember.keys() + flatten(self._dimensionToMember.values())
            return len(dimensionsAndMembers.intersection(temp)) >= 1
        else:
            return False

    class balance(AccountAttribute):
        """ Sum of entry amounts (owned by current account & all sub-accounts). No period. """
        getOriginalEntryField = Entry.amount.get
        setDerivedEntryField = Entry.balance.set

        # Balance becomes dirty as soon as some fields change : subAccounts, entry date/amount/...
        metadata = NewAttribute('_dirty')

        def recompute(self, account, force=False, entryToo=True):
            """ Unseting all account balances is sufficient to recompute them on demand. """
            if force or account.balance_dirty:
                Account.balance.unset(account)
                Account.balanceYTD.unset(account)

                if entryToo:
                    for entry in account.entries:
                        Entry.balance.unset(entry)

    class balanceYTD(balance):
        """ Year To Date balance. """
        setDerivedEntryField = metadata = None

        def getPeriod(self):
            # todo true formula
            return DateRange(Date(2006, 1, 1), Date.today())

    def __init__(self, parent, name=None, type=None, description='', dimensionMembers=[]):
        super(Account, self).__init__(name, description)
        assert parent is not None
        self._dimensionToMember = {}
        self.dimensionMembers = dimensionMembers
        self.changedEvent = sources.Broadcaster()
        if type is None:
            self.type = parent.type
        else:
            self.type = type
        parent.addSubAccount(self)

    def __setstate__(self, dict):
        """ Restore state from pickleable content. """
        self.__dict__ = dict
        self.changedEvent = sources.Broadcaster()

    def __getstate__(self):
        """ Purge state for pickleable content. """
        try:
            del self.changedEvent
        except:
            pass
        return self.__dict__

    def __repr__(self):
        # todo better formatted repr
        name = 'NO_NAME'
        if hasattr(self, 'name'):
            name = self.name
        return name.ljust(10) + str(self.balance).rjust(15)
        
    def __str__(self):
        return self.name
    
    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def __eq__(self, other):
        return self.name == other.name
        
    def __hash__(self):
        return hash(self.name)

    def makeInitialTransaction(self, equity, amount, date=None):
        date = date or Date.today()
        if self.isDebit:
            return Transaction(date, 'initial balance', self, equity, amount)
        else:
            return Transaction(date, 'initial balance', equity, self, amount)    

    def update(self, parent=None, description=None, name=None):
        """ Change account attributes. """
        event = None
        if description is not None:
            self.description = description

        if name is not None:
            self.name = name

        if parent is not None:
            # Old and new parent have their balance changed. No need to change their entry balances.
            Account.balance.recompute(self.parent, force=True, entryToo=False)
            self.parent = parent
            Account.balance.recompute(parent, force=True, entryToo=False)
            event = self

        # Notify any hierarchies to refresh themself.
        Account.hierarchyChanged.send(event)


class Transaction(elements.Element):

    class date(features.Attribute):
        referencedType = Date

    class number(features.Attribute):
        referencedType = datatypes.Integer

    class description(features.Attribute):
        referencedType = datatypes.String
        defaultValue = ''

    class entries(features.Collection):
        referencedType = 'Entry'
        referencedEnd = 'transaction'
        singularName = 'entry'

    class isSplit(features.DerivedFeature):
        referencedType = datatypes.Boolean
        
        def get(self, transaction):
            return len(transaction.entries) > 2

    class isBalanced(features.DerivedFeature):
        referencedType = datatypes.Boolean

        def get(self, transaction):
            debit = credit = Money.Zero
            for entry in transaction.entries:
                if entry.isDebit:
                    debit += entry.amount
                else:
                    credit += entry.amount
            return debit == credit

    def __init__(self, date=Date.today(), description='', debit=None, credit=None, amount=None):
        super(Transaction,self).__init__(date=date, description=description)

        if debit and credit and amount:
            if not isinstance(amount, Money):
                amount = Money(amount)
            self._addDebitEntry(debit, amount)
            self._addCreditEntry(credit, amount)

    def post(self, *modifiedEntries):
        """ Always use this method to post a transaction. """
        # todo split
        entry = modifiedEntries[0]

        accounts = set(e.account for e in self.entries)

        newOppositeAccount = entry.getModifiedAttr('oppositeAccount')
        if newOppositeAccount:
            accounts.add(newOppositeAccount)

        for account in accounts:
            account.balance_dirty = False  # Re-init _dirty attribute for the account balance.

        # Modifications on transaction attributes.
        self._update(date=entry.getModifiedAttr('date'),
                     nb=entry.getModifiedAttr('number'),
                     desc=entry.getModifiedAttr('description'),
                     amount=entry.getModifiedAttr('amount'))

        # Modifications on entry attributes.
        entry._update(isReconciled=entry.getModifiedAttr('isReconciled'), 
                      isDebit=entry.getModifiedAttr('isDebit'))

        # Modifications on the opposite entry attributes.
        entry.oppositeEntry._update(account=newOppositeAccount)

        for account in accounts:
            # Balance may have changed ...
            Account.balance.recompute(account)
            # Notify any registered view to refresh itself with this modified account.
            account.changedEvent.send(None)

        # todo send this event only if any account balance has changed.
        Account.hierarchyChanged.send(None)

    def _addDebitEntry(self, account, amount):
        entry = Entry(True, self, account, amount)
        Account.balance.recompute(account)
        return entry

    def _addCreditEntry(self, account, amount):
        entry = Entry(False, self, account, amount)
        Account.balance.recompute(account)
        return entry

    def _update(self, date=None, nb=None, desc=None, amount=None):
        """ Change transaction attributes. """
        if date is not None:
            assert self.date != date
            self.date = date
            for e in self.entries:
                account = e.account
                account.removeEntry(e)
                account.addEntry(e)    # Entry is replaced at the right place
        if nb is not None:
            self.number = nb
        if desc is not None:
            self.description = desc
        if amount is not None:
            if self.isSplit:
                raise "Can't update transaction amount because it's split"
            for entry in self.entries:
                entry._update(amount=amount)
