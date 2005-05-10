""" Domain model for basic accounting. """

from peak.api import *
from magot.refdata import *
from peak.util import fmtparse

class Account(model.Element):

    mdl_isAbstract = True
    
    class name(model.Attribute):
        referencedType = model.String

    class description(model.Attribute):
        referencedType = model.String
        defaultValue = ''

    class type(model.Attribute):
        referencedType = MovementType
        isChangeable = False

    class parent(model.Attribute):
        referencedType = 'SummaryAccount'
        referencedEnd = 'subAccounts'
        defaultValue = None

    class balance(model.DerivedFeature):
        referencedType = Money


    def __str__(self):
        return "%s\t\t%s\t\t%s" % (self.name, self.description, self.balance)


class SummaryAccount(Account):
    
    class subAccounts(model.Collection):
        referencedType = Account
        referencedEnd = 'parent'
        singularName = 'subAccount'

    class balance(model.DerivedFeature):
        referencedType = Money

        def get(feature, element):
            balance = Money.Zero
            for account in element.subAccounts:
                balance += account.balance
            return balance


class DetailAccount(Account):

    class commodity(model.Attribute):
        referencedType = Currency
        defaultValue = Currency.EUR
    
    class entries(model.Sequence):
        """ Ordered by entry date. """
        referencedType = 'Entry'
        referencedEnd = 'account'
        singularName = 'entry'

        def add(self, account, entry):
            date = entry.date
            positions = [i for i, e in enumerate(account.entries) if e.date <= date]
            self._notifyLink(account,entry, len(positions))

    class balance(model.DerivedFeature):
        referencedType = Money

        def get(feature, element):
            balance = Money.Zero
            for entry in element.entries:
                if entry.type is MovementType.DEBIT:
                    balance += entry.amount
                else:
                    balance -= entry.amount
            if element.type is MovementType.CREDIT:
                balance = Money(-balance.amount, balance.currency)
            return balance

    def makeInitialTransaction(self, equity, amount):
        
        if self.type is MovementType.DEBIT:
            return Transaction(date.today(), 'initial balance', self, equity, amount)
        else:
            return Transaction(date.today(), 'initial balance', equity, self, amount)


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
        
        def get(feature, element):
            return len(element.entries) > 2

    class isBalanced(model.DerivedFeature):
        referencedType = model.Boolean

        def get(feature, element):
            debit = credit = Money.Zero
            # TODO use list comprehension
            for entry in element.entries:
                if entry.type is MovementType.DEBIT:
                    debit += entry.amount
                else:
                    credit += entry.amount
            
            return debit == credit

    def __init__(self, date, description, debit=None, credit=None, amount=None):

        if debit is None or credit is None or amount is None:
            super(Transaction, self).__init__(date=date, description=description)
        else:
            if not isinstance(amount, Money):
                amount = Money(amount)

            super(Transaction, self).__init__(date=date, description=description)
            self.addDebitEntry(debit, amount)
            self.addCreditEntry(credit, amount)

    def addDebitEntry(self, account, amount):
        
        return Entry(MovementType.DEBIT, self, account, amount)

    def addCreditEntry(self, account, amount):
        
        return Entry(MovementType.CREDIT, self, account, amount)

    def update(self, date=None, nb=None, desc=None, amount=None):
        """ Always use this method to update a transaction. """
        if date is not None and date != self.date:
            self.date = date
            for e in self.entries:
                account = e.account
                account.removeEntry(e)
                account.addEntry(e)
        if nb is not None and nb != self.number:
            self.number = nb
        if desc is not None and desc != self.description:
            self.description = desc
        if amount is not None:
            if self.isSplit:
                raise AttributeError, "Can't update entry amount because tx is split"
            for e in self.entries:
                e.update(amount=amount)


class Entry(model.Element):

    class description(model.Attribute):
        referencedType = model.String
        defaultValue = ''

    class type(model.Attribute):
        referencedType = MovementType

    class amount(model.Attribute):
        referencedType = Money

    class account(model.Attribute):
        referencedType = DetailAccount
        referencedEnd = 'entries'

    class transaction(model.Attribute):
        referencedType = Transaction
        referencedEnd = 'entries'
        # TODO isChangeable = False ???

    class isReconciled(model.Attribute):
        referencedType = model.Boolean
        defaultValue = False

    class balance(model.DerivedFeature):
        """ Account balance at the entry update/insert time. 
            todo : improved algorithm """
        referencedType = Money
        
        def get(feature, element):
            entries = element.account.entries
            previousBalance = Money.Zero
            i = entries.index(element)
            if i > 0:
                # recursif
                previousBalance = entries[i-1].balance
            
            if element.type is element.account.type:
                previousBalance += element.amount
            else:
                previousBalance -= element.amount
            
            return previousBalance

    class date(model.DerivedFeature):
        referencedType = Date
        
        def get(self, entry):
            return entry.transaction.date

    class siblings(model.DerivedFeature):
        """ List of other entries contained in the same transaction. """
        
        def get(feature, element):
            siblings = list(element.transaction.entries)
            siblings.remove(element)
            return siblings

    def __init__(self, type, transaction, account=None, amount=0):
        super(Entry, self).__init__(type=type, amount=amount, transaction=transaction)
        account.addEntry(self)

    def __str__(self):
        return "%s\t%s\t%s\t%s" % (str(self.date), str(self.type),
            str(self.amount), str(self.balance))

    def update(self, account=None, type=None, amount=None, desc=None):
        if account is not None and account != self.account:
            self.account = account
        if type is not None and type != self.type:
            self.type = type
        if amount is not None and amount != self.amount:
            self.amount = amount
        if desc is not None and desc != self.description:
            self.description = desc
