import wx
import  wx.grid as gridlib
import  wx.calendar as  cal
import  wx.lib.popupctl as  pop
from wx.gizmos import TreeListCtrl


class ListCtrlAutoWidthMixin:
    """ A mix-in class that automatically resizes the last column to take up
        the remaining width of the wxListCtrl.

        This causes the wxListCtrl to automatically take up the full width of
        the list, without either a horizontal scroll bar (unless absolutely
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


class AutoWidthTreeListCtrl(TreeListCtrl, ListCtrlAutoWidthMixin):

    def __init__(self, parent, ID, pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.TR_DEFAULT_STYLE):
        TreeListCtrl.__init__(self, parent, ID, pos, size, style)
        ListCtrlAutoWidthMixin.__init__(self)


class DatePopUpControl(pop.PopupControl):
    
    def __init__(self,*_args,**_kwargs):
        
        apply(pop.PopupControl.__init__,(self,) + _args,_kwargs)

        self.win = wx.Window(self,-1,pos = (0,0),style = 0)
        self.cal = cal.CalendarCtrl(self.win,-1,pos = (0,0))

        bz = self.cal.GetBestSize()
        self.win.SetSize(bz)

        # This method is needed to set the contents that will be displayed
        # in the popup
        self.SetPopupContent(self.win)

        # Event registration for date selection
        cal.EVT_CALENDAR_DAY(self.cal, self.cal.GetId(), self.OnCalSelected)

    # Method called when a day is selected in the calendar
    def OnCalSelected(self,evt):
        self.PopDown()
        date = self.cal.GetDate()

        # Format the date that was selected for the text part of the control
        self.SetValue('%02d/%02d/%04d' % (date.GetDay(),
                                          date.GetMonth()+1,
                                          date.GetYear()))
        evt.Skip()

    # Method overridden from wxPopupControl
    # This method is called just before the popup is displayed
    # Use this method to format any controls in the popup
    def FormatContent(self):
        # I parse the value in the text part to resemble the correct date in
        # the calendar control
        txtValue = self.GetValue()
        dmy = txtValue.split('/')
        didSet = False
        if len(dmy) == 3:
            date = self.cal.GetDate()
            d = int(dmy[0])
            m = int(dmy[1]) - 1
            y = int(dmy[2])
            if d > 0 and d < 31:
                if m >= 0 and m < 12:
                    if y > 1000:
                        self.cal.SetDate(wx.DateTimeFromDMY(d,m,y))
                        didSet = True
        if not didSet:
            self.cal.SetDate(wx.DateTime_Today())


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
        self._tc = DatePopUpControl(parent, id, pos=(30,30), size=(100,22))
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

        # For this example, select the text
##~         self._tc.SetSelection(0, self._tc.GetLastPosition())


    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        self.log.write("DateCellEditor: EndEdit (%d,%d)\n" % (row, col))
        changed = False

        val = self._tc.GetValue()
        if val != self.startValue:
            changed = True
            grid.GetTable().SetValue(row, col, val) # update the table

        self.startValue = ''
        self._tc.SetValue('')
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
        self.log.write("DateCellEditor: IsAcceptedKey: %d\n" % (evt.GetKeyCode()))

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
                      wx.WXK_NUMPAD6, wx.WXK_NUMPAD7, wx.WXK_NUMPAD8, wx.WXK_NUMPAD9]:
            ch = ch = chr(ord('0') + key - wx.WXK_NUMPAD0)

        elif key < 256 and key >= 0 and chr(key) in string.printable:
            ch = chr(key)
            if not evt.ShiftDown():
                ch = ch.lower()

        if ch is not None:
            # For this example, replace the text.  Normally we would append it.
            #self._tc.AppendText(ch)
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