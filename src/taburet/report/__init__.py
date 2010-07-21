from pyExcelerator import XFStyle as Style
from pyExcelerator import Formatting
import numbers

class Workbook(object):
    def __init__(self):
        self.sheets = []
    
    def add_sheet(self, name):
        sheet = Worksheet(name)
        self.sheets.append(sheet)

        return sheet 


class Worksheet(object):
    def __init__(self, name):
        self.name = name
        self._cells = {}
        self._rows = {}
        self._columns = {}
        self.maxrow = -1
        self.maxcolumn = -1
        
        self.rows = RowCollection(self)
        
    def __getitem__(self, key):
        r, c = key.start, key.stop
        
        if c is None:
            return self._rows.setdefault(r, Row(self, r))

        if r is None:
            return self._columns.setdefault(c, Column(self, c))
        
        return self._cells.setdefault(r, {}).setdefault(c, Cell(self, r, c))
    
    def range(self, r1, r2, c1, c2):
        return Range(self, r1, r2, c1, c2)
    
    def __iter__(self):
        for row in self._cells.values():
            for c in row.values():
                yield c    

    style = property(lambda self: StyleManager(self))

         
class Cell(object):
    def __init__(self, sheet, row, column):
        self.row = row
        self.column = column
        self.value = None
        self.style = Style()
        
        if row > sheet.maxrow:
            sheet.maxrow = row
            
        if column > sheet.maxcolumn:
            sheet.maxcolumn = column
        
    def set_borders(self, width=2):
        self.style.borders.top = width
        self.style.borders.bottom = width
        self.style.borders.left = width
        self.style.borders.right = width

        
class Range(object):
    def __init__(self, sheet, r1, r2, c1, c2):
        self.sheet = sheet
        self.r1 = r1
        self.r2 = r2
        self.c1 = c1
        self.c2 = c2

    def __iter__(self):
        for r in range(self.r1, self.r2 + 1):
            for c in range(self.c1, self.c2 + 1):
                yield self.sheet[r:c]

    def set_borders(self, inwidth=1, outwidth=2):
        for c in self:
            c.style.borders.top = outwidth if c.row == self.r1 else inwidth
            c.style.borders.bottom = outwidth if c.row == self.r2 else inwidth
            c.style.borders.left = outwidth if c.column == self.c1 else inwidth
            c.style.borders.right = outwidth if c.column == self.c2 else inwidth
    
    style = property(lambda self: StyleManager(self))


class Align(object):
    def __init__(self):
        self.horz = HorzAlign()
        self.vert = VertAlign()
        
    def apply_style(self, cell):
        self.horz.apply_style(cell)
        self.vert.apply_style(cell)


class HorzAlign(object):
    def __init__(self):
        self.align = None
        
    def apply_style(self, cell):
        if self.align != None:
            cell.style.alignment.horz = self.align
            
    def center(self):
        self.align = Formatting.Alignment.HORZ_CENTER 


class VertAlign(object):
    def __init__(self):
        self.align = None 
        
    def apply_style(self, cell):
        if self.align != None:
            cell.style.alignment.vert = self.align
            
    def center(self):
        self.align = Formatting.Alignment.VERT_CENTER


class StyleManager(object):
    def __init__(self, cells):
        self.cells = cells
        
        self.format = None
        self.align = Align()
        
    def __enter__(self):
        return self
    
    def apply_style(self, cell):
        if self.format:
            cell.style.num_format_str = self.format
         
        self.align.apply_style(cell)
            
    def __exit__(self, exc_type, exc_value, traceback):
        for cell in self.cells:
            self.apply_style(cell)
        

class Row(object):
    def __init__(self, sheet, index):
        self.sheet = sheet
        self.index = index
        self.height = None
        

class Column(object):
    def __init__(self, sheet, index):
        self.sheet = sheet
        self.index = index
        self.width = None
        
    def autofit(self, start_row=None):
        maxwidth = 0
        for cell in self.sheet:
            if cell.column != self.index: continue
            if start_row and cell.row < start_row: continue
             
            value = cell.value
            if not value:
                value = u''
            
            if not isinstance(value, unicode):
                value = str(value).decode('utf8')
        
            width = len(value)
            
            if width > maxwidth:
                maxwidth = width
                
        self.width = maxwidth * 260


class RowCollection(object):
    def __init__(self, sheet):
        self.sheet = sheet
        
    def __set_height(self, height):
        for r in range(self.sheet.maxrow + 1):
            self.sheet[r:].height = height
    
    height = property(fset=__set_height)