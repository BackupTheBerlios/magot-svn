""" Domain model for basic accounting. Version2. """

from peak.model import elements, features, datatypes
from peak.events import sources

from magot.refdata import *
from magot.util import *


class DimensionMember(elements.Element):

    class code(features.Attribute):
        referencedType = datatypes.String

    class desc(features.Attribute):
        referencedType = datatypes.String

    class dimension(features.Attribute):
        referencedType = 'Dimension'
        referencedEnd = 'members'


class Dimension(elements.Element):

    class name(features.Attribute):
        referencedType = datatypes.String

    class members(features.Collection):
        referencedType = DimensionMember
        referencedEnd = 'dimension'
        singularName = 'member'


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

    class type(features.Attribute):
        # todo type is a reserved key choose another one
        referencedType = MovementType

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

    def __init__(self, type, transaction, account, amount=0):
        super(Entry, self).__init__(transaction=transaction)
        account.addEntry(self)
        self.amount = amount
        self.type = type

    def __str__(self):
        return "%s\t%s\t%s\t%s" % (str(self.date), str(self.type), 
                                   str(self.amount), str(self.balance))
    def _changeType(self):
        if self.type == MovementType.CREDIT:
            self.type = MovementType.DEBIT
        else:
            self.type = MovementType.CREDIT
        
    def _update(self, account=None, type=None, amount=None, desc=None, isReconciled=None):
        """ Update entry  attributes. """
        if account is not None:
            self.account.removeEntry(self)
            account.addEntry(self)
        if type is not None:
            self._changeType()
            self.oppositeEntry._changeType()
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
            if account.type is entry.type:
                result += self.getOriginalEntryField(entry)
            else:
                result -= self.getOriginalEntryField(entry)

            # Set derived field for the current entry.
            if self.setDerivedEntryField:
                self.setDerivedEntryField(entry, result)

        return result


class RootAccount(elements.Element):
    """ Root Account without parent and entries. """

    class name(features.Attribute):
        referencedType = datatypes.String

    class description(features.Attribute):
        referencedType = datatypes.String
        defaultValue = ''

    class subAccounts(features.Collection):
        referencedType = 'Account'
        referencedEnd = 'parent'
        singularName = 'subAccount'

    def __init__(self, name=None, description=None):
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
    
    """ Event source to notify any views interested in account hierarchy changes. """
    hierarchyChanged = sources.Broadcaster()
    
    class type(features.Attribute):
        """ debit or credit. """
        referencedType = MovementType
#        isChangeable = False
        # todo isChangeable = False ???
        # how to initialize unchangeable feature ?
        # todo derived from parent if not set?

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
        referencedType = 'Entry'
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
    
    class dimensions(features.Collection):
        """ Collection of DimensionMembers. """
        referencedType = 'DimensionMember'
        singularName = 'dimension'

    class balance(AccountAttribute):
        """ Sum of entry amounts (owned by current account & all sub-accounts). No period. """
        getOriginalEntryField = Entry.amount.get
        setDerivedEntryField = Entry.balance.set

        # Balance becomes dirty as soon as some fields change : subAccounts, entry date/type/amount.
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

    def __init__(self, parent, name=None, type=None, description='', dimensions=[]):
        super(Account, self).__init__(name, description)
        assert parent is not None
        self.parent = parent
        self.dimensions = dimensions
        self.changedEvent = sources.Broadcaster()
        if type is None:
            self.type = self.parent.type
        else:
            self.type = type

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
        return name.ljust(10) + str(self.balance).rjust(30) #+ self.description.rjust(25) + str(self.balance).rjust(8)
        
    def __str__(self):
        return self.name
    
    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def makeInitialTransaction(self, equity, amount, date=None):
        date = date or Date.today()
        if self.type is MovementType.DEBIT:
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
                if entry.type is MovementType.DEBIT:
                    debit += entry.amount
                else:
                    credit += entry.amount
            return debit == credit

    def __init__(self, date=Date.today(), description='', debit=None, 
                 credit=None, amount=None):
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
                      type=entry.getModifiedAttr('type'))

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
        entry = Entry(MovementType.DEBIT, self, account, amount)
        Account.balance.recompute(account)
        return entry

    def _addCreditEntry(self, account, amount):
        entry = Entry(MovementType.CREDIT, self, account, amount)
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
