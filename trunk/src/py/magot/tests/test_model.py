"""Unit tests for transaction creation/modification."""
# -*- coding: iso-8859-1 -*-

from unittest import TestCase, makeSuite, TestSuite
import unittest
import shelve
from datetime import *

from magot.model import *
from magot.refdata import *

def makeAccounts(self):
    # create all accounts
    self.root = SummaryAccount(name='Accounts')
    self.asset = SummaryAccount(parent=self.root, name='Asset')
    self.checking = DetailAccount(parent=self.asset, name='Checking', type=MovementType.DEBIT)
    self.computer = DetailAccount(parent=self.asset, name='Computer', type=MovementType.DEBIT)
    self.expense = SummaryAccount(parent=self.root, name='Expense', type=MovementType.DEBIT)
    self.warranty = DetailAccount(parent=self.expense, name='Warranty', type=MovementType.DEBIT)
    self.cash = DetailAccount(parent=self.expense, name='Cash', type=MovementType.DEBIT)
    self.income = SummaryAccount(parent=self.root, name='Income', type=MovementType.CREDIT)
    self.salary = DetailAccount(parent=self.income, name='Salary', type=MovementType.CREDIT)
    self.equity = DetailAccount(parent=self.root, name='Equity', type=MovementType.CREDIT)
    # set all initial balances
    self.checking.makeInitialTransaction(self.equity, Money(1))
    assert self.checking.balance == Money(1)
    self.computer.makeInitialTransaction(self.equity, Money(2))
    assert self.computer.balance == Money(2)
    assert self.asset.balance == Money(3)
    self.warranty.makeInitialTransaction(self.equity, Money(3))
    assert self.warranty.balance == Money(3)
    self.cash.makeInitialTransaction(self.equity, Money(4))
    assert self.cash.balance == Money(4)
    assert self.expense.balance == Money(7)       
    self.salary.makeInitialTransaction(self.equity, Money(100.5))
    assert self.salary.balance == Money(100.5)
    assert self.equity.balance == Money(-90.5)


class TestTransaction(TestCase):
    
    def setUp(self):
        makeAccounts(self)

    def check_ordered_entries(self, account):
        d = date(2003,1,1)
        for e in account.entries:
            assert d <= e.date, "%s > %s" % (d, e.date)
            d = e.date

    def test_account(self):
        # test parent relationship
        assert self.root.parent is None
        assert self.checking.parent is self.computer.parent is self.asset
        assert self.checking.parent.parent is self.salary.parent.parent is self.root
        # test subAccounts relationship
        assert self.root.subAccounts == [self.asset, self.expense, self.income, self.equity]
        assert self.asset.subAccounts == [self.checking, self.computer]
        assert self.expense.subAccounts == [self.warranty, self.cash]
        # test balance
        assert self.expense.balance == Money(7)
        assert self.asset.balance == Money(3)
        # move an account under a different parent
        assert self.cash.parent is self.expense
        self.cash.parent = self.asset
        assert self.cash.parent is self.asset
        assert self.asset.subAccounts == [self.checking, self.computer, self.cash]
        assert self.expense.subAccounts == [self.warranty]
        # test balance
        assert self.expense.balance == Money(3)
        assert self.asset.balance == Money(7)
        # add and remove an account DOES_NOT_WORK !!! use setParent instead or remove and add
        self.expense.addSubAccount(self.cash)
        assert self.cash.parent is self.expense
        assert self.expense.subAccounts == [self.warranty, self.cash]
        assert self.cash in self.asset.subAccounts # cash appears in 2 lists !!!
        self.asset.removeSubAccount(self.cash) # lets try to remove it
        assert self.cash not in self.asset.subAccounts 
        assert self.cash.parent is None # no parent anymore !!!
        # dont had anything after this line because relationships are incoherent !!!

    def test_2_ledged_transaction(self):
        # Get salary with check
        salary = Money(100.05)
        tx = Transaction(date.today(), 'Get salary with check', self.checking, self.salary, salary)
        assert tx.isBalanced
        debit = [e for e in tx.entries if e.type is MovementType.DEBIT][0]
        credit = [e for e in tx.entries if e.type is MovementType.CREDIT][0]
        assert debit in self.checking.entries
        assert credit in self.salary.entries
        # test account balance
        assert self.salary.balance == Money(100.5) + salary
        assert self.checking.balance == Money(1) + salary
        assert self.cash.balance == Money(4)
        # change entry account : get salary by cash instead of check
        self.checking.removeEntry(debit)
        self.cash.addEntry(debit)
        assert self.cash.balance == Money(4) + salary
        assert self.checking.balance == Money(1)
        assert debit in self.cash.entries
        assert debit not in self.checking.entries

    def test_4_ledged_transaction(self):
        # Buy a computer and a warranty by check and cash
        computerAmount = Money(999.99)
        warrantyAmount = Money(100)
        cashAmount = Money(500)
        checkAmount = Money(599.99)
        tx = Transaction(date.today(), 'Buy a computer and warranty')
        computer = tx.addDebitEntry(self.computer, computerAmount)            
        warranty = tx.addDebitEntry(self.warranty, warrantyAmount)
        checking = tx.addCreditEntry(self.checking, checkAmount)
        cash = tx.addCreditEntry(self.cash, cashAmount)
        assert tx.isBalanced
        # test relationships
        assert computer in self.computer.entries
        assert warranty in self.warranty.entries
        assert checking in self.checking.entries
        assert cash in self.cash.entries
        assert tx.entries == [computer, warranty, checking, cash]
        # test detail account balances
        assert self.checking.balance == Money(1) - checkAmount
        assert self.computer.balance == Money(2) + computerAmount
        assert self.warranty.balance == Money(3) + warrantyAmount
        assert self.cash.balance == Money(4) - cashAmount
        # test summary account balances
        assert self.asset.balance == Money(3) - checkAmount + computerAmount
        assert self.expense.balance == Money(7) + warrantyAmount - cashAmount
        assert self.income.balance == Money(100.5)
        assert self.equity.balance == Money(-90.5)

    def test_jump_between_tx_entries(self):
        checking_entry = self.checking.entries[0]
        equity_entry = checking_entry.siblings[0]
        # same tx
        assert equity_entry.transaction is checking_entry.transaction
        assert not checking_entry.transaction.isSplit
        assert checking_entry.transaction.entries == [checking_entry] + checking_entry.siblings
        # different accounts
        assert equity_entry.account is self.equity
        assert checking_entry.account is self.checking

    def test_entry_balance(self):
        assert self.equity.entries[0].balance == Money(1)
        assert self.equity.entries[1].balance == Money(3)
        assert self.equity.entries[2].balance == Money(6)
        assert self.equity.entries[3].balance == Money(10)
        assert self.equity.entries[4].balance == self.equity.balance == Money(-90.5)

    def test_order_account_entries(self):
        m = Money(1000)
        debit = self.checking
        credit = self.salary
        tx3 = Transaction(date(2003,1,3), 'tx3', debit, credit, m)
        tx1 = Transaction(date(2003,1,1), 'tx1', debit, credit, m)
        tx2 = Transaction(date(2003,1,2), 'tx2', debit, credit, m)
        self.check_ordered_entries(debit)
        # change tx date and check order fo all account entries
        tx2.update(date=date.today() + timedelta(1))
        self.check_ordered_entries(debit)
        
    def test_change_entry(self):
        checking = self.checking
        cash = self.cash
        salary = self.salary
        initialCheckingBalance = checking.balance
        initialCashBalance = cash.balance
        initialSalaryBalance = salary.balance
        amount = Money(1000)
        tx = Transaction(date(2003,1,3), "J'ai �t� pay� !")
        ed = tx.addDebitEntry(checking, amount)
        ec = tx.addCreditEntry(salary, amount)
        assert ed.transaction is ec.transaction is tx
        assert checking.balance == initialCheckingBalance + amount
        assert salary.balance == initialSalaryBalance + amount
        # change entry account : get salary by cash instead of checking
        ed.update(account=cash)
        assert checking.balance == initialCheckingBalance
        assert cash.balance == initialCashBalance + amount
        assert salary.balance == initialSalaryBalance + amount
        # change entry type
        assert ed.type is MovementType.DEBIT
        ed.update(type=MovementType.CREDIT)
        assert ed.type is MovementType.CREDIT
        assert not tx.isBalanced
        ec.update(type=MovementType.DEBIT)
        assert tx.isBalanced
        assert cash.balance == initialCashBalance - amount
        assert salary.balance == initialSalaryBalance - amount
        # change entry amount via entry
        ed.update(amount=Money(2000))
        assert cash.balance == initialCashBalance - Money(2000)
        assert not tx.isBalanced
        ec.update(amount=Money(2000))
        assert salary.balance == initialSalaryBalance - Money(2000)
        assert tx.isBalanced
        # can change all entry amounts via the tx since tx is not split
        assert not tx.isSplit
        tx.update(amount=Money(1999))
        assert tx.isBalanced
        assert cash.balance == initialCashBalance - Money(1999)
        assert salary.balance == initialSalaryBalance - Money(1999)


if __name__ == '__main__':
    unittest.main()
