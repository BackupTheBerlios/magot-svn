import cPickle

from peak.api import *
from datetime import *

from magot.model import *
from magot.refdata import *
from magot.storage import *

filename = config.fileNearModule('magot', 'account.list')

def makeDB():
    # create all accounts
    root = DetailAccount(name='root')
    # debit accounts
    asset = DetailAccount(parent=root, name='asset', type=MovementType.DEBIT)
    checking = DetailAccount(parent=asset, name='checking', type=MovementType.DEBIT)
    computer = DetailAccount(parent=asset, name='computer', type=MovementType.DEBIT)
    expense = DetailAccount(parent=root, name='expense', type=MovementType.DEBIT)
    warranty = DetailAccount(parent=expense, name='warranty', type=MovementType.DEBIT)
    cash = DetailAccount(parent=expense, name='cash', type=MovementType.DEBIT)
    # credit accounts
    income = DetailAccount(parent=root, name='income', type=MovementType.CREDIT)
    salary = DetailAccount(parent=income, name='salary', type=MovementType.CREDIT)
    liability = DetailAccount(parent=root, name='liability', type=MovementType.CREDIT)
    loan = DetailAccount(parent=liability, name='loan', type=MovementType.CREDIT)
    equity = DetailAccount(parent=root, name='equity', type=MovementType.CREDIT)
    
    # set all initial balances
    checking.makeInitialTransaction(equity, Money(1), date(2005,2,1))
    assert checking.balance == Money(1)
    computer.makeInitialTransaction(equity, Money(2), date(2005,1,1))
    assert computer.balance == Money(2)
    assert asset.balance == Money(3)
    warranty.makeInitialTransaction(equity, Money(3), date(2005,1,1))
    assert warranty.balance == Money(3)
    cash.makeInitialTransaction(equity, Money(4), date(2005,2,1))
    assert cash.balance == Money(4)
    assert expense.balance == Money(7)       
    salary.makeInitialTransaction(equity, Money(100.5), date(2005,1,1))
    assert salary.balance == Money(100.5)
    assert equity.balance == Money(-90.5)    

    cPickle.dump(root, open(filename,'w'))


def readDB():
    root = cPickle.load(open(filename))
    assert root.name == 'root'

if __name__ == '__main__':   
##~     makeDB()
    readDB()
