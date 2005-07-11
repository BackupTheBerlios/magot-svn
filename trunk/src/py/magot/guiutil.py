import datetime
import string
import sys

import wx
import wx.grid as gridlib


def pydate2wxdate(date):
    assert isinstance(date, (datetime.datetime, datetime.date))
    tt = date.timetuple()
    dmy = (tt[2], tt[1]-1, tt[0])
    return wx.DateTimeFromDMY(*dmy)

def wxdate2pydate(date):
    import datetime
    assert isinstance(date, wx.DateTime)
    if date.IsValid():
        ymd = map(int, date.FormatISODate().split('-'))
        return datetime.date(*ymd)
    else:
        return None


class GridCtrlAutoWidthMixin:
    """ A mix-in class that automatically resizes the last column to take up
        the remaining width of the wxGridCtrl.

        This causes the wxGridCtrl to automatically take up the full width of
        the line, without either a horizontal scroll bar (unless absolutely
        necessary) or empty space to the right of the last column.

        WARNING: If you override the EVT_SIZE event in your wxGridCtrl, make
                 sure you call event.Skip() to ensure that the mixin's
                 _OnResize method is called.
    """
    def __init__(self):
        """ Standard initialiser.
        """
        self._resizeColMinWidth = None
        self._resizeColStyle = "LAST"
        self._resizeCol = 0

        self.Bind(wx.EVT_SIZE, self._onResize)
        self.Bind(gridlib.EVT_GRID_COL_SIZE, self._onResize, self)

    def setResizeColumn(self, col):
        """
        Specify which column that should be autosized.  Pass either
        'LAST' or the column number.  Default is 'LAST'.
        """
        if col == "LAST":
            self._resizeColStyle = "LAST"
        else:
            self._resizeColStyle = "COL"
            self._resizeCol = col

    def resizeLastColumn(self, minWidth):
        """ Resize the last column appropriately.

            If the list's columns are too wide to fit within the window, we use
            a horizontal scrollbar.  Otherwise, we expand the right-most column
            to take up the remaining free space in the list.

            This method is called automatically when the wx.ListCtrl is resized;
            you can also call it yourself whenever you want the last column to
            be resized appropriately (eg, when adding, removing or resizing
            columns).

            'minWidth' is the preferred minimum width for the last column.
        """
        self.resizeColumn(minWidth)

    def resizeColumn(self, minWidth):
        self._resizeColMinWidth = minWidth
        self._doResize()

    # =====================
    # == Private Methods ==
    # =====================

    def _onResize(self, event):
        """ Respond to the wx.ListCtrl being resized.

            We automatically resize the last column in the list.
        """
        if 'gtk2' in wx.PlatformInfo:
            self._doResize()
        else:
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
        if not self:  # avoid a PyDeadObject error
            return
        
        numCols = self.GetNumberCols()
        if numCols == 0: return # Nothing to resize.

        if(self._resizeColStyle == "LAST"):
            resizeCol = self.GetNumberCols()
        else:
            resizeCol = self._resizeCol

        if self._resizeColMinWidth == None:
            self._resizeColMinWidth = self.GetColSize(resizeCol - 1)

        # We're showing the vertical scrollbar -> allow for scrollbar width
        # NOTE: on GTK, the scrollbar is included in the client size, but on
        # Windows it is not included
        listWidth = self.GetClientSize().width
##        if wx.Platform != '__WXMSW__':
##            if self.GetItemCount() > self.GetCountPerPage():
##                scrollWidth = wx.SystemSettings_GetMetric(wx.SYS_VSCROLL_X)
##                listWidth = listWidth - scrollWidth

        totColWidth = 0 # Width of all columns except last one.
        for col in range(numCols):
            if col != (resizeCol-1):
                totColWidth = totColWidth + self.GetColSize(col)

        resizeColWidth = self.GetColSize(resizeCol - 1)

        if totColWidth + self._resizeColMinWidth > listWidth:
            # We haven't got the width to show the last column at its minimum
            # width -> set it to its minimum width and allow the horizontal
            # scrollbar to show.
            self.SetColSize(resizeCol-1, self._resizeColMinWidth)
            return

        # Resize the last column to take up the remaining available space.
        self.SetColSize(resizeCol-1, listWidth - totColWidth)


class DateCellEditor(gridlib.PyGridCellEditor):
    """
    This is a sample GridCellEditor that shows you how to make your own custom
    grid editors.  All the methods that can be overridden are show here.  The
    ones that must be overridden are marked with "*Must Override*" in the
    docstring.

    Notice that in order to call the base class version of these special
    methods we use the method name preceded by "base_".  This is because these
    methods are "virtual" in C++ so if we try to call wxGridCellEditor.Create
    for example, then when the wxPython extension module tries to call
    ptr->Create(...) then it actually calls the derived class version which
    looks up the method in this class and calls it, causing a recursion loop.
    If you don't understand any of this, don't worry, just call the "base_"
    version instead.
    """
    def __init__(self, log):
        self.log = log
        self.log.write("DateCellEditor ctor\n")
        gridlib.PyGridCellEditor.__init__(self)

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wxControl.
        *Must Override*
        """
        self.log.write("DateCellEditor: Create\n")
        self._tc = wx.DatePickerCtrl(parent, id, size=(120,-1),
                style=wx.DP_DROPDOWN | wx.DP_SHOWCENTURY)
        self.SetControl(self._tc)
        
        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        self.log.write("DateCellEditor: SetSize %s\n" % rect)
        self._tc.SetDimensions(rect.x, rect.y, rect.width+2, rect.height+2,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Show(self, show, attr):
        """
        Show or hide the edit control.  You can use the attr (if not None)
        to set colours or fonts for the control.
        """
        self.log.write("DateCellEditor: Show(self, %s, %s)\n" % (show, attr))
        self.base_Show(show, attr)

    def PaintBackground(self, rect, attr):
        """
        Draws the part of the cell not occupied by the edit control.  The
        base  class version just fills it with background colour from the
        attribute.  In this class the edit control fills the whole cell so
        don't do anything at all in order to reduce flicker.
        """
        self.log.write("DateCellEditor: PaintBackground\n")

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing.  Set the focus to the edit control.
        *Must Override*
        """
        self.log.write("DateCellEditor: BeginEdit (%d,%d)\n" % (row, col))
        self.startValue = grid.GetTable().GetValue(row, col)
        self._tc.SetValue(self.startValue)
        self._tc.SetFocus()

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        changed = False
        val = self._tc.GetValue()
        
        if val != self.startValue:
            changed = True
            grid.GetTable().SetValue(row, col, val) # update the table

        self.startValue = ''
        self.log.write("DateCellEditor: EndEdit (%d,%d) return %s\n" %
                        (row, col, changed))
        return changed

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        *Must Override*
        """
        self.log.write("DateCellEditor: Reset\n")
        self._tc.SetValue(self.startValue)

    def IsAcceptedKey(self, evt):
        """
        Return True to allow the given key to start editing: the base class
        version only checks that the event has no modifiers.  F2 is special
        and will always start the editor.
        """
        self.log.write("DateCellEditor: IsAcceptedKey: %d\n" % 
                        (evt.GetKeyCode()))

        ## Oops, there's a bug here, we'll have to do it ourself..
        ##return self.base_IsAcceptedKey(evt)

        return (not (evt.ControlDown() or evt.AltDown()) and
                evt.GetKeyCode() != wx.WXK_SHIFT)

    def StartingKey(self, evt):
        """
        If the editor is enabled by pressing keys on the grid, this will be
        called to let the editor do something about that first key if desired.
        """
        self.log.write("DateCellEditor: StartingKey %d\n" % evt.GetKeyCode())
        key = evt.GetKeyCode()
        ch = None
        if key in [wx.WXK_NUMPAD0, wx.WXK_NUMPAD1, wx.WXK_NUMPAD2, 
                      wx.WXK_NUMPAD3, wx.WXK_NUMPAD4, wx.WXK_NUMPAD5, 
                      wx.WXK_NUMPAD6, wx.WXK_NUMPAD7, wx.WXK_NUMPAD8, 
                      wx.WXK_NUMPAD9]:
            ch = ch = chr(ord('0') + key - wx.WXK_NUMPAD0)

        elif key < 256 and key >= 0 and chr(key) in string.printable:
            ch = chr(key)
            if not evt.ShiftDown():
                ch = ch.lower()

        if ch is not None and isinstance(ch, wx.DateTime):
            self._tc.SetValue(ch)
        else:
            evt.Skip()

    def StartingClick(self):
        """
        If the editor is enabled by clicking on the cell, this method will be
        called to allow the editor to simulate the click on the control if
        needed.
        """
        self.log.write("DateCellEditor: StartingClick\n")

    def Destroy(self):
        """final cleanup"""
        self.log.write("DateCellEditor: Destroy\n")
        self.base_Destroy()

    def Clone(self):
        """
        Create a new object which is the copy of this one
        *Must Override*
        """
        self.log.write("DateCellEditor: Clone\n")
        return DateCellEditor(self.log)


class DateCellRenderer(gridlib.PyGridCellRenderer):
    
    def __init__(self):
        gridlib.PyGridCellRenderer.__init__(self)

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        dc.DrawRectangleRect(rect)
        dc.SetFont(attr.GetFont())

        date = grid.GetTable().GetValue(row, col)
        text = date.FormatDate()

        if isSelected:
            color = "WHITE"
        else:
            color = "BLACK"

        x = rect.x + 1
        y = rect.y + 1
        for ch in text:
            dc.SetTextForeground(color)
            dc.DrawText(ch, x, y)
            w, h = dc.GetTextExtent(ch)
            x = x + w
            if x > rect.right - 5:
                break

    def GetBestSize(self, grid, attr, dc, row, col):
        date = grid.GetTable().GetValue(row, col)
        text = date.FormatDate()
        dc.SetFont(attr.GetFont())
        w, h = dc.GetTextExtent(text)
        return wx.Size(w, h)

    def Clone(self):
        return DateCellRenderer()


class OppositeAccountEditor(gridlib.PyGridCellEditor):
    """
    Editor for choosing the opposite account of a selected entry.
    A Choice control is used to display all paths in the account hierarchy.
    """

    def __init__(self, ctx):
        gridlib.PyGridCellEditor.__init__(self)
        self.ctx = ctx
        self.log = sys.stdout

    def Create(self, parent, id, evtHandler):
        """
        Called to create the control, which must derive from wxControl.
        """
        self._tc = wx.Choice(parent, id)
        self.SetControl(self._tc)

        if evtHandler:
            self._tc.PushEventHandler(evtHandler)

    def BeginEdit(self, row, col, grid):
        """
        Fetch the value from the table and prepare the edit control
        to begin editing. Set the focus to the edit control.
        """
        self.log.write("OppositeAccountEditor:BeginEdit (%d,%d)\n" % (row, col))

        self.oldOppositeAcc = grid.GetTable().GetValue(row, col)
        self.accPathPairs = self._getAccountPathPairs()

        self._tc.Clear()
        for acc, path in self.accPathPairs:
            self._tc.Append(path, acc)

        self.Reset()
        self._tc.SetFocus()

    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. 
        Returns true if the value has changed.
        """
        self.log.write("OppositeAccountEditor:EndEdit (%d,%d)\n" % (row, col))
        changed = False

        selectedAcc = self._tc.GetClientData(self._tc.GetSelection())

        if not selectedAcc is self.oldOppositeAcc:
            changed = True
            grid.GetTable().SetValue(row, col, selectedAcc)

        return changed

    def SetSize(self, rect):
        """
        Called to position/size the edit control within the cell rectangle.
        If you don't fill the cell (the rect) then be sure to override
        PaintBackground and do something meaningful there.
        """
        self._tc.SetDimensions(rect.x, rect.y, rect.width+4, rect.height+4,
                               wx.SIZE_ALLOW_MINUS_ONE)

    def Reset(self):
        """
        Reset the value in the control back to its starting value.
        """
        opp = self.oldOppositeAcc
        idx = (i for i,(a,p) in enumerate(self.accPathPairs) if a is opp).next()
        self._tc.SetSelection(idx)

    def Clone(self):
        """
        Create a new object which is the copy of this one
        """
        return OppositeAccountEditor(self.ctx)

    def _getAccountPathPairs(self):
        accPathPairs = []
        self._addSubAccPathPairs(self.ctx.Accounts.root, accPathPairs, [], None)
        return accPathPairs

    def _addSubAccPathPairs(self, parent, accPathPairs, heap, currentPath):
        for account in parent.subAccounts:
            heap.append(account.name)
            if currentPath is not None:
                path = currentPath + ":" + account.name
            else:
                path = account.name
            self._addSubAccPathPairs(account, accPathPairs, heap, path)
        
        if heap:
            accountName = heap.pop()
            if not parent.subAccounts:
                accPathPairs.append((parent, currentPath))
