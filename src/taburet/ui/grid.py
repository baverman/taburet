import gtk
import gobject

from . import idle

class GridColumn(object):
    def __init__(self, name):
        self.name = name
        
    def create_widget(self):
        return gtk.Entry()
        
    def set_value(self, entry, row):
        entry.set_text(str(row[self.name]))


class Grid(gtk.Table):
    __gsignals__ = {
        "set-scroll-adjustments": (
            gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION, 
            gobject.TYPE_NONE, (gtk.Adjustment, gtk.Adjustment)
        ),
    }
        
    def __init__(self, *columns):
        gtk.Table.__init__(self)
        self.set_set_scroll_adjustments_signal("set-scroll-adjustments")
 
        self.connect_after('realize', self.on_after_realize)
        self.connect_after('size-allocate', self.on_after_size_allocate)
           
        self.columns = columns
        self.grid = {}

        for col, c in enumerate(self.columns):
            w = c.create_widget()
            self.grid.setdefault(0, {})[col] = w
            self.attach(w, col, col + 1, 0, 1,
                xoptions=gtk.EXPAND|gtk.SHRINK|gtk.FILL, yoptions=0)
        
        self.visible_rows_count = 1
        
    def on_after_realize(self, table):
        idle(self.fill_area_with_widgets)
        idle(self.populate, int(self._vadj.get_value()))

    def on_after_size_allocate(self, table, rect):
        idle(self.fill_area_with_widgets)
        idle(self.populate, int(self._vadj.get_value()))

    def do_set_scroll_adjustments(self, h_adjustment, v_adjustment):
        #h_adjustment.connect("value-changed", self._scroll_value_changed)
        self._hadj = h_adjustment
        
        if v_adjustment:
            v_adjustment.connect("value-changed", self.vscroll_value_changed)
            self._vadj = v_adjustment
    
    def vscroll_value_changed(self, adj):
        idle(self.populate, int(adj.get_value()))
    
    def fill_area_with_widgets(self):
        _, _, _, maxy, _ = self.window.get_geometry()

        self.visible_rows_count = 0
        
        height = 0
        row_count = len(self.grid)
        for r in range(row_count):
            height += max(w.size_request()[1] for w in self.grid[r].values())
            if r < row_count - 1:
                height += self.get_row_spacing(r)
            
            self.visible_rows_count += 1
            
            if height >= maxy:
                return
        
        while height < maxy:
            row = len(self.grid)
            for col, c in enumerate(self.columns):
                w = c.create_widget()
                self.grid.setdefault(row, {})[col] = w
                self.attach(w, col, col + 1, row, row + 1,
                    xoptions=gtk.EXPAND|gtk.SHRINK|gtk.FILL, yoptions=0)

            height += max(w.size_request()[1] for w in self.grid[row].values())
            height += self.get_row_spacing(row-1)
            self.visible_rows_count += 1
    
    def set_model(self, model):
        self.model = model
        if self.window:
            self.populate()
        else:
            self.must_populate_data = True
    
    def populate(self, from_row=0):
        if not self.model:
            return
            
        if from_row == 0:
            self._vadj.set_all(0, 0, len(self.model)+3,
                1, self.visible_rows_count, self.visible_rows_count)
        
        for row, r in enumerate(self.model[from_row:from_row + self.visible_rows_count]):
            for col, c in enumerate(self.columns):
                w = self.grid[row][col]
                c.set_value(w, r)
                w.show()
                
        row += 1
        row_count = len(self.grid)
        while row < row_count:
            for col in range(len(self.columns)):
                w = self.grid[row][col]
                w.hide()
            
            row += 1 
        
                
gobject.type_register(Grid)