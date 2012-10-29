# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""
    Created Oct 2008
    TablePlotter Class
    Copyright (C) Damien Farrell
 
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.
 
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
 
    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from Tkinter import *
import tkMessageBox
import tkFont
import math
from types import *

class ClippedText:
    def __init__(self, font, clip_str):
        self.font     = font
        self.clip_str = clip_str
        self.ch_len   = {}        
        self.len_clip_str = self.font.measure(clip_str)

    def len_ch(self, ch):
        cache_len = self.ch_len.get(ch, None)
        if cache_len == None:
            cache_len = self.font.measure(ch)
            self.ch_len[ch] = cache_len
        return cache_len

    def clipped_text(self, text, dop_str, width):
        if len(dop_str) == 0:
            len_dop_str = 0
        else:
            len_dop_str = self.font.measure(dop_str)

        if width < len_dop_str:
            return u''

        len_text = len(text)
        if len_text == 0:
            return dop_str

        text_width = self.font.measure(text) + len_dop_str
        if width >= text_width:
            return text + dop_str

        if width <= len_dop_str + self.len_clip_str:
            return dop_str

        add_str = self.clip_str + dop_str
        if len_text == 1:
            return add_str

        text_width += self.len_clip_str
        for i in range(0, len_text):
            ind = -i-1
            text_width -= self.len_ch(text[ind])
            if text_width <= width:
                return text[:ind] + add_str
        return add_str
        

class TableCanvas(Canvas):
    """A tkinter class for providing table functionality"""

    def __init__(self, parent, model, newdict=None, width=None, height=None, callback = None, **kwargs):
        Canvas.__init__(self, parent, bg='white',
                         width=width, height=height,
                         relief=GROOVE,
                         scrollregion=(0,0,300,200)                         
                         )

        self.col_positions=[]       #record current column grid positions
        self.currentrow = 0
        self.currentcol = 0
        self.startrow = self.endrow = None
        self.startcol = self.endcol = None
        self.multiplerowlist=[]
        self.multiplecollist=[]
        self.navFrame = None
        self.callback = callback
        
        self.parentframe = parent
        self.width=width
        self.height=height

        self.set_defaults()
        #set any options passed in kwargs to overwrite defaults/prefs
        for key in kwargs:
            self.__dict__[key] = kwargs[key]

        self.model = model
        if newdict != None:
            self.createfromDict(newdict)

        self.rows=self.model.get_row_count()
        self.cols=self.model.get_column_count()
        self.tablewidth=(self.cellwidth)*self.cols
        self.tablecolheader = ColumnHeader(self.parentframe, self, self.col_header_cfg)
        self.tablerowheader = RowHeader(self.parentframe, self, self.row_header_cfg)
        self.do_bindings()

    def set_defaults(self):
        self.cellwidth=120
        self.maxcellwidth=400
        self.autoresizecols = 0
        self.inset=2
        self.x_start=0
        self.y_start=1
        self.cellbackgr = '#F7F7FA'
        self.entrybackgr = 'white'
        self.rowselectedcolor = '#CCCCFF'
        self.multipleselectioncolor = '#ECD672'

        self.rowheight  = 20
        self.selectedcolor = 'yellow'
        self.grid_color = '#ABB1AD'
        self.text_color = 'black'
        self.tooltip_font_opt = ("Arial", 12, "bold")
        self.text_font_opt    = ("Arial", 11, "normal")
        self.padding = (5, 5)
        self.col_header_cfg = {
             "height"   : 20
            ,"font"     : ("Arial", 11, "normal")
            ,"bg_clr"   : "gray25"
            ,"font_clr" : "white"
            }
        self.row_header_cfg = {
             "width"    : 40
            ,"font"     : ("Arial", 11, "normal")
            ,"bg_clr"   : "gray25"
            ,"font_clr" : "white"
            }

    def getModel(self):
        """Get the current table model"""
        return self.model

    def createTableFrame(self):
        """Adds column header and scrollbars and combines them with
           the current table adding all to the master frame provided in constructor.
           Table is then redrawn."""

        fnt = self.tooltip_font_opt
        self.tooltip_font = tkFont.Font(family = fnt[0], size = fnt[1], weight = fnt[2])
        fnt = self.text_font_opt
        self.text_font = tkFont.Font(family = fnt[0], size = fnt[1], weight = fnt[2])
        self.clipped = ClippedText(self.text_font, u"..")

        #Add the table and header to the frame
        self.Yscrollbar = AutoScrollbar(self.parentframe,orient=VERTICAL,command=self.set_yviews)
        self.Yscrollbar.grid(row=1,column=2,rowspan=1,sticky='news',pady=0,ipady=0)
        self.Xscrollbar = AutoScrollbar(self.parentframe,orient=HORIZONTAL,command=self.set_xviews)
        self.Xscrollbar.grid(row=2,column=1,columnspan=1,sticky='news')
        self['xscrollcommand'] = self.Xscrollbar.set
        self['yscrollcommand'] = self.Yscrollbar.set
        self.tablecolheader['xscrollcommand']=self.Xscrollbar.set
        self.tablerowheader['yscrollcommand']=self.Yscrollbar.set
        self.parentframe.rowconfigure(1,weight=1)
        self.parentframe.columnconfigure(1,weight=1)

        self.tablecolheader.grid(row=0,column=1,rowspan=1,sticky='news',pady=0,ipady=0)
        self.tablerowheader.grid(row=1,column=0,rowspan=1,sticky='news',pady=0,ipady=0)
        self.grid(row=1,column=1,rowspan=1,sticky='news',pady=0,ipady=0)
        # if self.model.get_row_count()<500:
        #     self.adjust_colWidths()
        self.redrawTable()
        self.parentframe.bind("<Configure>", self.resizeTable)
        self.tablecolheader.xview("moveto", 0)
        self.xview("moveto", 0)

    ###############################################
    # Common
    ###############################################

    def set_xviews(self,*args):
        """Set the xview of table and col header"""
        apply(self.xview,args)
        apply(self.tablecolheader.xview,args)

    def set_yviews(self,*args):
        """Set the xview of table and row header"""
        apply(self.yview,args)
        apply(self.tablerowheader.yview,args)

    def set_colPositions(self):
        """Determine current column grid positions"""
        self.col_positions=[]
        x_pos = self.x_start
        self.col_positions.append(x_pos)
        for col in range(0, self.cols):
            x_pos += self.model.get_column(col).width
            self.col_positions.append(x_pos)
        self.tablewidth = self.col_positions[len(self.col_positions)-1]

    def getCellCoords(self, row, col):
        """Get x-y coordinates to drawing a cell in a given row/col"""        
        w = self.model.get_column(col).width
        h = self.rowheight

        x1 = self.col_positions[col]
        y1 = self.y_start + h*row
        x2 = x1 + w
        y2 = y1 + h
        return x1,y1,x2,y2

    def setSelectedRow(self, row):
        """Set currently selected row and reset multiple row list"""
        self.currentrow = row
        self.multiplerowlist = [row]

    def setSelectedCol(self, col):
        """Set currently selected column"""
        self.currentcol = col
        self.multiplecollist = [col]

    def is_valid_page_row(self, row):
        if row == None:
            return False
        return 0 <= row < self.model.get_page_row_count()

    def is_valid_col(self, col):
        if col == None:
            return False
        return 0 <= col < self.model.get_column_count()

    def get_row_clicked(self, event):
        """get row where event on canvas occurs"""
        y = int(self.canvasy(event.y))
        y_start = self.y_start
        return (y-y_start)/self.rowheight

    def get_col_clicked(self,event):
        """get col where event on canvas occurs"""
        x = int(self.canvasx(event.x))
        for ind, colpos in enumerate(self.col_positions):
            try:
                nextpos=self.col_positions[ind+1]
            except:
                nextpos=self.tablewidth
            if colpos < x <= nextpos:
                return ind
        return None

    ###############################################
    # Draw
    ###############################################

    def draw_grid(self):
        """Draw the table grid lines"""
        self.delete('gridline','text')
        rows    = self.model.get_page_row_count()
        cols    = self.cols
        h       = self.rowheight
        x_start = self.x_start
        x_stop  = self.tablewidth
        y_start = self.y_start
        y_stop  = y_start+rows*h

        for col in range(0, cols+1):
            x=self.col_positions[col]
            self.create_line(x, y_start, x, y_stop, tag='gridline',
                                 fill=self.grid_color, width=1)

        for row in range(0, rows+1):
            y=y_start+row*h
            self.create_line(x_start, y, x_stop, y, tag='gridline',
                                fill=self.grid_color, width=1)

    def draw_Text(self, row, col, celltxt, align):
        """Draw the text inside a cell area"""
        self.delete('celltext'+str(col)+'_'+str(row))
        clr = self.text_color
        x1,y1,x2,y2 = self.getCellCoords(row,col)
        h = self.rowheight
        w = x2-x1
        padding_left  = self.padding[0]
        padding_right = self.padding[1]
        allow_w = w - padding_left - padding_right

        y1 = y1 + h/2
        if align == 'right':
            anchor = E
            x1 = x1 + w - padding_right
        elif align == 'left':
            anchor = W
            x1 = x1 + padding_left
        else:
            anchor = CENTER
            x1 = x1 + padding_left + allow_w/2

        if self.callback != None:
            celltxt, clr = self.callback(row, col, celltxt, clr)

        self.create_text(x1, y1,
                         text   = self.clipped.clipped_text(celltxt, u"", allow_w),
                         fill   = clr,
                         font   = self.text_font,
                         anchor = anchor,
                         tag    = ('text','celltext'+str(col)+'_'+str(row)))

    def draw_tooltip(self, row, col):
        """Draw a tooltip showing contents of cell"""
        absrow = self.model.page_row_to_absolute_row(row)
        text   = self.model.get_value(col,absrow)
        if text == '':
            return

        x1,y1,x2,y2 = self.getCellCoords(row,col)
        w=x2-x1
        obj=self.create_text(x1+w/1.5, y2,
                                text   = text,
                                anchor = 'w',
                                font   = self.tooltip_font,
                                tag    = 'tooltip')

        box = self.bbox(obj)
        x1=box[0]-1
        y1=box[1]-1
        x2=box[2]+1
        y2=box[3]+1

        self.create_rectangle(x1+1,y1+1,x2+1,y2+1,tag='tooltip',fill='black')
        self.create_rectangle(x1,y1,x2,y2,tag='tooltip',fill='lightyellow')
        self.lift(obj)

    def drawSelectedRow(self):
        """Draw the highlight rect for the currently selected row"""
        self.delete('rowrect')
        self.delete('multiplesel')
        row = self.currentrow
        x1,y1,x2,y2 = self.getCellCoords(row,0)
        x2 = self.tablewidth
        self.create_rectangle(x1,y1,x2,y2,
                              fill    = self.rowselectedcolor,
                              outline = self.rowselectedcolor,
                              tag     = 'rowrect')
        self.lower('rowrect')

    def drawMultipleRows(self, rowlist):
        """Draw more than one row selection"""
        self.delete('rowrect')
        self.delete('multiplesel')
        for row in rowlist:
            x1,y1,x2,y2 = self.getCellCoords(row,0)
            x2=self.tablewidth
            self.create_rectangle(x1,y1,x2,y2,
                                  fill    = self.multipleselectioncolor,
                                  outline = self.rowselectedcolor,
                                  tag     = ('multiplesel','rowrect'))
        self.lower('multiplesel')

    def drawSelectedRect(self):
        """User has clicked to select a cell"""
        self.delete('currentrect')
        w=3
        x1,y1,x2,y2 = self.getCellCoords(self.currentrow, self.currentcol)
        self.create_rectangle(x1+w/2, y1+w/2, x2-w/2, y2-w/2,
                              fill    = self.selectedcolor,
                              outline = 'gray25',
                              width   = w,
                              stipple = 'gray50',
                              tag     = 'currentrect')
        self.lift('celltext'+str(self.currentcol)+'_'+str(self.currentrow))

    def drawMultipleCells(self):
        """Draw an outline box for multiple cell selection"""
        self.delete('multicellrect')
        rows = self.multiplerowlist
        cols = self.multiplecollist
        w=2
        x1,y1,a,b = self.getCellCoords(rows[0],cols[0])
        c,d,x2,y2 = self.getCellCoords(rows[len(rows)-1],cols[len(cols)-1])
        rect = self.create_rectangle(x1+w/2,y1+w/2,x2,y2,
                             outline='blue',width=w,activefill='red',activestipple='gray25',
                             tag='multicellrect')

    def clearSelected(self):
        self.delete('tooltip')
        self.delete('rowrect')
        self.delete('multiplesel')
        self.delete('multicellrect')
        self.delete('currentrect')

    def redrawTable(self):
        """Draw the table from scratch based on it's model data"""
        self.rows = self.model.get_row_count()
        self.cols = self.model.get_column_count()
        self.configure(bg=self.cellbackgr) #todo
        self.set_colPositions()

        if self.model.get_pages_count() == 1:
            try:
                self.navFrame.destroy()
                self.navFrame.forget()
            except:
                pass
        else:
            self.drawNavFrame()

        self.configure(scrollregion=(0,0, self.tablewidth+self.x_start,
                                          self.rowheight*self.model.get_page_row_count()+10
                                          ))#todo
        self.draw_grid()
        self.update_idletasks()
        self.tablecolheader.redraw()
        self.tablerowheader.redraw()

        #now draw model data in cells
        for col in range(self.cols):
            align = self.model.get_column(col).align
            for rowpos, row in enumerate(self.model.get_page_rows()):
                text = self.model.get_value(col, row)
                self.draw_Text(rowpos, col, text, align)

        self.startrow = 0
        self.endrow   = 0
        self.startcol = 0
        self.endcol   = 0
        self.setSelectedRow(0)
        self.setSelectedCol(0)
        self.clearSelected()
        self.drawSelectedRow()
        self.drawSelectedRect()
        self.tablerowheader.drawSelectedRows(0)

    ###############################################
    # Mouse and Keyboard
    ###############################################

    def do_bindings(self):
        """Bind keys and mouse clicks, this can be overriden"""
        self.bind("<Button-1>",        self.handle_left_click)
        self.bind("<Shift-Button-1>",  self.handle_left_shift_click)
        self.bind("<ButtonRelease-1>", self.handle_left_release)
        self.bind('<B1-Motion>',       self.handle_mouse_drag)
        self.bind('<Motion>',          self.handle_motion)

        self.parentframe.master.bind_all("<Up>",     self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Down>",   self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Right>",  self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Left>",   self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Prior>",  self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Next>",   self.handle_arrow_keys)
        self.parentframe.master.bind_all("<Home>",   self.handle_arrow_keys)
        self.parentframe.master.bind_all("<End>",    self.handle_arrow_keys)

        self.parentframe.master.bind_all("<MouseWheel>",
            lambda event=None: self.mouse_wheel(-math.trunc(math.copysign(1, event.delta))))
        self.parentframe.master.bind_all('<Button-4>',
            lambda event=None: self.mouse_wheel(-1))
        self.parentframe.master.bind_all('<Button-5>',
            lambda event=None: self.mouse_wheel(1))

    def handle_motion(self, event):
        """Handle mouse motion on table"""
        self.tablecolheader.delete('resizesymbol')
        self.delete('tooltip')
        rowclicked = self.get_row_clicked(event)
        colclicked = self.get_col_clicked(event)
        if not (self.is_valid_page_row(rowclicked) and self.is_valid_col(colclicked)):
            return
        self.draw_tooltip(rowclicked, colclicked)

    def handle_left_click(self, event):
        """Respond to a single press"""        
        rowclicked = self.get_row_clicked(event)
        colclicked = self.get_col_clicked(event)
        if not (self.is_valid_page_row(rowclicked) and self.is_valid_col(colclicked)):
            return

        self.startrow = rowclicked
        self.endrow   = rowclicked
        self.startcol = colclicked
        self.endcol   = colclicked
        self.setSelectedRow(rowclicked)
        self.setSelectedCol(colclicked)
        self.clearSelected()
        self.drawSelectedRow()
        self.drawSelectedRect()
        self.tablerowheader.drawSelectedRows(rowclicked)

    def handle_mouse_drag(self, event):
        """Handle mouse moved with button held down, multiple selections"""
        rowclicked = self.get_row_clicked(event)
        colclicked = self.get_col_clicked(event)
        if not (self.is_valid_page_row(rowclicked) and self.is_valid_col(colclicked)):
            return
        self.endrow = rowclicked
        self.endcol = colclicked
        #do columns
        if self.endcol < self.startcol:
            self.multiplecollist=range(self.endcol, self.startcol+1)
        else:
            self.multiplecollist=range(self.startcol, self.endcol+1)
        #draw the selected rows
        if self.endrow != self.startrow:
            if self.endrow < self.startrow:
                self.multiplerowlist=range(self.endrow, self.startrow+1)
            else:
                self.multiplerowlist=range(self.startrow, self.endrow+1)
            self.drawMultipleRows(self.multiplerowlist)
            self.tablerowheader.drawSelectedRows(self.multiplerowlist)
            #draw selected cells outline using row and col lists
            self.drawMultipleCells()
        else:
            self.multiplerowlist = []
            self.multiplerowlist.append(self.currentrow)
            if len(self.multiplecollist) >= 1:
                self.drawMultipleCells()
            self.delete('multiplesel')

    def handle_left_shift_click(self, event):
        """Handle shift click, for selecting multiple rows"""
        #Has same effect as mouse drag, so just use same method
        self.handle_mouse_drag(event)

    def handle_left_release(self,event):
        self.endrow = self.get_row_clicked(event)

    def scroll_table_by_y(self, cnt):
        row_cnt = self.model.get_page_row_count()
        h       = float(self.rowheight)
        self.currentrow = min(max(self.currentrow + cnt, 0), row_cnt-1)

        x1, y1, x2, y2 = self.getCellCoords(self.currentrow, 0)
        screen_y1 = self.canvasy(0)
        screen_y2 = screen_y1 + self.winfo_height()
        if y2 > screen_y2:
            screen_pos = screen_y1 + (y2 - screen_y2) + 5
        elif y1 < screen_y1:
            screen_pos = float(y1)
        else:
            return
        canvas_pos = float(screen_pos)/(row_cnt*h+10.0)
        self.yview('moveto', canvas_pos)
        self.tablerowheader.yview('moveto', canvas_pos)

    def scroll_table_by_x(self, cnt):
        self.currentcol = min(max(self.currentcol + cnt, 0), self.cols-1)

        x1, y1, x2, y2 = self.getCellCoords(0, self.currentcol)
        screen_x1 = self.canvasx(0)
        screen_x2 = screen_x1 + self.winfo_width()
        if x2 > screen_x2:
            screen_pos = screen_x1 + (x2 - screen_x2) + 5
        elif x1 < screen_x1:
            screen_pos = float(x1)
        else:
            return
        canvas_pos = float(screen_pos)/(self.tablewidth+self.x_start)
        self.xview('moveto', canvas_pos)
        self.tablecolheader.xview("moveto", canvas_pos)

    def handle_arrow_keys(self, event):
        """Handle arrow keys press"""

        if event.keysym == 'Up':
            self.scroll_table_by_y(-1)
        elif event.keysym == 'Down':
            self.scroll_table_by_y(1)
        elif event.keysym == 'Prior':
            self.scroll_table_by_y(-10)
        elif event.keysym == 'Next':
            self.scroll_table_by_y(10)
        elif event.keysym == 'Home':
            self.scroll_table_by_y(-self.model.get_page_row_count())
        elif event.keysym == 'End':
            self.scroll_table_by_y(self.model.get_page_row_count())
        elif event.keysym == 'Right':
            self.scroll_table_by_x(1)
        elif event.keysym == 'Left':
            self.scroll_table_by_x(-1)

        self.startrow = self.currentrow
        self.endrow   = self.currentrow
        self.startcol = self.currentcol
        self.endcol   = self.currentcol
        self.setSelectedRow(self.currentrow)
        self.setSelectedCol(self.currentcol)
        self.clearSelected()
        self.drawSelectedRow()
        self.drawSelectedRect()
        self.tablerowheader.drawSelectedRows(self.currentrow)

    def mouse_wheel(self, delta):
        """Handle mouse wheel scroll"""
        self.scroll_table_by_y(delta)
        
        self.startrow = self.currentrow
        self.endrow   = self.currentrow
        self.startcol = self.currentcol
        self.endcol   = self.currentcol
        self.setSelectedRow(self.currentrow)
        self.setSelectedCol(self.currentcol)
        self.clearSelected()
        self.drawSelectedRow()
        self.drawSelectedRect()
        self.tablerowheader.drawSelectedRows(self.currentrow)

    ###############################################
    # Navigation
    ###############################################

    def drawNavFrame(self):
        """Draw the frame for selecting pages when paging is on"""
        import Table_images
        self.navFrame = Frame(self.parentframe)
        self.navFrame.grid(row=4, column=0, columnspan=2, sticky='news', padx=1, pady=1, ipady=1)
        pagingbuttons = { 'start' : self.first_Page,
                          'prev'  : self.prev_Page,
                          'next'  : self.next_Page,
                          'end'   : self.last_Page}
        images = { 'start' : Table_images.start(),
                   'prev'  : Table_images.prev(),
                   'next'  : Table_images.next(),
                   'end'   : Table_images.end()}
        skeys=['start', 'prev', 'next', 'end']
        for i in skeys:
            b = Button(self.navFrame, text=i, command=pagingbuttons[i], relief=GROOVE, image=images[i])
            b.image = images[i]
            b.pack(side=LEFT, ipadx=1, ipady=1)
        txt = 'Страница %i из %i' % (self.model.get_current_page()+1, self.model.get_pages_count())
        Label(self.navFrame, text=txt, fg='white', bg='#3366CC',relief=SUNKEN).pack(side=LEFT,ipadx=2,ipady=2,padx=4)
        txt = '%i записей' % self.rows
        Label(self.navFrame, text=txt).pack(side=LEFT,padx=3)
        txt = 'В одну страницу'
        Button(self.navFrame,text=txt,command=self.paging_Off, bg='#99CCCC',relief=GROOVE).pack(side=LEFT,padx=3)

    def first_Page(self):
        if self.model.goto_first_page():
            self.redrawTable()

    def last_Page(self):
        if self.model.goto_last_page():
            self.redrawTable()

    def prev_Page(self):
        if self.model.goto_prev_page():
            self.redrawTable()

    def next_Page(self):
        if self.model.goto_next_page():
            self.redrawTable()

    def paging_Off(self):
        self.rows=self.model.get_row_count()
        if self.rows >= 1000:
            txt = 'Эта страница содержит более 1000 записей. Вы уверены?'
            if not tkMessageBox.askyesno("Warning", txt, parent=self.parentframe):
                return
        self.model.set_paginal(False)
        self.redrawTable()

    ###############################################    
    # Navigation
    ###############################################

    def resizeTable(self, event):
        """Respond to a resize event - redraws table"""
        if self.autoresizecols == 1 and event != None:
            self.cellwidth = (event.width - self.x_start - 24) / self.cols
            self.redrawTable()

    def sortTable(self, sortcol):
        self.model.resort(sortcol)
        self.redrawTable()
      
    def resize_Column(self, col, width):
        """Resize a column by dragging"""
        self.model.get_column(col).width = width

        self.set_colPositions()
        self.redrawTable()

class ColumnHeader(Canvas):
    """Class that takes it's size and rendering from a parent table
        and column names from the table model."""

    def __init__(self, parent, table, cfg):
        Canvas.__init__(self, parent, bg=cfg["bg_clr"], width=table.width, height=cfg["height"])
        self.table    = table
        fnt           = cfg["font"]
        self.thefont  = tkFont.Font(family=fnt[0], size=fnt[1], weight=fnt[2])
        self.clipped  = ClippedText(self.thefont, u".")
        self.model    = self.table.getModel()
        self.font_clr = cfg["font_clr"]
        self.bind("<Button-1>",        self.handle_left_click)
        self.bind("<ButtonRelease-1>", self.handle_left_release)
        self.bind("<B1-Motion>",       self.handle_mouse_drag)
        self.bind("<Motion>",          self.handle_mouse_move)

    def redraw(self):
        h = int(self["height"])
        cols=self.model.get_column_count()
        self.tablewidth=self.table.tablewidth
        self.configure(scrollregion=(0,0, self.table.tablewidth+self.table.x_start, h))
        self.delete('gridline','text')
        self.atdivider = None

        if cols == 0:
            return

        if self.model.get_sort_is_reverse():
            order_ch = u" ▼"
        else:
            order_ch = u" ▲"

        for col in range(cols):
            w=self.model.get_column(col).width
            x=self.table.col_positions[col]

            if col == self.model.get_sort_index():
                dop_str = order_ch
            else:
                dop_str = u""

            text = self.model.get_column(col).caption
            text = self.clipped.clipped_text(text, dop_str, w)

            line = self.create_line(x, 0, x, h, tag=('gridline', 'vertline'), fill='white', width=2)

            self.create_text(x+w/2,h/2,
                                text=text,
                                fill=self.font_clr,
                                font=self.thefont,
                                tag='text')

        x=self.table.col_positions[col+1]
        self.create_line(x,0, x,h, tag='gridline', fill='white', width=2)

    def handle_left_click(self,event):
        """Does cell selection when mouse is clicked on canvas"""
        self.table.delete('multicellrect')
        
        if self.atdivider == 1:
            x=int(self.canvasx(event.x))          
            self.table.setSelectedCol(self.get_col_for_resize(x))
        else:
            colclicked = self.table.get_col_clicked(event)
            self.table.setSelectedCol(colclicked)
            self.table.sortTable(colclicked)

    def handle_left_release(self,event):
        """When mouse released implement col move"""
        self.delete('resizesymbol')
        if self.atdivider == 1:
            x=int(self.canvasx(event.x))
            col = self.table.currentcol
            x1,y1,x2,y2 = self.table.getCellCoords(0,col)
            newwidth=x - x1
            if newwidth < 5:
                newwidth=5
            self.table.resize_Column(col, newwidth)
            self.table.delete('resizeline')
            self.delete('resizeline')
            self.atdivider = 0

    def handle_mouse_drag(self, event):
        """Handle column drag, will be either to resize cols"""
        x=int(self.canvasx(event.x))
        if self.atdivider == 1:
            self.table.delete('resizeline')
            self.delete('resizeline')
            self.table.create_line(x, 0, x, self.table.rowheight*self.table.rows,
                                width=2, fill='gray', tag='resizeline')
            self.create_line(x, 0, x, int(self["height"]),
                                width=2, fill='gray', tag='resizeline')

    def handle_mouse_move(self, event):
        """Handle mouse moved in header, if near divider draw resize symbol"""
        self.delete('resizesymbol')

        x = int(self.canvasx(event.x))
        if self.table.x_start < x < (self.tablewidth+self.table.cellwidth):
            col = self.get_col_for_resize(x)
            if col == None:
                self.atdivider = 0
            else:
                self.atdivider = 1
                self.draw_resize_symbol(col)

    def get_col_for_resize(self, pos_x):
        dt = 10
        for i, pos in enumerate(self.table.col_positions):
            if i > 0 and abs(pos_x-pos) <= dt:
                return i-1
        return None

    def draw_resize_symbol(self, col):
        """Draw a symbol to show that col can be resized when mouse here"""
        self.delete('resizesymbol')
        
        h=int(self["height"])
        x1,y1,x2,y2 = self.table.getCellCoords(0,col)

        self.create_polygon(x2-3,h/4, x2-10,h/2, x2-3,h*3/4, tag='resizesymbol',
            fill='white', outline='gray', width=1)
        self.create_polygon(x2+2,h/4, x2+10,h/2, x2+2,h*3/4, tag='resizesymbol',
            fill='white', outline='gray', width=1)

class RowHeader(Canvas):
    """Class that displays the row headings on the table
       takes it's size and rendering from the parent table
       This also handles row/record selection as opposed to cell
       selection"""
    def __init__(self, parent, table, cfg):
        Canvas.__init__(self, parent, bg=cfg["bg_clr"], width=cfg["width"], height=table.height)
        self.table = table
        self.x_start = 40 #todo
        self.inset = 1 #todo
        self.startrow = self.endrow = None
        self.model = self.table.getModel()
        self.bind('<Button-1>',self.handle_left_click)
        self.bind("<Control-Button-1>", self.handle_left_ctrl_click)
        self.bind('<B1-Motion>', self.handle_mouse_drag)

    def redraw(self):
        """Redraw row header"""       
        self.configure(scrollregion=(0,0, int(self["width"]),
                                          self.table.rowheight*self.table.model.get_page_row_count()+10
                                          ))

        self.delete('rowheader','text')
        self.delete('rect')

        w=1
        x_start=self.x_start
        y_start=self.table.y_start
        h = self.table.rowheight
        rowpos=0
        for row in self.table.model.get_page_rows():
            x1,y1,x2,y2 = self.table.getCellCoords(rowpos,0)
            self.create_rectangle(0,y1,x_start-w,y2,
                                      fill='gray75',
                                      outline='white',
                                      width=w,
                                      tag='rowheader')
            self.create_text(x_start/2,y1+h/2,
                                      text=row+1,
                                      fill='black',
                                      font=self.table.text_font,
                                      tag='text')
            rowpos+=1

    def handle_left_click(self, event):
        rowclicked = self.table.get_row_clicked(event)
        self.startrow = rowclicked
        maxrow = self.table.model.get_page_row_count()
        if 0 <= rowclicked < maxrow:
            self.delete('rect')
            self.table.delete('multicellrect')
            self.table.setSelectedRow(rowclicked)
            self.table.drawSelectedRow()
            self.drawSelectedRows(self.table.currentrow)

    def handle_left_ctrl_click(self, event):
        """Handle ctrl clicks - for multiple row selections"""
        rowclicked = self.table.get_row_clicked(event)
        maxrow = self.table.model.get_page_row_count()
        if 0 <= rowclicked < maxrow:
            multirowlist = self.table.multiplerowlist
            if rowclicked not in multirowlist:
                multirowlist.append(rowclicked)
            else:
                multirowlist.remove(rowclicked)
            self.table.drawMultipleRows(multirowlist)
            self.drawSelectedRows(multirowlist)

    def handle_mouse_drag(self, event):
        """Handle mouse moved with button held down, multiple selections"""
        rowclicked = self.table.get_row_clicked(event)
        if self.table.model.get_page_row_count() <= rowclicked or self.startrow > self.table.rows:
            return
        else:
            self.endrow = rowclicked
        #draw the selected rows
        if self.endrow != self.startrow:
            if self.endrow < self.startrow:
                rowlist=range(self.endrow, self.startrow+1)
            else:
                rowlist=range(self.startrow, self.endrow+1)
            self.drawSelectedRows(rowlist)
            self.table.multiplerowlist = rowlist
            self.table.drawMultipleRows(rowlist)
        else:
            self.table.multiplerowlist = []
            self.table.multiplerowlist.append(rowclicked)
            self.drawSelectedRows(rowclicked)
            self.table.drawMultipleRows(self.table.multiplerowlist)

    def drawSelectedRows(self, rows=None):
        """Draw selected rows, accepts a list or integer"""
        self.delete('rect')
        if type(rows) is not ListType:
            rowlist=[]
            rowlist.append(rows)
        else:
           rowlist = rows
        for r in rowlist:
            self.draw_rect(r, delete=0)

    def draw_rect(self, row=None, tag=None, color=None, outline=None, delete=1):
        """Draw a rect representing row selection"""
        if tag==None:
            tag='rect'
        if color==None:
            color='#0099CC'
        if outline==None:
            outline='gray25'
        if delete == 1:
            self.delete(tag)
        w=0
        i = self.inset
        x1,y1,x2,y2 = self.table.getCellCoords(row, 0)
        rect = self.create_rectangle(0+i,y1+i,self.x_start-i,y2,
                                      fill=color,
                                      outline=outline,
                                      width=w,
                                      tag=tag)
        self.lift('text')

class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"