import sys
import wx

from magot.storage import *
from magot.accountHierarchy import *
from magot.accountLedger import *


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
        self.BindMenuItemToHandler(menuFile, "&Close\tAlt-C", 
            "Close account ledger", self.OnCloseAccount)
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

    def OnCloseAccount(self, evt):
        if self.isAccountLedgerCurrentSelection():
            self.nb.CloseAccount()

    def OnEditAccount(self, evt):
        if self.isAccountLedgerCurrentSelection():
            return

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

    def OnSave(self, evt):
        self.ctx.Accounts.register(self.accRoot)
        storage.commitTransaction(self.ctx)
        storage.beginTransaction(self.ctx)

    def OnJump(self, evt):
        if self.isAccountLedgerCurrentSelection():
            # TODO: split
            selectedEntry = self.nb.GetCurrentPage().GetSelectedEntry()
            if selectedEntry is not None:
                oppositeEntry = selectedEntry.oppositeEntry
                self.nb.OpenAccount(oppositeEntry.account, oppositeEntry)

    def BindMenuItemToHandler(self, menu, title, help, handler):
        item = menu.Append(-1, title, help)
        self.Bind(wx.EVT_MENU, handler, item)

    
    def isAccountLedgerCurrentSelection(self):
        return not self.nb.GetCurrentPage() is self.nb.hierarchy

class AccountEditor(wx.Dialog):
    """ 
    This class provides access to all the properties of an account.
    """
    
    def __init__(self, parent, account, ID, pos=wx.DefaultPosition, 
                 size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self, parent, ID, account.name+" account details", 
                           pos, size, style)
        
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
            self.GetPage(evt.GetSelection()).RefreshLedger()
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
        page.RefreshLedger()
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
