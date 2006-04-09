""" Domain model for basic accounting. Version2. """

from peak.api import *
from magot.refdata import *
import datetime


class DerivedAndCached(model.Attribute):
    """ Value is computed only if it's not locally set. """

    def get(feature, element):
        try:
            return element.__dict__[feature.attrName]
        except KeyError:
            value = feature.compute(element)
            feature.set(element, value)
            return value

    def compute(feature, element):
        raise NotImplementedError


class Proxy(object):
    """The Proxy base class."""

    def __init__(self, obj):
        """The initializer."""
        super(Proxy, self).__init__(obj)
        # Original object.
        self._obj = obj

    def __getattr__(self, attr):
        try:
            # Is this attribute overridden in the proxy?
            return self.__dict__[attr]
        except KeyError:
            # If not, then return the attribute value from the original object
            return getattr(self._obj, attr)

    def getModifiedAttr(self, attr):
        modified = self.__dict__.get(attr, None)
        try:
            if modified != getattr(self._obj, attr):
                return modified
            else:
                return None
        except AttributeError:
            return modified

    def getOriginalObject(self):
        return self._obj


class Entry(model.Element):

    class description(model.Attribute):
        referencedType = model.String
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

    class type(model.Attribute):
        # todo type is reserved key choose anoth
        referencedType = MovementType

    class amount(model.Attribute):
        referencedType = Money
        newVerbs = [('get_event', '%(singularName)sEvent')]

        def get_event(feature, element):
            key = feature.attrName+'__event'
            try:
                source = element.__dict__[key]
                return source
            except KeyError:
                source = element.__dict__.setdefault(key, events.Broadcaster())
                return source

        def _onLink(feature, element, item, posn=None):
            source = feature.get_event(element)
            source.send(item)

        def addCallback(feature, element, callback):
            source = feature.get_event(element)
            unsubscribe = events.subscribe(source, callback)
            return unsubscribe
     
    class account(model.Attribute):
        #referencedType = Account
        referencedEnd = 'entries'

    class transaction(model.Attribute):
        #referencedType = Transaction
        referencedEnd = 'entries'
        # todo isChangeable = False ???

    class isReconciled(model.Attribute):
        referencedType = model.Boolean
        defaultValue = False

    class balance(DerivedAndCached):
        """ Account balance at the entry update/insert date. 
            todo : improved algorithm using memoized balances"""
        referencedType = Money        
        def compute(self, entry):
            entries = entry.account.entries
            previousBalance = Money.Zero
            i = entries.index(entry)
            if i > 0:
                # recursif
                previousBalance = entries[i-1].balance
            
            if entry.type is entry.account.type:
                previousBalance += entry.amount
            else:
                previousBalance -= entry.amount
            
            return previousBalance

    class date(model.DerivedFeature):
        referencedType = Date        
        def get(self, entry):
            return entry.transaction.date

    class number(model.DerivedFeature):
        referencedType = model.Integer        
        def get(self, entry):
            if hasattr(entry.transaction, 'number'):
                return entry.transaction.number
            else:
                return None

    class siblings(model.DerivedFeature):
        """ List of other entries contained in the same transaction. """        
        def get(self, entry):
            entries = list(entry.transaction.entries)
            entries.remove(entry)
            return entries

    class oppositeEntry(model.DerivedFeature):
        """ The first sibling entry contained in the same transaction. """        
        def get(self, entry):
            return entry.siblings[0]

    def __init__(self, type, transaction, account=None, amount=0):
        super(Entry, self).__init__(type=type, amount=amount, 
                                    transaction=transaction)
        account.addEntry(self)

    def __getstate__(self):
        """ Purge state for picklable content. """
        odict = self.__dict__
        key = 'amount__event'
        try:
            del odict[key]
        except KeyError:
            pass
        return odict

    def __setstate__(self, dict):
        """ Restore state from picklable content. """
        self.__dict__ = dict
        Entry.amount.addCallback(self, self.account.emptyBalanceCacheCallback)
        evt = self.amountEvent()
        evt.send(self.amount)

    def __str__(self):
        return "%s\t%s\t%s\t%s" % (str(self.date), str(self.type),
                                   str(self.amount), str(self.balance))
    def _changeType(self):
        if self.type == MovementType.CREDIT:
            self.type = MovementType.DEBIT
        else:
            self.type = MovementType.CREDIT
        
    def _update(self, account=None, type=None, amount=None, desc=None, 
               isReconciled=None):
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
        

class AccountAttribute(DerivedAndCached):
    
    """ Derived account attribute from local entries plus sub-account entries."""
    def compute(self, account):
        value = self.__localValue(account)
        for subAccount in account.subAccounts:
            value += self.get(subAccount)        
        return value

    def getPeriod(self):                      
        return None

    def __localValue(self, account):
        entries = account.entries
        period = self.getPeriod()
        if period is not None:
            entries = (e for e in entries if period.contains(e.date))
        
        result = Money.Zero
        for entry in entries:
            if entry.type is MovementType.DEBIT:
                result += self.getField(entry)
            else:
                result -= self.getField(entry)
        
        if account.type is MovementType.CREDIT:
            return -result
        else:
            return result 


class RootAccount(model.Element):
    """ Root Account without parent and entries. """

    class name(model.Attribute):
        referencedType = model.String

    class description(model.Attribute):
        referencedType = model.String
        defaultValue = ''

    class subAccounts(model.Collection):
        referencedType = 'Account'
        referencedEnd = 'parent'
        singularName = 'subAccount'

    def __init__(self, name=None, description=None):
        self.name = name
        self.description = description


class Account(RootAccount):
    
    class type(model.Attribute):
        """ debit or credit. """
        referencedType = MovementType
##        isChangeable = False
        # todo isChangeable = False ???
        # how to initialize unchangeable feature ?
        # todo derived from parent if not set?

    class commodity(model.Attribute):
        referencedType = Currency
        defaultValue = Currency.EUR
        # todo derived from parent if not set?

    class parent(model.Attribute):
        referencedType = 'RootAccount'
        referencedEnd = 'subAccounts'
        defaultValue = None

    class entries(model.Sequence):
        """ Ordered by entry date. """
        referencedType = 'Entry'
        referencedEnd = 'account'
        singularName = 'entry'

        def add(self, account, entry):
            date = entry.date
            positions = [i for i,e in enumerate(account.entries) if e.date <= date]
            self._notifyLink(account, entry, len(positions))
   
    class balance(AccountAttribute):
        """ Total amount of all entries (local & sub-accounts). No period. """       
        getField = Entry.amount.get
        
        def get_event(feature, element):
            key = feature.attrName+'__event'
            try:
                source = element.__dict__[key]
                return source
            except KeyError:
                source = element.__dict__.setdefault(key, events.Distributor())
                return source

        def _onLink(feature, element, item, posn=None):
            source = feature.get_event(element)

        def addCallback(feature, element, callback):
            source = feature.get_event(element)
            unsubscribe = events.subscribe(source, callback)
            return unsubscribe      

    class balanceMTD(balance):
        """ Balance since start of the current Month. """
        def getPeriod(self):
             # todo true formula
            return DateRange(date(2006, 4, 3), date(2006, 4, 4))


    def __init__(self, parent, name=None, type=None):
        assert parent is not None
        self.parent = parent
        self.name = name
        if type is None:
            self.type = self.parent.type
        else:
            self.setType(type)

    def __repr__(self):
        # todo better formatted repr
        return self.name.ljust(10) + self.description.rjust(25) + \
            str(self.balance).rjust(8)
        
    def __str__(self):
        return self.name
    
    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def makeInitialTransaction(self, equity, amount, date=None):        
        date = date or datetime.date.today()
        if self.type is MovementType.DEBIT:
            return Transaction(date, 'initial balance', self, equity, amount)
        else:
            return Transaction(date, 'initial balance', equity, self, amount)    

    def emptyBalanceCacheCallback(self, source, event):
        self.unsetBalance()
        if self.parent is not None and not isinstance(self.parent, Account):
            self.parent.emptyBalanceCacheCallback(source, event)
        for entry in self.entries:
            entry.unsetBalance()
            
        source = Account.balance.get_event(self)
        source.send(None)


class Transaction(model.Element):

    class date(model.Attribute):
        referencedType = Date

    class number(model.Attribute):
        referencedType = model.Integer

    class description(model.Attribute):
        referencedType = model.String
        defaultValue = ''

    class entries(model.Collection):
        referencedType = 'Entry'
        referencedEnd = 'transaction'
        singularName = 'entry'

    class isSplit(model.DerivedFeature):
        referencedType = model.Boolean
        
        def get(self, transaction):
            return len(transaction.entries) > 2

    class isBalanced(model.DerivedFeature):
        referencedType = model.Boolean

        def get(self, transaction):
            debit = credit = Money.Zero
            # todo use list comprehension
            for entry in transaction.entries:
                if entry.type is MovementType.DEBIT:
                    debit += entry.amount
                else:
                    credit += entry.amount
            
            return debit == credit

    def __init__(self, date, description, debit=None, credit=None, amount=None):

        if debit is None or credit is None or amount is None:
            super(Transaction,self).__init__(date=date, description=description)
        else:
            if not isinstance(amount, Money):
                amount = Money(amount)

            super(Transaction,self).__init__(date=date, description=description)
            self._addDebitEntry(debit, amount)
            self._addCreditEntry(credit, amount)

    def post(self, *entries):
        """ Always use this method to post a transaction. """        
        # todo split
        entry = entries[0]
                
        # modifications on tx attributes
        self._update(
            date=entry.getModifiedAttr('date'),
            nb=entry.getModifiedAttr('number'),
            desc=entry.getModifiedAttr('description'),
            amount=entry.getModifiedAttr('amount'))

        # modifications on entry attributes
        entry._update(
            isReconciled=entry.getModifiedAttr('isReconciled'),
            type=entry.getModifiedAttr('type'))

        # modifications on the opposite entry attributes
        entry.oppositeEntry._update(
            account=entry.getModifiedAttr('oppositeAccount'))
        
    def _addDebitEntry(self, account, amount):        
        return Entry(MovementType.DEBIT, self, account, amount)

    def _addCreditEntry(self, account, amount):
        return Entry(MovementType.CREDIT, self, account, amount)

    def _update(self, date=None, nb=None, desc=None, amount=None):
        """ Always use this method to post a transaction. """
        if date is not None:
            self.date = date
            for e in self.entries:
                account = e.account
                account.removeEntry(e)
                account.addEntry(e)
        if nb is not None:
            self.number = nb
        if desc is not None:
            self.description = desc
        if amount is not None:
            if self.isSplit:
                raise "Can't update transaction amount because it's split"
            for entry in self.entries:
                entry._update(amount=amount)        
