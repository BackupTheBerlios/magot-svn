import cPickle

from peak.api import *
from datetime import *

from magot.model import *
from magot.refdata import *
from magot.storage import *

filename = config.fileNearModule('magot', 'account.list')

def makeDB():

    CREDIT = MovementType.CREDIT
    DEBIT = MovementType.DEBIT

    # root of all accounts
    root = Account(name='root')

    # ##################
    # Debit accounts
    # ##################

    # Asset accounts
    
    assets = EntryAccount(root, 'Assets', DEBIT)
    
    currentAssets = EntryAccount(assets, 'Current assets')

    cash = EntryAccount(currentAssets, 'Cash')
    tBills = EntryAccount(currentAssets, 'T-Bills')
    receivable = EntryAccount(currentAssets, 'Accounts Receivable')
    
    inventory = EntryAccount(assets, 'Inventory')
    
    rawMaterials = EntryAccount(inventory, 'Raw Materials')
    wip = EntryAccount(inventory, 'Work-in-progress')
    finishedGoods = EntryAccount(inventory, 'Finished Goods')
   
    longTermAssets = EntryAccount(assets, 'Long-Term assets')

    land = EntryAccount(longTermAssets, 'Land')
    machinery = EntryAccount(longTermAssets, 'Machinery')
    depreciation = EntryAccount(longTermAssets, 'Depreciation', CREDIT)
    patents = EntryAccount(longTermAssets, 'Patents')
    
    # Expense accounts
    
    expense = EntryAccount(root, 'Expenses', DEBIT)
    warranty = EntryAccount(expense, 'Warranty')

    
    # ##################
    # Credit accounts
    # ##################

    # Debt accounts
    
    liabilities = EntryAccount(root, "Liabilitie and Owners' Equity", CREDIT)

    currentLiabilities = EntryAccount(liabilities, 'Short-Term liabilities')
    accPayable = EntryAccount(currentLiabilities, 'Accounts Payable')
    divPayable = EntryAccount(currentLiabilities, 'Dividend Payable')
    taxesPayable = EntryAccount(currentLiabilities, 'Taxes Payable')
    
    longTermLiabilities = EntryAccount(liabilities, 'Long-Term liabilities')
    loans = EntryAccount(longTermLiabilities, 'Bank Loans')

    equity = EntryAccount(root, "Owners' Equity", CREDIT)
    capital = EntryAccount(equity, "Capital")
    retainedEarnings = EntryAccount(equity, "Retained Earnings")
    
    # Income accounts
    
    income = EntryAccount(root, 'Income', CREDIT)
    salary = EntryAccount(income, 'Salaries')


    # set all initial balances
    cash.makeInitialTransaction(capital, Money(500000), Date(2005,2,1))
    tBills.makeInitialTransaction(capital, Money(1000000), Date(2005,2,1))
    receivable.makeInitialTransaction(capital, Money(7000000), Date(2005,2,1))

    rawMaterials.makeInitialTransaction(capital, Money(825000), Date(2005,2,1))
    wip.makeInitialTransaction(capital, Money(750000), Date(2005,2,1))
    finishedGoods.makeInitialTransaction(capital, Money(1200000), Date(2005,2,1))
    
    land.makeInitialTransaction(capital, Money(30000000), Date(2005,2,1))
    machinery.makeInitialTransaction(capital, Money(20000000), Date(2005,2,1))
    depreciation.makeInitialTransaction(capital, Money(5000000), Date(2005,2,1))
    patents.makeInitialTransaction(capital, Money(1000000), Date(2005,2,1))
    
##    computer.makeInitialTransaction(capital, Money(2), Date(2005,1,1))
##    warranty.makeInitialTransaction(capital, Money(3), Date(2005,1,1))
##    cash.makeInitialTransaction(capital, Money(4), Date(2005,2,1))
##    salary.makeInitialTransaction(capital, Money(100.5), Date(2005,1,1))
##
##    assert checking.balance == Money(1)
##    assert computer.balance == Money(2)
##    assert assets.balance == Money(3)
##    assert warranty.balance == Money(3)
##    assert cash.balance == Money(4)
##    assert expense.balance == Money(7)       
##    assert salary.balance == Money(100.5)
##    assert equity.balance == Money(-90.5)    

    cPickle.dump(root, open(filename,'w'))


def readDB():
    root = cPickle.load(open(filename))
    assert root.name == 'root'

if __name__ == '__main__':   
    #makeDB()
    readDB()
