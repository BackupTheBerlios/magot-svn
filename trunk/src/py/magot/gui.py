import wx
import wx.grid as gridlib
import sys
import datetime
import weakref


from magot.model import *
from magot.refdata import *
from magot.storage import *
from magot.guiutil import *

#---------------------------------------------------------------------------
# TODO :
# double click sur un compte ==> TAB des entries
# population des entries
# catcher la sortie de ligne pour valider l'entry = creer ou modifier la tx grace au veto
# touche entree deplace le curseur vers la gauche et non vers le bas

# sortable columns
# population de la liste de comptes
# split a plusieurs entries
# mettre des defauts visibles blanc et non egal a 0
# validation des champs : entier, montant

class Frame(wx.Frame):

    def __init__(self, parent, title, ctx):
        wx.Frame.__init__(self, parent, -1, title, pos=(150, 150), size=(850, 500))
        self.ctx = ctx

        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append(wx.ID_OPEN, "E&dit\tAlt-E", "Edit account details")
        menu.Append(wx.ID_SAVE, "&Save\tAlt-S", "Save data")
        menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit application")
        menu.Append(1, "&Jump\tAlt-J", "Jump to account")
        menu.Append(2, "&Sort\tAlt-R", "Sort entries")
        
        wx.EVT_MENU(self, wx.ID_OPEN, self.OnEditAccount)
        wx.EVT_MENU(self, wx.ID_SAVE, self.OnSave)
        wx.EVT_MENU(self, wx.ID_EXIT, self.OnTimeToClose)
        wx.EVT_MENU(self, 1, self.OnJump)
        wx.EVT_MENU(self, 2, self.OnSort)

        menuBar.Append(menu, "&File") 
        self.SetMenuBar(menuBar) 
        self.CreateStatusBar()

        # one long transaction between each save
        storage.beginTransaction(self.ctx)
        self.accRoot = self.ctx.Accounts.root

        self.nb = MainNotebook(self, -1, self.accRoot)
    
    def OnTimeToClose(self, evt):
        self.Close() 

    def OnEditAccount(self, evt):
        tree = self.panel.tree
        win = AccountDetailDialog(self, tree, -1, "Account details", 
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
                self.panel.refresh(account)

    def OnSave(self, evt):
        self.ctx.Accounts.register(self.accRoot)
        storage.commitTransaction(self.ctx)
        storage.beginTransaction(self.ctx)

    def OnJump(self, event):
        page = self.nb.GetPage(self.nb.GetSelection())
        table = page.GetTable()
        key = table.rowkeys[page.GetGridCursorRow()]
        entry = table.data[key]
        self.nb.openEntry(entry.siblings[0])

    def OnSort(self, event):
        table = self.nb.GetPage(self.nb.GetSelection()).GetTable()
        table.Sort()

class AllAccountsPanel(wx.Panel):

    def __init__(self, parent, accRoot):
        wx.Panel.__init__(self, parent, -1)
        wx.EVT_SIZE(self, self.OnSize)

        self.accRoot = accRoot
        self.parent = parent
        self.tree = AutoWidthTreeListCtrl(self, -1, style=wx.TR_DEFAULT_STYLE |
            wx.TR_HIDE_ROOT)

        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        self.fldridx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(wx.ArtProvider_GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, isz))

        self.tree.SetImageList(il)
        self.il = il

        # create some columns
        self.tree.AddColumn("Account")
        self.tree.AddColumn("Description")
        self.tree.AddColumn("Balance")
        self.tree.SetMainColumn(0) # the one with the tree in it...
        self.tree.SetColumnWidth(0, 175)
        self.tree.SetColumnWidth(1, 300)

        self.refresh()

        wx.EVT_LEFT_DCLICK(self.tree.GetMainWindow(), self.OnLeftDClick)


    def OnLeftDClick(self, event):
        pt = event.GetPosition();
        item, flags, col = self.tree.HitTest(pt)
        if item:
            account = self.tree.GetPyData(item)
            sys.stdout.write('OnLeftDClick: %s, Col:%s, Text: %s, name %s\n' %
                (flags, col, self.tree.GetItemText(item, col), account.name))
            self.parent.openEntry(account.entries[0])

    def OnSize(self, evt):
        self.tree.SetSize(self.GetSize())

    def refresh(self, focus=None):
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("The Root Item")
        self._displayLevel(self.accRoot, self.root, focus)

    def _displayLevel(self, parent, node, focus=None):
        if isinstance(parent, SummaryAccount):
            for account in parent.subAccounts:
                child = self.tree.AppendItem(node, account.name)
                
                self.tree.SetItemText(child, account.description, 1)
                self.tree.SetItemText(child, str(account.balance.amount), 2)
                self.tree.SetItemImage(child, self.fldridx, which=wx.TreeItemIcon_Normal)
                self.tree.SetItemImage(child, self.fldropenidx, which=wx.TreeItemIcon_Expanded)
                self.tree.SetPyData(child, account)
                if account is focus:
                    self.tree.Expand(child)
                    
                self._displayLevel(account, child, focus)


class AccountDetailDialog(wx.Dialog):
    
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
        #  size=(21,21) is mandatory on windows
        wx.Notebook.__init__(self, parent, id, size=(21,21), style=wx.NB_LEFT)

        panel = AllAccountsPanel(self, accRoot)
        panel.Layout()
        self.AddPage(panel, 'accounts')
        parent.panel = panel
        self.mapAccountToPage = {'root':0}

        wx.EVT_NOTEBOOK_PAGE_CHANGED(self, self.GetId(), self.OnPageChanged)
        wx.EVT_NOTEBOOK_PAGE_CHANGING(self, self.GetId(), self.OnPageChanging)

    def OnPageChanged(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def OnPageChanging(self, event):
        old = event.GetOldSelection()
        new = event.GetSelection()
        sel = self.GetSelection()
        event.Skip()

    def openEntry(self, entry):
        account = entry.account
        if  account.name not in self.mapAccountToPage:
            page = AccountLedger(self, account, sys.stdout)
            self.AddPage(page, account.name)
            self.mapAccountToPage[account.name] = self.GetPageCount() - 1

        self.SetSelection(self.mapAccountToPage[account.name])
        page = self.GetPage(self.GetSelection())
        page.SetCursorOn(entry)


class EntryDataTable(gridlib.PyGridTableBase):
    
    def __init__(self, view, account, log):
        gridlib.PyGridTableBase.__init__(self)
        
        self.view = view
        self.account = account
        self.log = log
        
        self.colLabels = ['Date', 'Num', 'Description', 'Account', 'Reconciled',
                                'Debit', 'Credit', 'Balance']

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

        self.data = {}
        for entry in account.entries:
            self.data[id(entry)] = entry
        self.rowkeys=self.data.keys()


    #--------------------------------------------------
    # required methods for the wxPyGridTableBase interface

    def GetNumberRows(self):
        return len(self.rowkeys)

    def GetNumberCols(self):
        return len(self.colLabels)

    def IsEmptyCell(self, row, col):
        return False

    # Get/Set values in the table.  The Python version of these
    # methods can handle any data-type, (as long as the Editor and
    # Renderer understands the type too,) not just strings as in the C++ version.
    def GetValue(self, row, col):
        try:
            entry = self.data[self.rowkeys[row]]
        except:
            print "bad row", row
            return ''
        return self.getdata(col, entry, "")

    def getdata(self, col, entry, default=''):
        # TODO split
        if col == 0:
            return pydate2wxdate(entry.date)
        if col == 1:
            return hasattr(entry.transaction, 'number') or ''
        if col == 2:
            return entry.transaction.description
        if col == 3:
            return entry.siblings[0].account.name
        if col == 4:
            return entry.isReconciled
        if col == 5:
            if entry.type is MovementType.DEBIT:
                return entry.amount.amount
            else:
                return default
        if col == 6:
            if entry.type is MovementType.DEBIT:
                return default
            else:
                return entry.amount.amount
        if col == 7:
            return entry.balance.amount

    def SetValue(self, row, col, value):
        try:
            entry = self.data[self.rowkeys[row]]
            entry.transaction.date = wxdate2pydate(value)
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

    def Sort(self):
        bycol = 3 # opposite account
        descending = False
        ## ::TODO:: this sorting is not stable - it should include the current pos rather than key
        l=[ (self.getdata(bycol, self.data[key]), key) for key in self.rowkeys]
        l.sort()
        if descending:
            l.reverse()
        self.rowkeys=[key for val,key in l]
        msg=wx.grid.GridTableMessage(self, wx.grid.GRIDTABLE_REQUEST_VIEW_GET_VALUES)
        self.view.ProcessTableMessage(msg)


class AccountLedger(gridlib.Grid):
    """ 
    This is a page of the notebook and displays all entries for one account.
    """
    def __init__(self, parent, account, log):
        super(AccountLedger, self).__init__(parent, -1)
        # todo own renderer
        renderer = gridlib.GridCellDateTimeRenderer('%c', '%c')
        self.RegisterDataType(gridlib.GRID_VALUE_DATETIME,
                                        renderer,
                                        DateCellEditor(log))

        table = EntryDataTable(self, account, log)
        # The second parameter means that the grid is to take ownership of the
        # table and will destroy it when done. Otherwise you would need to keep
        # a reference to it and call it's Destroy method later.
        self.SetTable(table, True)

        self.SetRowLabelSize(0)
        self.SetMargins(0,0)
        self.AutoSizeColumns(False)

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

    def SetCursorOn(self, entry):
        rowkeys = self.GetTable().rowkeys
        self.SetGridCursor(rowkeys.index(id(entry)),3)

    def GetTable(self):
        return self.tableRef()

    def SetTable(self, object, *attributes):
        self.tableRef = weakref.ref(object)
        return gridlib.Grid.SetTable(self, object, *attributes)


class WxApp(wx.App):
   
    def __init__(self, ctx):
        self.ctx = ctx
        wx.App.__init__(self)
    
    def OnInit(self):
        self.frame = Frame(None, 'Magot', self.ctx)
        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True


class MagotGUI(commands.AbstractCommand):

    Accounts = binding.Make('magot.storage.AccountDM')

    def _run(self):
        wxapp = WxApp(self)
        wxapp.MainLoop()


if __name__ == '__main__':
    root = config.makeRoot()
    app = MagotGUI(root)
    app.run()
