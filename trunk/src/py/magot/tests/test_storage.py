import cPickle

from peak.api import *
from datetime import *

from magot.model import *
from magot.refdata import *
from magot.storage import *

filename = config.fileNearModule('magot', 'account.list')

def makeDB():
    # create all accounts
    root = Account(name='root')
    # debit accounts
    equity = EntryAccount(parent=root, name='equity', type=MovementType.CREDIT, description="")
    asset = EntryAccount(parent=root, name='asset', type=MovementType.DEBIT, description="")
    checking = EntryAccount(parent=asset, name='checking', type=MovementType.DEBIT, description="")
    computer = EntryAccount(parent=asset, name='computer', type=MovementType.DEBIT, description="")
    expense = EntryAccount(parent=root, name='expense', type=MovementType.DEBIT, description="")
    warranty = EntryAccount(parent=expense, name='warranty', type=MovementType.DEBIT, description="")
    cash = EntryAccount(parent=expense, name='cash', type=MovementType.DEBIT, description="")
    # credit accounts
    income = EntryAccount(parent=root, name='income', type=MovementType.CREDIT, description="")
    salary = EntryAccount(parent=income, name='salary', type=MovementType.CREDIT, description="")
    liability = EntryAccount(parent=root, name='liability', type=MovementType.CREDIT, description="")
    loan = EntryAccount(parent=liability, name='loan', type=MovementType.CREDIT, description="")
    
    # set all initial balances
    checking.makeInitialTransaction(equity, Money(1), Date(2005,2,1))
    assert checking.balance == Money(1)
    computer.makeInitialTransaction(equity, Money(2), Date(2005,1,1))
    assert computer.balance == Money(2)
    assert asset.balance == Money(3)
    warranty.makeInitialTransaction(equity, Money(3), Date(2005,1,1))
    assert warranty.balance == Money(3)
    cash.makeInitialTransaction(equity, Money(4), Date(2005,2,1))
    assert cash.balance == Money(4)
    assert expense.balance == Money(7)       
    salary.makeInitialTransaction(equity, Money(100.5), Date(2005,1,1))
    assert salary.balance == Money(100.5)
    assert equity.balance == Money(-90.5)    

    cPickle.dump(root, open(filename,'w'))


def readDB():
    root = cPickle.load(open(filename))
    assert root.name == 'root'

if __name__ == '__main__':   
##~     makeDB()
    readDB()
