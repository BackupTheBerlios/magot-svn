import cPickle

from peak.api import *
from datetime import *

from magot.model import *
from magot.refdata import *
from magot.storage import *

def makeDB(filename):

    CREDIT = MovementType.CREDIT
    DEBIT = MovementType.DEBIT

    # Root of all accounts
    root = Account(name='root')

    # ##################
    # Debit accounts
    # ##################

    # Asset accounts
    assets = EntryAccount(root, 'Assets', DEBIT)

    # Current assets
    currentAssets = EntryAccount(assets, 'Current Assets')
    cash = EntryAccount(currentAssets, 'Cash')
    tBills = EntryAccount(currentAssets, 'T-Bills')
    receivable = EntryAccount(currentAssets, 'Accounts Receivable')

    # Inventory
    inventory = EntryAccount(assets, 'Inventory')
    rawMaterials = EntryAccount(inventory, 'Raw Materials')
    wip = EntryAccount(inventory, 'Work-In-Progress')
    finishedGoods = EntryAccount(inventory, 'Finished Goods')

    # LongTerm assets
    longTermAssets = EntryAccount(assets, 'Long-Term Assets')
    land = EntryAccount(longTermAssets, 'Land')
    machinery = EntryAccount(longTermAssets, 'Machinery')
    depreciation = EntryAccount(longTermAssets, 'Depreciation')
    patents = EntryAccount(longTermAssets, 'Patents')
    
    # Expense accounts
    expense = EntryAccount(root, 'Expenses', DEBIT)
    warranty = EntryAccount(expense, 'Warranty')
    computer = EntryAccount(expense, 'Computer')

    
    # ##################
    # Credit accounts
    # ##################

    # Debt accounts
    liabilities = EntryAccount(root, "Liabilities and Owners' Equity", CREDIT)

    currentLiabilities = EntryAccount(liabilities, 'Short-Term liabilities')
    accPayable = EntryAccount(currentLiabilities, 'Accounts Payable')
    divPayable = EntryAccount(currentLiabilities, 'Dividend Payable')
    taxesPayable = EntryAccount(currentLiabilities, 'Taxes Payable')
    
    longTermLiabilities = EntryAccount(liabilities, 'Long-Term liabilities')
    loans = EntryAccount(longTermLiabilities, 'Bank Loans')

    equity = EntryAccount(liabilities, "Owners' Equity")
    capital = EntryAccount(equity, "Capital")
    retainedEarnings = EntryAccount(equity, "Retained Earnings")

    # Income accounts
    income = EntryAccount(root, 'Income', CREDIT)
    salary = EntryAccount(income, 'Salaries')


    # ##################
    # Initial balances
    # ##################
    cash.makeInitialTransaction(capital, Money(500000), Date(2005,2,1))
    tBills.makeInitialTransaction(capital, Money(1000000), Date(2005,2,2))
    receivable.makeInitialTransaction(capital, Money(7000000), Date(2005,2,3))

    rawMaterials.makeInitialTransaction(capital, Money(825000), Date(2005,2,1))
    wip.makeInitialTransaction(capital, Money(750000), Date(2005,2,2))
    finishedGoods.makeInitialTransaction(capital, Money(1200000), Date(2005,2,3))
    
    land.makeInitialTransaction(capital, Money(30000000), Date(2005,2,1))
    machinery.makeInitialTransaction(capital, Money(20000000), Date(2005,3,1))
    Transaction(date.today(), "First depreciation", capital, depreciation, Money(5000000))
    patents.makeInitialTransaction(capital, Money(1000000), Date(2005,5,1))

    computer.makeInitialTransaction(capital, Money(999), Date(2005,11,1))
    warranty.makeInitialTransaction(capital, Money(253), Date(2005,1,1))
    salary.makeInitialTransaction(capital, Money(2133), Date(2005,1,1))

    cPickle.dump(root, open(filename,'w'))


def readDB():
    root = cPickle.load(open(filename))
    assert root.name == 'root'

if __name__ == '__main__':   
    #makeDB()
    readDB()
