import weakref
import wx
import wx.grid as gridlib

from magot.guiutil import *
from magot.refdata import *


def _getdata(col, entry):
    if col == 0:
        return entry.date
    if col == 1:
        return entry.number
    if col == 2:
        return entry.description
    if col == 3:
        # TODO: split
        if hasattr(entry, 'oppositeAccount'):
            return entry.oppositeAccount
        else:
            return entry.oppositeEntry.account
    if col == 4:
        return entry.isReconciled
    if col == 5:
        if entry.type == MovementType.DEBIT:
            return entry.amount.amount
        else:
            return ZERO
    if col == 6:
        if entry.type == MovementType.CREDIT:
            return entry.amount.amount
        else:
            return ZERO
    if col == 7:
        return entry.balance.amount

def _setdata(col, entry, value=None):
    if col == 0:
        entry.date = value
    elif col == 1:
        entry.number = value
    elif col == 2:
        entry.description = value
    elif col == 3:
        entry.oppositeAccount = value
    elif col == 4:
        entry.isReconciled = value
    elif col == 5:
        entry.type = MovementType.DEBIT
        entry.amount = Money(value)
    elif col == 6:
        entry.type = MovementType.CREDIT
        entry.amount = Money(value)


class AccountLedgerModel(gridlib.PyGridTableBase):
    """ The MVC model containing all entries for an account.
        Synchronize automatically with the view to do sorting, updating, ...
    """
    
    def __init__(self, view, account, log):
        gridlib.PyGridTableBase.__init__(self)
        
        self.account = account
        self.log = log
        self.colLabels = ['Date', 'Num', 'Description', 'Opposite Account', 
                          'R', 'Debit', 'Credit', 'Balance']
        self.dataTypes = [
            gridlib.GRID_VALUE_DATETIME,
            gridlib.GRID_VALUE_STRING,
            gridlib.GRID_VALUE_STRING,
            gridlib.GRID_VALUE_CHOICE,
            gridlib.GRID_VALUE_BOOL,
            gridlib.GRID_VALUE_FLOAT + ':10,2',
            gridlib.GRID_VALUE_FLOAT + ':10,2',
            gridlib.GRID_VALUE_FLOAT + ':10,2',
        ]
        # data stores account entries so that we can sort them
        # whithout changing value-date ordered account.entries
        self.data = []

    #--------------------------------------------------
    # required methods for the wxPyGridTableBase interface

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.colLabels)

    def IsEmptyCell(self, row, col):
        return False

    # Get/Set values in the table. The Python version of these
    # methods can handle any data-type, (as long as the Editor and
    # Renderer understands the type too) not just strings as in the C++ version.
    def GetValue(self, row, col):
        try:
            entry = self.GetEntry(row)
        except:
            print "bad row", row
            return ''
        return _getdata(col, entry)

    def SetValue(self, row, col, value):
        try:
            if not self.GetView().HasEntryBeenModified():
                e = self.GetEntry(row)
                # first modification on this entry, so register it in the view
                modifiedEntry = self.GetView().PrepareEntryForModification(e)
                # display now the modified entry instead of the original
                self.SetEntry(row, modifiedEntry)

            _setdata(col, self.GetView().GetModifiedEntry(), value)
        except IndexError:
            # TODO: add a new row
            self.data.append([''] * self.GetNumberCols())
            self.SetValue(row, col, value)

            # tell the grid we've added a row
            msg = gridlib.GridTableMessage(self,            # The table
                    gridlib.GRIDTABLE_NOTIFY_ROWS_APPENDED, # what we did to it
                    1                                       # how many
                    )
            self.GetView().ProcessTableMessage(msg)

    #--------------------------------------------------
    # Some optional methods

    # Called when the grid needs to display labels
    def GetColLabelValue(self, col):
        return self.colLabels[col]

    # Called to determine the kind of editor/renderer to use by
    # default, doesn't necessarily have to be the same type used
    # natively by the editor/renderer if they know how to convert.
    def GetTypeName(self, row, col):
        return self.dataTypes[col]

    # Called to determine how the data can be fetched and stored by the
    # editor and renderer.  This allows you to enforce some type-safety
    # in the grid.
    def CanGetValueAs(self, row, col, typeName):
        colType = self.dataTypes[col].split(':')[0]
        if typeName == colType:
            return True
        else:
            return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)
    
    def GetEntry(self, row):
        if self.GetNumberRows() > 0:
            entry = self.data[row]
            return entry
        return None

    def SetEntry(self, row, entry):
        self.data[row] = entry

    def GetRow(self, entry):
        entryIndex = self.data.index(entry)
        return entryIndex

    def RefreshLedger(self, sortByCol=None, focusEntry=None, sync=True):
        if focusEntry is None:
            # try to get the current entry as focus
            focusEntry = self.GetView().GetSelectedEntry()

        msg = "Refresh called on ledger "+self.account.name
        if focusEntry is None:
            msg += " with no focus.\n"
        else:
            msg += " with focus on entry "+focusEntry.description+"\n"
        self.log.write(msg)
        
        if sync:
            self._syncModelAgainstAccount()
        
        if sortByCol is not None:
            self.Sort(updateView=False, byCol=sortByCol)
        
        msg = wx.grid.GridTableMessage(
            self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        self.GetView().ProcessTableMessage(msg)

        # TODO: should really the model access the view ? is the model a controler ?
        self.GetView().SetCursorOn(focusEntry)

    def Sort(self, byCol=0, descending=False, updateView=True):
        self.log.write("Sort() called on ledger "+self.account.name+
                       " on column "+str(byCol)+"\n")
        
        if self.GetNumberRows() < 2:
            return
        
        if byCol == 0:
            # account.entries is already sorted by date
            self.data = list(self.account.entries)
            if descending:
                self.data.reverse()
        else:
            def keyColumn(col):
                return lambda entry : _getdata(col, entry)
            self.data.sort(key=keyColumn(byCol), reverse=descending)

        if updateView:
            msg = wx.grid.GridTableMessage(
                self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
            self.GetView().ProcessTableMessage(msg)

    def _syncModelAgainstAccount(self):
        lo = self.GetNumberRows()
        # update model with a shallow copy
        self.data = list(self.account.entries)
        ln = len(self.data)
        if lo != ln:
            if ln > lo:
                msg = wx.grid.GridTableMessage(self, 
                    wx.grid.GRIDTABLE_NOTIFY_ROWS_APPENDED, ln-lo)
            elif lo > ln:
                msg = wx.grid.GridTableMessage(self, 
                    wx.grid.GRIDTABLE_NOTIFY_ROWS_DELETED, 0, lo-ln)
        else:
            msg = None
        if msg is not None:
            self.GetView().ProcessTableMessage(msg)


class AccountLedgerView(gridlib.Grid, GridCtrlAutoWidthMixin):
    """ It's a page of the notebook that displays all entries of an account. """
    
    def __init__(self, parent, account, log):
        super(AccountLedgerView, self).__init__(parent, -1)
        GridCtrlAutoWidthMixin.__init__(self)
        # TODO: not working perfectly
##        self.setResizeColumn(3) # description

        self.ctx = parent.ctx
        self.account = account
        self.log = log
        self.sortByCol = 0 # by entry date
        
        self.CreateGrid(25, 25, gridlib.Grid.SelectRows)
        
        table = AccountLedgerModel(self, account, log)
        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done. Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)

        self.SetRowLabelSize(0)
        self.SetSelectionBackground(wx.Colour(255, 250, 205)) # LemonChiffon
        self.SetSelectionForeground("Black")

        # column date
        self.SetColSize(0, 80)
        attr = gridlib.GridCellAttr()
        attr.SetRenderer(gridlib.GridCellStringRenderer())
        attr.SetEditor(DateCellEditor(log))
        self.SetColAttr(0, attr)

        # column num
        self.SetColSize(1, 50)
        # column description
        self.SetColSize(2, 300)
        
        # column opposite account
        self.SetColSize(3, 230)
        attr = gridlib.GridCellAttr()
        attr.SetEditor(OppositeAccountEditor(self.ctx))
        attr.SetAlignment(wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
        self.SetColAttr(3, attr)

        # column reconciled
        self.SetColSize(4, 30)

        # column debit
        self.SetColSize(5, 80)

        # column credit
        self.SetColSize(6, 80)

        # column account balance
        self.SetColSize(7, 80)
        attr = gridlib.GridCellAttr()
        attr.SetReadOnly(True)  # balance is readonly
        self.SetColAttr(7, attr)

        self.__enableEdit = 0
        
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.OnSort)
        self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        self.Bind(gridlib.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)

    def GetTable(self):
        return self.tableRef()

    def SetTable(self, object, *attributes):
        self.tableRef = weakref.ref(object)
        return gridlib.Grid.SetTable(self, object, *attributes)

    def OnIdle(self, evt):
        if self.__enableEdit and self.GetGridCursorCol() != 0:
            if self.CanEnableCellControl():
                self.EnableCellEditControl()
            self.__enableEdit = 0
        evt.Skip()

    def OnSelectCell(self, evt):
##        if :
##            return
        
        if self.IsCellEditControlEnabled():
            self.HideCellEditControl()
            self.DisableCellEditControl()
        
        if self.GetGridCursorRow() != evt.GetRow():
            # when changing line, check any tx modifications
            if not self.CheckTransactionModification():
                return
        self.SelectRow(evt.GetRow())
        self.__enableEdit = 1
        evt.Skip()

    def OnKeyDown(self, evt):
        if evt.KeyCode() != wx.WXK_RETURN or evt.ControlDown():
            evt.Skip()
            return

        self.DisableCellEditControl()
        self.CheckTransactionModification(askConfirmation=False)
        evt.Skip()
## TODO: new entry
##        nextRow = self.GetGridCursorRow() + 1
##        if nextRow < self.GetTable().GetNumberRows():
##            self.SetGridCursor(nextRow, 0)
##            self.MakeCellVisible(nextRow, 0)
##        else:
##            # this would be a good place to add a new row if your app
##            # needs to do that
##            pass

    def OnSort(self, evt):
        self.sortByCol = evt.GetCol()
        self.RefreshLedger(sync=False, sort=True)
##        evt.Skip()
    
    def OnRangeSelect(self, evt):
        if evt.Selecting() and evt.GetBottomRow() !=  evt.GetTopRow():
            # vertical selection not allowed
            evt.Veto()
            self.SelectRow(self.GetGridCursorRow())
        evt.Skip()

    def GetSelectedEntry(self):
        row = self.GetGridCursorRow()
        if row not in [None, -1]:
            selectedEntry = self.GetTable().GetEntry(row)
            return selectedEntry
        return None

    def SetCursorOn(self, entry):
        try:
            row = self.GetTable().GetRow(entry)
        except ValueError:
            row = 0
        self.SetGridCursor(row, 0)
        self.SelectRow(self.GetGridCursorRow())

    def RefreshLedger(self, focusEntry=None, sync=True, sort=True):
        col = None
        if sort:
            col = self.sortByCol
        self.GetTable().RefreshLedger(focusEntry=focusEntry, 
                                      sync=sync, sortByCol=col)
        for row in xrange(self.GetNumberRows()):
            for col in xrange(self.GetNumberCols()):
                if row % 2:
                    self.SetCellBackgroundColour(row, col, 
                        wx.Colour(245, 245, 245))  # "WhiteSmoke"

    def CheckTransactionModification(self, askConfirmation=True):
        """ Return True if we can can pursue the flow. False else. 
            Force Save if askConfirmation is False.
        """

        if self.HasEntryBeenModified():
            toBeSaved = wx.ID_YES 
            if askConfirmation:
                dlg = wx.MessageDialog(self, 
                    'Do you want to save entry modifications?', 'Question',
                    wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
                )
                toBeSaved = dlg.ShowModal()
                dlg.Destroy()

            if toBeSaved == wx.ID_CANCEL:
                self.SelectRow(self.GetGridCursorRow())
                return False
            if toBeSaved == wx.ID_YES:
                self.PostTransaction()
                self.RefreshLedger()
            elif toBeSaved == wx.ID_NO:
                self.ReleaseEntryForModification()
                self.RefreshLedger(sort=False)
        return True

    def HasEntryBeenModified(self):
        return hasattr(self, '_entryProxy')

    def ReleaseEntryForModification(self):
        del self._entryProxy

    def GetModifiedEntry(self):
        return self._entryProxy

    def PrepareEntryForModification(self, entry):
        self._entryProxy = entry.getProxy()
        return self._entryProxy

    def PostTransaction(self):
        """ Return the account Entry whose Transaction has been modified. """
        modified = self.GetModifiedEntry()
        original = modified.getOriginalObject()

        original.transaction.post(modified)
        
        # get ready to register next entry modifications
        self.ReleaseEntryForModification()
        
        # modifications OK, so replace in the model the proxy by the entry
        self.GetTable().SetEntry(self.GetGridCursorRow(), original)
        return original
