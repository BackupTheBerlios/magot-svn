import sys
import wx
import wx.gizmos

from magot.model2 import Entry, Account


class TreeListCtrlAutoWidthMixin:
    """ A mix-in class that automatically resizes the last column to take up
        the remaining width of the wxTreeListCtrl.

        This causes the wxTreeListCtrl to automatically take up the full width 
        of the list, without either a horizontal scroll bar (unless absolutely
        necessary) or empty space to the right of the last column.

        NOTE:    This only works for report-style lists.

        WARNING: If you override the EVT_SIZE event in your wxListCtrl, make
                 sure you call event.Skip() to ensure that the mixin's
                 _OnResize method is called.

        This mix-in class was written by Erik Westra <ewestra@wave.co.nz>
    """
    def __init__(self):
        """ Standard initialiser.
        """
        self._lastColMinWidth = None

        wx.EVT_SIZE(self, self._onResize)
        wx.EVT_LIST_COL_END_DRAG(self, self.GetId(), self._onResize)

    def resizeLastColumn(self, minWidth):
        """ Resize the last column appropriately.

            If the list's columns are too wide to fit within the window, we use
            a horizontal scrollbar.  Otherwise, we expand the right-most column
            to take up the remaining free space in the list.

            This method is called automatically when the wxListCtrl is resized;
            you can also call it yourself whenever you want the last column to
            be resized appropriately (eg, when adding, removing or resizing
            columns).

            'minWidth' is the preferred minimum width for the last column.
        """
        self._lastColMinWidth = minWidth
        self._doResize()

    # =====================
    # == Private Methods ==
    # =====================

    def _onResize(self, event):
        """ Respond to the wxListCtrl being resized.

            We automatically resize the last column in the list.
        """
        wx.CallAfter(self._doResize)
        event.Skip()

    def _doResize(self):
        """ Resize the last column as appropriate.

            If the list's columns are too wide to fit within the window, we use
            a horizontal scrollbar.  Otherwise, we expand the right-most column
            to take up the remaining free space in the list.

            We remember the current size of the last column, before resizing,
            as the preferred minimum width if we haven't previously been given
            or calculated a minimum width.  This ensure that repeated calls to
            _doResize() don't cause the last column to size itself too large.
        """
        numCols = self.GetColumnCount()
        if numCols == 0: return # Nothing to resize.

        if self._lastColMinWidth == None:
            self._lastColMinWidth = self.GetColumnWidth(numCols - 1)

        # We're showing the vertical scrollbar -> allow for scrollbar width
        # NOTE: on GTK, the scrollbar is included in the client size, but on
        # Windows it is not included
        listWidth = self.GetClientSize().width
##~         if wxPlatform != '__WXMSW__':
##~             if self.GetItemCount() > self.GetCountPerPage():
##~                 scrollWidth = wxSystemSettings_GetSystemMetric(wxSYS_VSCROLL_X)
##~                 listWidth = listWidth - scrollWidth

        totColWidth = 0 # Width of all columns except last one.
        for col in range(numCols-1):
            totColWidth = totColWidth + self.GetColumnWidth(col)

        lastColWidth = self.GetColumnWidth(numCols - 1)

        if totColWidth + self._lastColMinWidth > listWidth:
            # We haven't got the width to show the last column at its minimum
            # width -> set it to its minimum width and allow the horizontal
            # scrollbar to show.
            self.SetColumnWidth(numCols-1, self._lastColMinWidth)
            return

        # Resize the last column to take up the remaining available space.
        self.SetColumnWidth(numCols-1, listWidth - totColWidth)


class AccountTreeListCtrl(wx.gizmos.TreeListCtrl, TreeListCtrlAutoWidthMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.TR_DEFAULT_STYLE):
        wx.gizmos.TreeListCtrl.__init__(self, parent, ID, pos, size, style)
        TreeListCtrlAutoWidthMixin.__init__(self)

    def Traverse(self, func, startNode, funcStartNode=True):
        """ Apply fun' to each node in a branch, beginning with 'startNode'. """
        def TraverseAux(node, depth, func):
            nc = self.GetChildrenCount(node, 0)
            child, cookie = self.GetFirstChild(node)
            for i in xrange(nc):
                func(child, depth)
                TraverseAux(child, depth + 1, func)
                child, cookie = self.GetNextChild(node, cookie)
        if funcStartNode:
            func(startNode, 0)
        TraverseAux(startNode, 1, func)

    def ItemIsChildOf(self, item1, item2):
        """ Tests if item1 is a child of item2, using the Traverse function. """
        self.result = False
        def test_func(node, depth):
            if node == item1:
                self.result = True

        self.Traverse(test_func, item2)
        return self.result

    def SaveItemsToList(self, startnode):
        """ Generates a python object representation of the tree (or a 
            branch of it),
            composed of a list of dictionaries with the following key/values:
            label:      the text that the tree item had
            data:       the node's data, returned from GetItemPyData(node)
            children:   a list containing the node's children (one of these 
                        dictionaries for each)
        """
        global list
        list = []

        def save_func(node, depth):
            tmplist = list
            for x in range(0,depth):
                if not type(tmplist[-1]) is dict:
                    tmplist.append({})
                if not tmplist[-1].has_key('children'):
                    tmplist[-1]['children'] = []
                tmplist = tmplist[-1]['children']

            item = {}
            item['label'] = self.GetItemText(node)
            item['data'] = self.GetItemPyData(node)
            item['icon-normal'] = self.GetItemImage(node, wx.TreeItemIcon_Normal)
            item['icon-selected'] = self.GetItemImage(node, wx.TreeItemIcon_Selected)
            item['icon-expanded'] = self.GetItemImage(node, wx.TreeItemIcon_Expanded)
            item['icon-selectedexpanded'] = self.GetItemImage(node, 
                wx.TreeItemIcon_SelectedExpanded)

            tmplist.append(item)

        self.Traverse(save_func, startnode)
        return list

    def InsertItemsFromList(self, itemlist, parent, insertafter=None):
        """ Takes a list, 'itemslist', generated by SaveItemsToList, and inserts
            it in to the tree. The items are inserted as children of the
            treeitem given by 'parent', and if 'insertafter' is specified, they
            are inserted directly after that treeitem. Otherwise, they are put 
            at the end.

            Returns a list of the newly inserted treeitems, so they can be
            selected, etc.
        """
        newitems = []
        for item in itemlist:
            if insertafter:
                node = self.InsertItem(parent, insertafter, item['label'])
            else:
                node = self.AppendItem(parent, item['label'])
            self.SetPyData(node, item['data'])
            self.SetItemImage(node, item['icon-normal'], wx.TreeItemIcon_Normal)
            self.SetItemImage(node, item['icon-selected'], wx.TreeItemIcon_Selected)
            self.SetItemImage(node, item['icon-expanded'], wx.TreeItemIcon_Expanded)
            self.SetItemImage(node, item['icon-selectedexpanded'], 
                wx.TreeItemIcon_SelectedExpanded)

            newitems.append(node)
            if item.has_key('children'):
                self.InsertItemsFromList( item['children'], node )

        self.SortChildren(parent)
        return newitems


class AccountHierarchy(wx.Panel):

    def __init__(self, parent, accRoot):
        wx.Panel.__init__(self, parent, -1)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        
        self.log = sys.stdout
        self.accRoot = accRoot
        self.parent = parent
        
        self.tree = AccountTreeListCtrl(self, -1, style=wx.TR_HIDE_ROOT 
            | wx.TR_LINES_AT_ROOT
            | wx.TR_ROW_LINES
            | wx.TR_HAS_BUTTONS 
##            | wx.TR_DEFAULT_STYLE 
##            | wx.TR_FULL_ROW_HIGHLIGHT 
        )

        isz = (16,16)
        il = wx.ImageList(isz[0], isz[1])
        bitmap = wx.ArtProvider_GetBitmap
        self.fldridx = il.Add(bitmap(wx.ART_FOLDER, wx.ART_OTHER, isz))
        self.fldropenidx = il.Add(bitmap(wx.ART_FOLDER_OPEN, wx.ART_OTHER, isz))
##        self.fileidx = il.Add(bitmap(wx.ART_REPORT_VIEW, wx.ART_OTHER, isz))
        
        self.tree.SetImageList(il)
        self.il = il
        
        # source item being draged & droped
        self.dragItem = None

        # create some columns
        self.tree.AddColumn("Account")
        self.tree.AddColumn("Description")
        self.tree.AddColumn("Balance")
        self.tree.SetMainColumn(0) # the one with the tree in it...
        self.tree.SetColumnWidth(0, 175)
        self.tree.SetColumnWidth(1, 300)
        self.tree.SetColumnAlignment(2, wx.LIST_FORMAT_RIGHT)

        self.BuildHierarchy()
        
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        self.tree.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnOpenAccount)
        self.tree.Bind(wx.EVT_TREE_BEGIN_DRAG, self.OnBeginDrag)
        self.tree.Bind(wx.EVT_TREE_END_DRAG, self.OnEndDrag)

    def OnSize(self, evt):
        self.tree.SetSize(self.GetSize())

    def OnSelChanged(self, event):
        if self.dragItem is not None:
            self.tree.SetItemBackgroundColour(event.GetOldItem(), "White")
            self.lastSelectedItem = event.GetItem()
            self.tree.SetItemBackgroundColour(self.lastSelectedItem, "Green")

    def OnOpenAccount(self, evt):
        item = evt.GetItem();
        if item:
            account = self.tree.GetPyData(item)
            self.parent.OpenAccount(account)

    def OnBeginDrag(self, event):
        """ Allow drag-and-drop for any node. """
        event.Allow()
        self.dragItem = event.GetItem()

    def OnEndDrag(self, event):
        """ Do the re-organization if possible. """
        self.tree.SetItemBackgroundColour(self.lastSelectedItem, "White")

        # Make sure drag has begun.
        if self.dragItem is None:
            return
        # reset drag item
        source = self.dragItem
        self.dragItem = None

        # If we dropped somewhere that isn't on top of an item use the tree root
        if event.GetItem().IsOk():
            target = event.GetItem()
        else:
            target = self.tree.GetRootItem()

        # Prevent the user from dropping an item inside of itself
        if self.tree.ItemIsChildOf(target, source):
            self.log.write("the tree item can not be moved in to itself!\n")
            self.tree.UnselectAll()
            return

        newItems = self.MoveAccount(source, target)
        self.Refresh()
        self.tree.SelectItem(newItems[0])

    def BuildHierarchy(self, focus=None):
        self.tree.DeleteAllItems()
        self.root = self.tree.AddRoot("The Root of all Accounts")
        self.tree.SetPyData(self.root, self.accRoot)
        self.tree.SetItemImage(self.root, self.fldridx, wx.TreeItemIcon_Normal)
        self.tree.SetItemImage(self.root, self.fldropenidx, wx.TreeItemIcon_Expanded)
        
        self.displayOneLevel(self.accRoot, self.root, focus)
        self.tree.Expand(self.root)

    def displayOneLevel(self, parent, node, focus=None):
        for account in parent.subAccounts:
            Account.balance.addCallback(account, self.Refresh)            
            child = self.createAndAppendAccount(node, account)
            if focus is None:
                focus = account
            if account == focus:
                self.tree.SelectItem(child)
            self.displayOneLevel(account, child, focus)
        self.tree.SortChildren(node)

    def createAndAppendAccount(self, parent, account):
        child = self.tree.AppendItem(parent, account.name, 
                                     self.fldridx, self.fldropenidx)
        self.tree.SetPyData(child, account)
        self.tree.SetItemText(child, account.description, 1)
        self.tree.SetItemText(child, str(account.balance), 2)
        return child

    def CheckTransactionModification(self):
        """ No modification to validate, so we can safely pursue the flow. """
        return True

    def MoveAccount(self, source, target):
        movedAccount = self.tree.GetPyData(source)
        newParentAccount = self.tree.GetPyData(target)
        # save + delete the source
        save = self.tree.SaveItemsToList(source)
        # TODO: should be all sub-treeitems deleted? call DeleteChildren()?
        self.tree.Delete(source)
        newitems = self.tree.InsertItemsFromList(save, target)
        movedAccount.parent = newParentAccount
        return newitems

    def Refresh(self, source=None, event=None):
        """ Refresh the balance of each account. """
        def refreshAccount(child, depth):
            account = self.tree.GetPyData(child)
            self.tree.SetItemText(child, account.description, 1)
            self.tree.SetItemText(child, str(account.balance), 2)
        self.tree.Traverse(refreshAccount, self.tree.GetRootItem(), False)
        return True
