import sys
import datetime
import weakref

import wx
import wx.grid as gridlib

from magot.model import *
from magot.refdata import *
from magot.storage import *
from magot.guiutil import *


class MainFrame(wx.Frame):

    def __init__(self, parent, title, ctx):
        wx.Frame.__init__(self, parent, -1, title, 
                            pos=(150, 150), size=(850, 500))
        self.ctx = ctx

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append(wx.ID_OPEN, "E&dit\tAlt-E", "Edit account details")
        menu.Append(wx.ID_SAVE, "&Save\tAlt-S", "Save data")
        menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit application")
        menu.Append(1, "&Jump\tAlt-J", "Jump to account")
        
        wx.EVT_MENU(self, wx.ID_OPEN, self.OnEditAccount)
        wx.EVT_MENU(self, wx.ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnExit)
        wx.EVT_MENU(self, 1, self.OnJump)
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        menuBar.Append(menu, "&File") 
        self.SetMenuBar(menuBar) 
        self.CreateStatusBar()

        # one long transaction between each save
        storage.beginTransaction(self.ctx)
        self.accRoot = self.ctx.Accounts.root

        self.nb = MainNotebook(self, -1, self.accRoot)
    
    def OnExit(self, evt):
        self.Close()

    def OnCloseWindow(self, evt):
        # todo : save modification before commit ?
        storage.commitTransaction(self.ctx)
        self.Destroy()

    def OnEditAccount(self, evt):
        tree = self.panel.tree
        win = AccountEditor(self, tree, -1, "Account details", 
            size=wx.Size(500, 200), 
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        win.CenterOnScreen()
        
        if win.ShowModal() == wx.ID_OK:
            item = tree.GetSelection()
            account = tree.GetPyData(item)
            account.description = win.desc()
            account.name = win.name()
            tree.SetItemText(item, account.name, 0)
            tree.SetItemText(item, account.description, 1)
            if account.parent.name != win.parent():
                try:
                    newParent = self.ctx.Accounts.get(win.parent())
                except exceptions.NameNotFound:
                    return
                    
                account.parent = newParent
                self.panel.Refresh(account)

    def OnSave(self, evt):
        self.ctx.Accounts.register(self.accRoot)
        storage.commitTransaction(self.ctx)
        storage.beginTransaction(self.ctx)

    def OnJump(self, event):
        accountLedger = self.nb.GetCurrentPage()
        # todo split
        selectedEntry = accountLedger.GetSelectedEntry()
        if selectedEntry is not None:
            opposedEntry = selectedEntry.opposedEntry
            self.nb.OpenAccount(opposedEntry.account, opposedEntry)


class AccountHierarchy(wx.Panel):

    def __init__(self, parent, accRoot):
        wx.Panel.__init__(self, parent, -1)
        wx.EVT_SIZE(self, self.OnSize)

        self.accRoot = accRoot
        self.parent = parent
        self.tree = AutoWidthTreeListCtrl(self, -1, 
            style=wx.TR_DEFAULT_STYLE | wx.TR_HIDE_ROOT)

        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx = il.Add(wx.ArtProvider_GetBitmap(
            wx.ART_FOLDER, wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(
            wx.ART_FILE_OPEN, wx.ART_OTHER, isz))

        self.tree.SetImageList(il)
        self.il = il

        # create some columns
        self.tree.AddColumn("Account")
        self.tree.AddColumn("Description")
        self.tree.AddColumn("Balance")
        self.tree.SetMainColumn(0) # the one with the tree in it...
        self.tree.SetColumnWidth(0, 175)
        self.tree.SetColumnWidth(1, 300)

        self.Refresh()

        wx.EVT_LEFT_DCLICK(self.tree.GetMainWindow(), self.OnLeftDClick)


    def OnLeftDClick(self, event):
        pt = event.GetPosition();
        item, flags, col = self.tree.HitTest(pt)
        if item:
            account = self.tree.GetPyData(item)
            sys.stdout.write('OnLeftDClick: %s, Col:%s, Text: %s, name %s\n' %
                (flags, col, self.tree.GetItemText(item, col), account.name))
            self.parent.OpenAccount(account)

    def OnSize(self, evt):
        self.tree.SetSize(self.GetSize())

    def Refresh(self, focus=None):
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("The Root Item")
        self._displayLevel(self.accRoot, self.root, focus)

    def _displayLevel(self, parent, node, focus=None):
        for account in parent.subAccounts:
            child = self.tree.AppendItem(node, account.name)
            
            self.tree.SetItemText(child, account.description, 1)
            self.tree.SetItemText(child, str(account.balance.amount), 2)
            self.tree.SetItemImage(child, self.fldridx, 
                                   which=wx.TreeItemIcon_Normal)
            self.tree.SetItemImage(child, self.fldropenidx, 
                                   which=wx.TreeItemIcon_Expanded)
            self.tree.SetPyData(child, account)
            if account is focus:
                self.tree.Expand(child)
                
            self._displayLevel(account, child, focus)

    def ValidAnyModification(self):
        """ No modification to validate, so can pursue the flow. """
        return True

class AccountEditor(wx.Dialog):
    
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

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Parent :")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        parentName = tree.GetPyData(item).parent.name
        text = wx.TextCtrl(self, -1, parentName)
        self.parent = text.GetValue
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
        #  todo size=(21,21) is mandatory on windows ???
        wx.Notebook.__init__(self, parent, id, size=(21,21), style=wx.NB_LEFT)
        self.ctx = parent.ctx

        panel = AccountHierarchy(self, accRoot)
        panel.Layout()
        self.AddPage(panel, 'accounts')
        parent.panel = panel
        self.mapAccountToPage = {'root':0}

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

    def OnPageChanging(self, event):
        oldPage = self.GetPage(event.GetOldSelection())
        if not oldPage.ValidAnyModification():
            event.Veto()
        event.Skip()

    def OnPageChanged(self, event):
        if hasattr(self,'pageShouldRefresh') and self.pageShouldRefresh:
            self.GetPage(event.GetSelection()).Refresh()
        event.Skip()

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
        # todo split
        if hasattr(entry, 'oppositeAccountName'):
            return entry.oppositeAccountName
        else:
            return entry.opposedEntry.account.name
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
        entry.oppositeAccountName = value
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
            gridlib.GRID_VALUE_NUMBER,
            gridlib.GRID_VALUE_STRING,
            gridlib.GRID_VALUE_CHOICE + 
                ':checking,computer,warranty,cash,salary,loan,equity',
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

    # Get/Set values in the table.  The Python version of these
    # methods can handle any data-type, (as long as the Editor and
    # Renderer understands the type too,) not just strings as in the C++ version.
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
                # first modification on this entry, so register it in the view
                e = self.GetEntry(row)
                modifiedEntry = self.GetView().RegisterEntryForModification(e)
                # the model must now use the modified entry
                self.SetEntry(row, modifiedEntry)

            _setdata(col, self.GetView().GetModifiedEntry(), value)
        except IndexError:
            # add a new row
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
            "with focus on entry "+str(focusEntry)+"\n")
        
        if sync:
            self._syncModelAgainstAccount()
        
        if sortByCol is not None:
            self.Sort(updateView=False, byCol=sortByCol)
        
        msg = wx.grid.GridTableMessage(
            self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        self.GetView().ProcessTableMessage(msg)
        self.GetView().AutoSizeColumns()

        # todo : should really the model access the view ?
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


class AccountLedgerView(gridlib.Grid):
    """ It's a page of the notebook that displays all entries of an account. """
    
    def __init__(self, parent, account, log):
        super(AccountLedgerView, self).__init__(parent, -1)
        self.ctx = parent.ctx
        self.log = log
        self.sortByCol = 0
        
        self.CreateGrid(25, 25, gridlib.Grid.SelectRows)
        
        table = AccountLedgerModel(self, account, log)
        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done. Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)

        # todo use right format
        renderer = gridlib.GridCellDateTimeRenderer('%c', '%c')
        self.RegisterDataType(gridlib.GRID_VALUE_DATETIME,
                              renderer, DateCellEditor(log))
        self.SetRowLabelSize(0)
        self.SetMargins(0, 0)
        self.AutoSizeColumns(True)

        attr = gridlib.GridCellAttr()
        self.SetColAttr(0, attr)
        self.SetColSize(0, 100)

        attr = gridlib.GridCellAttr()
        attr.SetRenderer(gridlib.GridCellNumberRenderer())
        self.SetColAttr(1, attr)

        attr = gridlib.GridCellAttr()
        self.SetColAttr(3, attr)
        self.SetColSize(3, 100)

        attr = gridlib.GridCellAttr()
        self.SetColAttr(5, attr)

        attr = gridlib.GridCellAttr()
        attr.SetReadOnly(True)
        self.SetColAttr(7, attr)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(gridlib.EVT_GRID_SELECT_CELL, self.OnSelectCell)
        self.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.OnLabelLeftClick)
        self.Bind(gridlib.EVT_GRID_RANGE_SELECT, self.OnRangeSelect)
        
        self.Bind(gridlib.EVT_GRID_EDITOR_SHOWN, self.OnEditorShown)        
 
    def GetTable(self):
        return self.tableRef()

    def SetTable(self, object, *attributes):
        self.tableRef = weakref.ref(object)
        return gridlib.Grid.SetTable(self, object, *attributes)

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
## todo new entry
##        nextRow = self.GetGridCursorRow() + 1
##        if nextRow < self.GetTable().GetNumberRows():
##            self.SetGridCursor(nextRow, 0)
##            self.MakeCellVisible(nextRow, 0)
##        else:
##            # this would be a good place to add a new row if your app
##            # needs to do that
##            pass

    def OnSelectCell(self, evt):
        # todo : really necessary ?
        if self.IsCellEditControlEnabled():
            self.HideCellEditControl()
            self.DisableCellEditControl()
        
        if self.GetGridCursorRow() != evt.GetRow():        
            if not self.ValidAnyModification():
                return
        self.SelectRow(evt.GetRow())
        evt.Skip()
   
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

    def OnEditorShown(self, evt):
        self.log.write("OnEditorShown: (%d,%d) %s\n" %
                       (evt.GetRow(), evt.GetCol(), evt.GetPosition()))
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
        
        # transaction level modifications
        entry.transaction.update(
            date=proxy.getModifiedAttr('date'),
            nb=proxy.getModifiedAttr('number'),
            desc=proxy.getModifiedAttr('description'),
            amount=proxy.getModifiedAttr('amount'))
        # entry level modifications
        entry.update(
            isReconciled=proxy.getModifiedAttr('isReconciled'),
            type=proxy.getModifiedAttr('type'))
        # opposite entry level modifications
        account = proxy.getModifiedAttr('oppositeAccountName')
        if account:
            account = self.ctx.Accounts.get(account)
        entry.opposedEntry.update(account=account)
        
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
