import sys
import datetime
import weakref

import wx
import wx.grid as gridlib

from magot.model import *
from magot.refdata import *
from magot.storage import *
from magot.guiutil import *
from magot.accountHierarchy import *


class MainFrame(wx.Frame):

    def __init__(self, parent, title, ctx):
        wx.Frame.__init__(self, parent, -1, title, 
                          pos=(150, 150), size=(850, 500))
        self.ctx = ctx

        menuFile = wx.Menu()
        self.BindMenuItemToHandler(menuFile, "E&dit\tAlt-E", 
            "Edit account details", self.OnEditAccount)
        self.BindMenuItemToHandler(menuFile, "&Save\tAlt-S", 
            "Save data", self.OnSave)
        self.BindMenuItemToHandler(menuFile, "&Jump\tAlt-J", 
            "Jump to account", self.OnJump)
        self.BindMenuItemToHandler(menuFile, "E&xit\tAlt-X", 
            "Exit application", self.OnExit)

        menuBar = wx.MenuBar()
        menuBar.Append(menuFile, "&File")
        self.SetMenuBar(menuBar)
        
        # begin one long transaction between each save
        storage.beginTransaction(self.ctx)
        self.accRoot = self.ctx.Accounts.root

        self.nb = MainNotebook(self, -1, self.accRoot)

        self.CreateStatusBar()

    def OnExit(self, evt):
        self.Close(True)
        # TODO: save modification before commit ?
        # storage.commitTransaction(self.ctx)
        self.Destroy()

    def OnEditAccount(self, evt):
        tree = self.nb.hierarchy.tree
        item = tree.GetSelection()
        if item is None or tree.GetRootItem() == item:
            return
        
        win = AccountEditor(self, tree, -1, "Account details", 
            size=wx.Size(500, 150), 
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        win.CenterOnScreen()
        
        if win.ShowModal() == wx.ID_OK:
            account = tree.GetPyData(item)
            account.description = win.desc()
            account.name = win.name()
            tree.SetItemText(item, account.name, 0)
            tree.SetItemText(item, account.description, 1)

    def OnSave(self, evt):
        self.ctx.Accounts.register(self.accRoot)
        storage.commitTransaction(self.ctx)
        storage.beginTransaction(self.ctx)

    def OnJump(self, evt):
        page = self.nb.GetCurrentPage()
        if isinstance(page, AccountLedgerView):
            # TODO: split
            selectedEntry = page.GetSelectedEntry()
            if selectedEntry is not None:
                oppositeEntry = selectedEntry.oppositeEntry
                self.nb.OpenAccount(oppositeEntry.account, oppositeEntry)

    def BindMenuItemToHandler(self, menu, title, help, handler):
        item = menu.Append(-1, title, help)
        self.Bind(wx.EVT_MENU, handler, item)


class AccountEditor(wx.Dialog):
    """ 
    This class provides access to all the properties of an account.
    """
    
    def __init__(self, parent, tree, ID, title, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, title, pos, size, style)
        
        item = tree.GetSelection()
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Name :")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        name = tree.GetItemText(item, 0)
        text = wx.TextCtrl(self, -1, name)
        self.name = text.GetValue
        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Description :")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        desc = tree.GetItemText(item, 1)
        text = wx.TextCtrl(self, -1, desc)
        self.desc = text.GetValue
        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        btn = wx.Button(self, wx.ID_OK, " OK ")
        btn.SetDefault()
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        btn = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        box.Add(btn, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        sizer.Add(box, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)


class MainNotebook(wx.Notebook):
    
    def __init__(self, parent, id, accRoot):
        # TODO: size=(21,21) is mandatory on windows ???
        wx.Notebook.__init__(self, parent, id, size=(21,21), style=wx.NB_LEFT)
        self.ctx = parent.ctx

        self.hierarchy = AccountHierarchy(self, accRoot)
        self.hierarchy.Layout()
        self.AddPage(self.hierarchy, 'accounts')
        self.mapAccountToPage = {'root':0}

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanging(self, evt):
        oldPage = self.GetPage(evt.GetOldSelection())
        if not oldPage.ValidAnyModification():
            evt.Veto()
        evt.Skip()

    def OnPageChanged(self, evt):
        if hasattr(self, 'pageShouldRefresh') and self.pageShouldRefresh:
            self.GetPage(evt.GetSelection()).Refresh()
        evt.Skip()

    def OpenAccount(self, account, focusEntry=None):
        if account.name not in self.mapAccountToPage:
            page = AccountLedgerView(self, account, sys.stdout)
            self.AddPage(page, account.name)
            self.mapAccountToPage[account.name] = self.GetPageCount() - 1
    
        # don't refresh in any handler when changing page, it will be done later
        self.pageShouldRefresh = False
        self.SetSelection(self.mapAccountToPage[account.name])

        page = self.GetCurrentPage()
        page.Refresh()
        self.pageShouldRefresh = True
        page.SetCursorOn(focusEntry)


class Proxy(object):
    """The Proxy base class."""

    def __init__(self, obj):
        """The initializer."""
        super(Proxy, self).__init__(obj)
        #Set attribute.
        self._obj = obj
        
    def __getattr__(self, attrib):
        try:
            return self.__dict__[attrib]
        except KeyError:
            return getattr(self._obj, attrib)

    def getModifiedAttr(self, key):
        return self.__dict__.get(key, None)


def _getdata(col, entry):
    if col == 0:
        return pydate2wxdate(entry.date)
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
        entry.date = wxdate2pydate(value)
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
        
        self.view = view
        self.account = account
        self.log = log
        self.colLabels = ['Date', 'Num', 'Description', 'Account', 
                          'Reconciled', 'Debit', 'Credit', 'Balance']
        self.dataTypes = [
            gridlib.GRID_VALUE_DATETIME,
            gridlib.GRID_VALUE_STRING,
            gridlib.GRID_VALUE_STRING,
            gridlib.GRID_VALUE_CHOICE,
            gridlib.GRID_VALUE_BOOL,
            gridlib.GRID_VALUE_FLOAT + ':6,2',
            gridlib.GRID_VALUE_FLOAT + ':6,2',
            gridlib.GRID_VALUE_FLOAT + ':6,2',
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
                modifiedEntry = self.GetView().RegisterEntryForModification(e)
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

    def Refresh(self, sortByCol=None, focusEntry=None, sync=True):
        if focusEntry is None:
            # try to get the current entry as focus
            focusEntry = self.GetView().GetSelectedEntry()

        self.log.write("Refresh called on ledger "+self.account.name+
            " with focus on entry "+str(focusEntry)+"\n")
        
        if sync:
            self._syncModelAgainstAccount()
        
        if sortByCol is not None:
            self.Sort(updateView=False, byCol=sortByCol)
        
        msg = wx.grid.GridTableMessage(
            self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        self.GetView().ProcessTableMessage(msg)

        # TODO: should really the model access the view ?
        # is the model a controler ?
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
            self.view.ProcessTableMessage(msg)


class AccountLedgerView(gridlib.Grid, GridCtrlAutoWidthMixin):
    """ It's a page of the notebook that displays all entries of an account. """
    
    def __init__(self, parent, account, log):
        super(AccountLedgerView, self).__init__(parent, -1)
        GridCtrlAutoWidthMixin.__init__(self)
        self.setResizeColumn(3) # description
            
        self.ctx = parent.ctx
        self.log = log
        self.sortByCol = 0 # by entry date
        
        self.CreateGrid(25, 25, gridlib.Grid.SelectRows)
        
        table = AccountLedgerModel(self, account, log)
        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done. Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)

        self.SetRowLabelSize(0)
##        self.AutoSizeColumns(True)

        attr = gridlib.GridCellAttr()
        attr.SetRenderer(DateCellRenderer())
        attr.SetEditor(DateCellEditor(log))
        self.SetColAttr(0, attr)

        attr = gridlib.GridCellAttr()
        attr.SetEditor(OppositeAccountEditor(self.ctx))
        self.SetColAttr(3, attr)

        attr = gridlib.GridCellAttr()
        attr.SetReadOnly(True)  # account balance is readonly
        self.SetColAttr(7, attr)

        self.__enableEdit = 0
        
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelLeftClick)
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
        if self.IsCellEditControlEnabled():
            self.HideCellEditControl()
            self.DisableCellEditControl()
            
        if self.GetGridCursorRow() != evt.GetRow():
            if not self.ValidAnyModification():
                return
        self.SelectRow(evt.GetRow())
        self.__enableEdit = 1
        evt.Skip()
   
    def OnKeyDown(self, evt):
        if evt.KeyCode() != wx.WXK_RETURN:
            evt.Skip()
            return

        if evt.ControlDown():   # the edit control needs this key
            evt.Skip()
            return

        self.DisableCellEditControl()

        if self.HasEntryBeenModified():
            self.PostEntry()
            self.Refresh()
## TODO: new entry
##        nextRow = self.GetGridCursorRow() + 1
##        if nextRow < self.GetTable().GetNumberRows():
##            self.SetGridCursor(nextRow, 0)
##            self.MakeCellVisible(nextRow, 0)
##        else:
##            # this would be a good place to add a new row if your app
##            # needs to do that
##            pass

    def ValidAnyModification(self):
        """ Return True if validation is OK to pursue the flow. False else. """
        if self.HasEntryBeenModified():
            dlg = wx.MessageDialog(self, 
                'Do you want to save entry modifications?',
                'Question',
                wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION | wx.STAY_ON_TOP
            )
            toBeSaved = dlg.ShowModal()
            dlg.Destroy()
            if toBeSaved == wx.ID_CANCEL:
                self.SelectRow(self.GetGridCursorRow())
                return False
            if toBeSaved == wx.ID_YES:
                self.PostEntry()
                self.Refresh(sync=True, sort=True)
            elif toBeSaved == wx.ID_NO:
                self.InitEntryForModification()
                self.Refresh(sync=True, sort=False)
        return True

    def OnLabelLeftClick(self, evt):
        self.sortByCol = evt.GetCol()
        self.Refresh(sync=False, sort=True)
        evt.Skip()
    
    def OnRangeSelect(self, evt):
        if evt.Selecting() and evt.GetBottomRow() !=  evt.GetTopRow():
            # vertical selection not allowed
            evt.Veto()
            self.SelectRow(self.GetGridCursorRow())
        evt.Skip()

    def Refresh(self, focusEntry=None, sync=True, sort=True):
        col = None
        if sort:
            col = self.sortByCol
        self.GetTable().Refresh(focusEntry=focusEntry, 
                                sync=sync, sortByCol=col)

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

    def HasEntryBeenModified(self):
        return hasattr(self, '_entryProxy')
    def InitEntryForModification(self):
        del self._entryProxy
    def RegisterEntryForModification(self, entry):
        self._entryProxy = Proxy(entry)
        return self._entryProxy
    def GetModifiedEntry(self):
        return self._entryProxy
    def PostEntry(self):
        proxy = self._entryProxy
        entry = proxy._obj
        
        # modifications on the transaction
        entry.transaction.update(
            date=proxy.getModifiedAttr('date'),
            nb=proxy.getModifiedAttr('number'),
            desc=proxy.getModifiedAttr('description'),
            amount=proxy.getModifiedAttr('amount'))
        # modifications on the entry
        entry.update(
            isReconciled=proxy.getModifiedAttr('isReconciled'),
            type=proxy.getModifiedAttr('type'))
        # modifications on the opposite entry
        entry.oppositeEntry.update(
            account=proxy.getModifiedAttr('oppositeAccount'))
        
        # get ready to register next entry modifications with a new proxy
        self.InitEntryForModification()
        
        # modifications OK, so replace in the model the proxy by the entry
        self.GetTable().SetEntry(self.GetGridCursorRow(), entry)
        return entry


class WxApp(wx.App):
   
    def __init__(self, ctx):
        self.ctx = ctx
        wx.App.__init__(self)
    
    def OnInit(self):
        wx.InitAllImageHandlers()
        self.frame = MainFrame(None, 'Magot', self.ctx)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


class MagotGUICmd(commands.AbstractCommand):

    Accounts = binding.Make('magot.storage.AccountDM')

    def _run(self):
        wxapp = WxApp(self)
        wxapp.MainLoop()


if __name__ == '__main__':
    root = config.makeRoot()
    app = MagotGUICmd(root)
    app.run()
