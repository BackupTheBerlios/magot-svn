import sys
import wx
from wx.lib.splitter import MultiSplitterWindow

from magot.storage import *
from magot.accountHierarchy import *
from magot.accountLedger import *


class MainFrame(wx.Frame):

    def __init__(self, parent, title, ctx):
        wx.Frame.__init__(self, parent, -1, title, pos=(150, 150), size=(1000, 1000))
        self.ctx = ctx

        menuFile = wx.Menu()
        self.bindMenuItemToHandler(menuFile, "E&dit account\tAlt-E", 
            "Configure account details", self.OnConfigureAccount)
        self.bindMenuItemToHandler(menuFile, "&Save\tAlt-S", 
            "Save modified data", self.OnSave)
        self.bindMenuItemToHandler(menuFile, "&Jump to opposite account\tAlt-J",
            "Jump to the opposite account", self.OnJumpToOppositeAccount)
        self.bindMenuItemToHandler(menuFile, "&Close account ledger\tAlt-C", 
            "Close the selected account ledger", self.OnCloseAccount)
        self.bindMenuItemToHandler(menuFile, "E&xit\tAlt-X", 
            "Exit application", self.OnExit)

        menuBar = wx.MenuBar()
        menuBar.Append(menuFile, "&File")
        self.SetMenuBar(menuBar)
        
        # begin one long transaction between each save
        storage.beginTransaction(self.ctx)
        self.accRoot = self.ctx.Accounts.root
        
        self.sp = MultiSplitterPanel(self, self.accRoot)

        self.CreateStatusBar()

    def OnExit(self, evt):
        if self.isActionRefused():
            return

        self.OnSave()
        self.Close(True)
        self.Destroy()

    def OnSave(self, evt=None):
        if self.isActionRefused():
            return

        self.ctx.Accounts.register(self.accRoot)
        storage.commitTransaction(self.ctx)
        storage.beginTransaction(self.ctx)

    def OnCloseAccount(self, evt):
        if self.isActionRefused():
            return

        if self.isCurrentSelectionAnAccountLedger():
            self.nb.CloseAccount()

    def OnConfigureAccount(self, evt):
        if self.isActionRefused():
            return

        if self.isCurrentSelectionAnAccountLedger():
            account = self.nb.GetCurrentPage().account
        else:
            tree = self.nb.hierarchy.tree
            item = tree.GetSelection()
            if item is None or tree.GetRootItem() == item:
                return           
            account = tree.GetPyData(item)
            
        win = AccountEditor(self, account, -1, size=wx.Size(500, 150), 
                            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        win.CenterOnScreen()
        if win.ShowModal() == wx.ID_OK:
            account.description = win.desc()
            account.name = win.name()
            # TODO: call updateAccount on hierarchy and ledger
            tree.SetItemText(item, account.name, 0)
            tree.SetItemText(item, account.description, 1)
            if account in self.nb.mapAccountToPage:
                page = self.nb.mapAccountToPage[account]
                self.nb.SetPageText(page, account.name)

    def OnJumpToOppositeAccount(self, evt):
        if self.isActionRefused():
            return

        if self.isCurrentSelectionAnAccountLedger():
            # TODO: split
            selectedEntry = self.nb.GetCurrentPage().GetSelectedEntry()
            if selectedEntry is not None:
                oppositeEntry = selectedEntry.oppositeEntry
                # jump to the other notebook
                self.nb = self.getOtherNotebook()
                self.nb.OpenAccount(oppositeEntry.account, oppositeEntry)

    def isCurrentSelectionAnAccountLedger(self):
        return not self.nb.GetCurrentPage() is self.nb.hierarchy

    def getOtherNotebook(self):
        if self.nb is self.nb1:
            return self.nb2
        if self.nb is self.nb2:
            return self.nb1

    def isActionRefused(self):
        return self.isCurrentSelectionAnAccountLedger() and \
           not self.nb.GetCurrentPage().CheckTransactionModification()

    def bindMenuItemToHandler(self, menu, title, help, handler):
        item = menu.Append(-1, title, help)
        self.Bind(wx.EVT_MENU, handler, item)


class MultiSplitterPanel(wx.Panel):
    
    def __init__(self, parent, accRoot):
        wx.Panel.__init__(self, parent, -1)

        self.splitter = MultiSplitterWindow(self)
        self.splitter.SetOrientation(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.nb1 = parent.nb = parent.nb1 = AccountNotebook(self.splitter, accRoot, parent.ctx)
        self.splitter.AppendWindow(self.nb1, 340)
        
        self.nb2 = parent.nb2 = AccountNotebook(self.splitter, accRoot, parent.ctx)
        self.splitter.AppendWindow(self.nb2, 340)


class AccountEditor(wx.Dialog):
    """ 
    This class provides access to all the properties of an account.
    """
    
    def __init__(self, parent, account, ID, pos=wx.DefaultPosition, size=wx.DefaultSize, 
                 style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, account.name+" account details", pos, size, style)
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Name :")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        text = wx.TextCtrl(self, -1, account.name)
        self.name = text.GetValue
        box.Add(text, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Description :")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        text = wx.TextCtrl(self, -1, account.description)
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


class AccountNotebook(wx.Notebook):
    
    def __init__(self, parent, accRoot, ctx, id=-1):
        # TODO: size=(21,21) is mandatory on windows ???
        wx.Notebook.__init__(self, parent, id, size=(21,21), style=wx.NB_TOP)

        self.ctx = ctx
        self.hierarchy = AccountHierarchy(self, accRoot)
        self.hierarchy.Layout()
        self.AddPage(self.hierarchy, 'accounts')
        self.mapAccountToPage = {'root':0}

        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING, self.OnSelChanging)

    def OnSelChanging(self, evt):
        oldPage = self.GetPage(evt.GetOldSelection())
        if not oldPage.CheckTransactionModification():
            if oldPage.IsCellEditControlEnabled():
                oldPage.HideCellEditControl()
            evt.Veto()  # The button Cancel was clicked, so stop the page change
        else:
            evt.Skip()

    def OnSelChange(self, evt):
        if hasattr(self, 'pageShouldRefresh') and self.pageShouldRefresh:
            self.GetPage(evt.GetSelection()).RefreshView()
        evt.Skip()

    def OpenAccount(self, account, focusEntry=None):
        if account not in self.mapAccountToPage:
            page = AccountLedgerView(self, account, sys.stdout)
            self.AddPage(page, account.name)
            self.mapAccountToPage[account] = self.GetPageCount() - 1
    
        # don't refresh in any handler when changing page, it will be done later
        self.pageShouldRefresh = False
        self.SetSelection(self.mapAccountToPage[account])

        page = self.GetCurrentPage()
        page.RefreshView()
        self.pageShouldRefresh = True
        page.SetCursorOn(focusEntry)

    def CloseAccount(self, account=None, focusEntry=None):
        if account is None:
            account = self.GetCurrentPage().account
            
        self.DeletePage(self.GetSelection())
        # update mapAccountToPage
        removedIndex = self.mapAccountToPage[account]
        del self.mapAccountToPage[account]
        for a,i in self.mapAccountToPage.iteritems():
            if i > removedIndex:
                self.mapAccountToPage[a] = i - 1


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
