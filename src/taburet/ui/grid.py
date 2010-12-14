# -*- coding: utf-8 -*-

import time
import gtk
import gobject
import glib

from .util import idle, guard, guarded_by


class BadValueException(Exception):
    def __init__(self, message):
        super(BadValueException, self).__init__(message)


class GridColumn(object):
    def __init__(self, name, label=None, editable=True, width=None):
        self.name = name
        self.label = label
        self.editable = editable
        self.width = width

    def create_widget(self, dirty_row):
        e = gtk.Entry()

        e.set_editable(self.editable)
        e.props.can_focus = self.editable

        if self.width:
            e.set_width_chars(self.width)

        e.connect_after('changed', self.on_changed, dirty_row)

        return e

    @guard('changing')
    def set_value(self, entry, row):
        self._set_value(entry, row)

    def _set_value(self, entry, row):
        entry.set_text(str(row[self.name]))

    @guard('changing')
    def set_dirty_value(self, entry, row):
        entry.set_text(row[self.name])

    def update_row_value(self, dirty_row, row):
        row[self.name] = dirty_row[self.name]

    @guarded_by('changing')
    def on_changed(self, entry, dirty_row):
        dirty_row.widget_changed(entry, self)

    def get_dirty_value(self, entry):
        return entry.get_text()

    def get_title_widget(self):
        label = self.label or self.name
        return gtk.Label(label)


class IntGridColumn(GridColumn):
    def update_row_value(self, dirty_row, row):
        value_to_convert = dirty_row[self.name]
        try:
            value = int(value_to_convert)
        except ValueError:
            raise BadValueException('Нельзя привести "%s" к числу' % value_to_convert)

        row[self.name] = value


class FloatGridColumn(GridColumn):
    def update_row_value(self, dirty_row, row):
        value_to_convert = dirty_row[self.name]
        try:
            value = float(value_to_convert)
        except ValueError:
            raise BadValueException('Нельзя привести "%s" к числу' % value_to_convert)

        row[self.name] = value


class DirtyRow(dict):
    def __init__(self):
        super(DirtyRow, self).__init__()
        self.model_row = None

    def flush(self):
        if self and self.model_row is not None:
            for col, c in enumerate(self.grid.columns):
                if c.name in self:
                    try:
                        c.update_row_value(self, self.grid.model[self.model_row])
                    except BadValueException, e:
                        self.on_error(e)
                        self.grid.jump_to_error_widget(self.model_row, col)
                        return False

            self.clear()

        return True

    def on_error(self, e):
        print e

    def clear(self):
        super(DirtyRow, self).clear()
        self.model_row = None

    def widget_changed(self, widget, column):
        if self and self.model_row != widget.row:
            print 'Ahtung!!! Unflashed dirty row', self.model_row, widget.row

        self[column.name] = column.get_dirty_value(widget)
        self.model_row = widget.row

class Grid(gtk.Table):
    __gsignals__ = {
        "set-scroll-adjustments": (
            gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION,
            gobject.TYPE_NONE, (gtk.Adjustment, gtk.Adjustment)
        ),
    }

    def __init__(self, columns, dirty_row=None):
        gtk.Table.__init__(self)
        self.set_set_scroll_adjustments_signal("set-scroll-adjustments")

        self.connect_after('realize', self.on_after_realize)
        self.connect_after('size-allocate', self.on_after_size_allocate)
        self.connect('set-focus-child', self.on_child_focus)

        self.columns = columns
        self.grid = {}
        self.dirty_row = dirty_row or DirtyRow()
        self.dirty_row.grid = self
        self.current_row = None
        self.from_row = None
        self.to_row = None
        self.current_column = None

        self.last_resize = None
        self.resize_monitor_timer_id = None

        for col, c in enumerate(self.columns):
            self.attach(c.get_title_widget(), col, col + 1, 0, 1,
                xoptions=gtk.EXPAND|gtk.SHRINK|gtk.FILL, yoptions=0)
            w = self.create_widget(0, c)
            w.first = True
            self.grid.setdefault(0, {})[col] = w
            self.attach(w, col, col + 1, 1, 2,
                xoptions=gtk.EXPAND|gtk.SHRINK|gtk.FILL, yoptions=0)

        self.visible_rows_count = 1

    def create_widget(self, r, c):
        w = c.create_widget(self.dirty_row)
        w.first = False
        w.last = False
        w.row = None
        w.vrow = r
        w.column = c
        w.connect('focus', self.on_focus)
        return w

    def on_after_realize(self, table):
        idle(self.fill_area_with_widgets)
        idle(self.populate, int(self._vadj.get_value()))

    def on_after_size_allocate(self, table, rect):
        self.last_resize = time.time()
        if self.resize_monitor_timer_id is None:
            self.resize_monitor_timer_id = glib.timeout_add(100, self.monitor_resize)

        idle(self.fill_area_with_widgets)
        idle(self.populate, int(self._vadj.get_value()))

    def monitor_resize(self):
        if time.time() - self.last_resize > 0.5:
            self.resize_monitor_timer_id = None
            self.remove_partial_row_visibility()
            return False

        return True

    def remove_partial_row_visibility(self):
        _, _, w, maxy, _ = self.window.get_geometry()

        height = 0
        for r in range(self.visible_rows_count):
            row_height = max(w.size_request()[1] for w in self.grid[r].values())
            height += row_height
            if r < self.visible_rows_count - 1:
                height += self.get_row_spacing(r)

        self.window.resize(w, height)

    def do_set_scroll_adjustments(self, h_adjustment, v_adjustment):
        #h_adjustment.connect("value-changed", self._scroll_value_changed)
        self._hadj = h_adjustment

        if v_adjustment:
            v_adjustment.connect("value-changed", self.vscroll_value_changed)
            self._vadj = v_adjustment

    def vscroll_value_changed(self, adj):
        new_from_row = int(adj.value)
        if self.from_row != new_from_row:
            idle(self.populate, new_from_row)

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
                w = self.create_widget(row, c)
                self.grid.setdefault(row, {})[col] = w
                self.attach(w, col, col + 1, row+1, row + 2,
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

    @guard('populating')
    def populate(self, from_row=0, skip_focus=False, model_row_to_focus=None):
        if self.model is None:
            return

        self.from_row = from_row
        if from_row == 0:
            self._vadj.set_all(0, 0, len(self.model)+3,
                1, self.visible_rows_count, self.visible_rows_count)

        row = -1
        for row, r in enumerate(self.model[from_row:from_row + self.visible_rows_count]):
            for col, c in enumerate(self.columns):
                w = self.grid[row][col]
                c.set_value(w, r)
                w.show()
                w.last = False
                w.row = row + from_row

                if model_row_to_focus is not None:
                    frow, fcolumn = model_row_to_focus
                    if w.row == frow and fcolumn == col:
                        w.grab_focus()
                        self.set_cursor(w)

                if w.row == self.current_row:
                    if c.name in self.dirty_row:
                        c.set_dirty_value(w, self.dirty_row)

        if row >= 0:
            self.to_row = row + from_row
            for col, c in enumerate(self.columns):
                self.grid[row][col].last = True

        if not skip_focus and self.current_row is not None:
            child = self.get_focus_child()
            if child and child.row != self.current_row:
                if not self.dirty_row.flush():
                    return
                self.current_row = child.row

        row += 1
        row_count = len(self.grid)
        while row < row_count:
            for col in range(len(self.columns)):
                w = self.grid[row][col]
                w.hide()

            row += 1

        if self.current_row is None and self.get_focus_child():
            self.set_cursor(self.get_focus_child())

    def set_cursor(self, widget):
        self.current_row = widget.row
        self.current_column = widget.column

    def jump_to_error_widget(self, row, col):
        if self.from_row <= row <= self.to_row:
            self.current_row = row
            for r in self.grid.values():
                for c, column in enumerate(self.columns):
                    w = r[c]
                    if w.row == row and col == c:
                        idle(w.grab_focus)
                        idle(self.populate, self.from_row, True)
        else:
            if row < self.from_row:
                idle(self.populate, row, False, (row, col))
            else:
                idle(self.populate, self.from_row + row - self.to_row, False, (row, col))


    @guarded_by('populating')
    def on_focus(self, widget, direction):
        if direction == gtk.DIR_DOWN and widget.last and widget.is_focus():
            new_value = widget.row + 2 - self.visible_rows_count
            if new_value <= len(self.model) - self.visible_rows_count:
                self._vadj.value = new_value
            else:
                self.dirty_row.flush()

            return True

        if direction == gtk.DIR_UP and widget.first and widget.is_focus():
            new_value = widget.row - 1
            if new_value >= self._vadj.lower:
                self._vadj.value = new_value

            return True

        return False

    @guarded_by('populating')
    def on_child_focus(self, table, widget):
        if widget:
            if self.current_row is not None and self.current_row != widget.row:
                if not self.dirty_row.flush():
                    self.stop_emission('set-focus-child')
                    return

            self.current_row = widget.row
            self.current_column = widget.column
        else:
            self.current_row = None
            self.current_column = None

gobject.type_register(Grid)