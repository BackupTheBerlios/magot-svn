from datetime import *
from peak.api import *
from magot.model import *
from magot.refdata import *


class Magot(commands.Bootstrap): 

    acceptURLs = False
    
    usage = """
Usage: run <command> [<arguments>]

Available commands:

    gui -- launch user interface
    newdb -- creates a new database
    accounts -- displays all accounts with their balances
    account accountName -- displays one account
    check -- check the accounting equation
    addTx desc debit credit amount [date, num]-- add a new Transaction
"""

    Accounts = binding.Make(
        'magot.storage.AccountDM', offerAs=[storage.DMFor(EntryAccount)]
    )

class newDatabaseCmd(commands.AbstractCommand):

    usage = """
Usage: newdb

create a new database.
"""

    Accounts = binding.Obtain(storage.DMFor(EntryAccount))

    def _run(self):
        if len(self.argv)<1:
            raise commands.InvocationError("Missing command")
            
        from magot.tests import test_storage
        test_storage.makeDB()


class displayAccountsCmd(commands.AbstractCommand):

    usage = """
Usage: accounts

Displays all accounts.
"""

    Accounts = binding.Obtain(storage.DMFor(EntryAccount))

    def _run(self):
        if len(self.argv)<1:
            raise commands.InvocationError("Missing command")
        storage.beginTransaction(self)
        
        for acc1 in self.Accounts.root.subAccounts:
            print >>self.stdout, repr(acc1)
            for acc2 in acc1.subAccounts:
                print >>self.stdout, '\t' + repr(acc2)

        storage.commitTransaction(self)


class checkEquationCmd(commands.AbstractCommand):

    usage = """
Usage: check

Checks the accounting equation : Assets + Expenses = Equity + Liabilities + Income
"""

    Accounts = binding.Obtain(storage.DMFor(EntryAccount))

    def _run(self):
        if len(self.argv)<1:
            raise commands.InvocationError("Missing command")
        storage.beginTransaction(self)
        debit = credit = Money.Zero
        for account in self.Accounts.root.subAccounts:
            if account.type is MovementType.DEBIT:
                debit += account.balance
            else:
                credit += account.balance
        assert debit == credit, 'The accounting equation is not correct'
        print 'The accounting equation is correct'
        storage.commitTransaction(self)


class displayAccountCmd(commands.AbstractCommand):

    usage = """
Usage: account accountName

Displays one account.
"""

    Accounts = binding.Obtain(storage.DMFor(EntryAccount))

    def _run(self):
        if len(self.argv)<2:
            raise commands.InvocationError("Missing account name")
        storage.beginTransaction(self)

        account = self.Accounts.get(self.argv[1])
        print >>self.stdout, str(account)
        if isinstance(account, EntryAccount):
            for entry in account.entries:
                print >>self.stdout, str(entry)

        storage.commitTransaction(self)


class addTransactionCmd(commands.AbstractCommand):

    usage = """
Usage: addTx desc debit credit amount [date num]

Add a new Transaction.
"""

    Accounts = binding.Obtain(storage.DMFor(EntryAccount))
   
    def _run(self):
   
        if len(self.argv)<5:
            raise commands.InvocationError("Missing arguments")

        parts = ' '.join(self.argv[1:]).split(' ')
        if len(parts) != 4:
            raise commands.InvocationError("Bad argument format")
            
        desc, debit, credit, amount = [part.strip() for part in parts]
        
        storage.beginTransaction(self)
        
        debitAcc = self.Accounts.get(debit)
        creditAcc = self.Accounts.get(credit)
        tx = Transaction(date.today(), desc, debitAcc, creditAcc, amount)

        storage.commitTransaction(self)
