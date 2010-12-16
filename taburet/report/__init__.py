from pyExcelerator import XFStyle as Style
from pyExcelerator import Formatting
import numbers

def setprop(func):
    return property(fset=func)

def group_sum(map, key, value):
    if key in map:
        map[key] += value
    else:
        map[key] = value


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
        self._merges = []
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

    def merge(self, r1, r2, c1, c2):
        self._merges.append((r1, r2, c1, c2))
        return self[r1:c1]

    def __iter__(self):
        for row in self._cells.values():
            for c in row.values():
                yield c

    @property
    def style(self):
        return StyleManager(self)


class Cell(object):
    def __init__(self, sheet, row, column):
        self.row = row
        self.column = column
        self.value = None
        self._style = Style()

        if row > sheet.maxrow:
            sheet.maxrow = row

        if column > sheet.maxcolumn:
            sheet.maxcolumn = column

    def set_borders(self, width=2):
        self._style.borders.top = width
        self._style.borders.bottom = width
        self._style.borders.left = width
        self._style.borders.right = width

    @property
    def style(self):
        return StyleManager((self,))


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
            c._style.borders.top = outwidth if c.row == self.r1 else inwidth
            c._style.borders.bottom = outwidth if c.row == self.r2 else inwidth
            c._style.borders.left = outwidth if c.column == self.c1 else inwidth
            c._style.borders.right = outwidth if c.column == self.c2 else inwidth

    @property
    def style(self):
        return StyleManager(self)


class Align(object):
    def __init__(self, manager):
        self.horz = HorzAlign(manager)
        self.vert = VertAlign(manager)

    def apply_style(self, cell):
        self.horz.apply_style(cell)
        self.vert.apply_style(cell)


class HorzAlign(object):
    def __init__(self, manager):
        self.align = None
        self.manager = manager

    def apply_style(self, cell):
        if self.align != None:
            cell._style.alignment.horz = self.align

    def center(self):
        self.align = Formatting.Alignment.HORZ_CENTER
        self.manager.check_lazy_and_apply(self)


class VertAlign(object):
    def __init__(self, manager):
        self.align = None
        self.manager = manager

    def apply_style(self, cell):
        if self.align != None:
            cell._style.alignment.vert = self.align

    def center(self):
        self.align = Formatting.Alignment.VERT_CENTER
        self.manager.check_lazy_and_apply(self)


class StyleManager(object):
    def __init__(self, cells):
        self.cells = cells
        self.lazy = False
        self._format = None
        self.align = Align(self)

    def __enter__(self):
        self.lazy = True
        return self

    def check_lazy_and_apply(self, obj):
        if self.lazy: return
        for cell in self.cells:
            obj.apply_style(cell)

    def apply_style(self, cell):
        if self._format:
            cell._style.num_format_str = self._format

        self.align.apply_style(cell)

    @setprop
    def format(self, format):
        self._format = format
        self.check_lazy_and_apply(self)

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

        self.width = maxwidth * 300


class RowCollection(object):
    def __init__(self, sheet):
        self.sheet = sheet

    @setprop
    def height(self, height):
        for r in range(self.sheet.maxrow + 1):
            self.sheet[r:].height = height