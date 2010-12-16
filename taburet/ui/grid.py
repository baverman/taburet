# -*- coding: utf-8 -*-

import time
import gtk
import gobject
import glib

from . import idle, guard, guarded_by, debug

class BadValueException(Exception): pass

class GridColumn(object):
    def __init__(self, name, label=None, editable=True, width=None, default=''):
        self.name = name
        self.label = label
        self.editable = editable
        self.width = width
        self.default = default

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
        try:
            entry.set_text(str(row[self.name]))
        except KeyError:
            entry.set_text(self.default)

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
    def __init__(self, grid, on_commit=None, on_error=None):
        super(DirtyRow, self).__init__()
        self.model_row = None
        self.grid = grid
        self.on_commit = on_commit
        self.on_error = on_error

    def flush(self):
        if self and self.model_row is not None:
            row_to_commit = self.grid.model[self.model_row]
            for col, c in enumerate(self.grid.columns):
                if c.name in self:
                    try:
                        c.update_row_value(self, row_to_commit)
                    except BadValueException, e:
                        if self.on_error:
                            self.on_error(self, e)
                        self.grid.jump_to_error_widget(self.model_row, col)
                        return False

            if self.on_commit:
                self.on_commit(self, row_to_commit)

            self.clear()

        return True

    def clear(self):
        super(DirtyRow, self).clear()
        self.model_row = None

    def widget_changed(self, widget, column):
        if self and self.model_row != widget.row:
            print 'Ahtung!!! Unflushed dirty row', self.model_row, widget.row

        self[column.name] = column.get_dirty_value(widget)
        self.model_row = widget.row

    def jump_to_new_row(self, col=0):
        new_row_num = self.model_row + 1
        fr = self.grid.from_row
        if new_row_num >= self.grid.from_row + self.grid.visible_rows_count:
            fr += 1
        idle(self.grid.populate, fr, False, (new_row_num, col))


class Grid(gtk.Table):
    __gsignals__ = {
        "set-scroll-adjustments": (
            gobject.SIGNAL_RUN_LAST | gobject.SIGNAL_ACTION,
            gobject.TYPE_NONE, (gtk.Adjustment, gtk.Adjustment)
        ),
    }

    def __init__(self, columns):
        gtk.Table.__init__(self)
        self.set_set_scroll_adjustments_signal("set-scroll-adjustments")

        self.connect_after('realize', self.on_after_realize)
        self.connect_after('size-allocate', self.on_after_size_allocate)
        self.connect('set-focus-child', self.on_child_focus)
        self.connect('destroy', self.on_destroy)

        self.columns = columns
        self.headers = [None] * len(columns)
        self.grid = {}
        self.dirty_row = None
        self.current_row = None
        self.from_row = None
        self.to_row = None

        self.last_resize = None
        self.resize_monitor_timer_id = None

        for col, c in enumerate(self.columns):
            h = self.headers[col] = c.get_title_widget()
            self.attach(h, col, col + 1, 0, 1,
                xoptions=gtk.EXPAND|gtk.SHRINK|gtk.FILL, yoptions=0)

        self.visible_rows_count = 0

    def on_destroy(self, grid):
        if hasattr(self, '_vscroll_handler_id'):
            self._vadj.handler_disconnect(self._vscroll_handler_id)

    def create_widget(self, r, c):
        w = c.create_widget(self.dirty_row)
        w.first = False
        w.last = False
        w.row = None
        w.vrow = r
        w.column = c
        w.connect('focus', self.on_focus)
        w.connect('activate', self.on_activate)
        return w

    def on_after_realize(self, table):
        idle(self.fill_area_with_widgets)
        if hasattr(self, '_vadj'):
            idle(self.populate, int(round(self._vadj.get_value())))

    def on_after_size_allocate(self, table, rect):
        self.last_resize = time.time()
        if self.resize_monitor_timer_id is None:
            self.resize_monitor_timer_id = glib.timeout_add(100, self.monitor_resize)

        idle(self.fill_area_with_widgets)
        idle(self.populate, int(round(self._vadj.get_value())))

    def monitor_resize(self):
        if time.time() - self.last_resize > 0.5:
            self.resize_monitor_timer_id = None
            self.remove_partial_row_visibility()
            return False

        return True

    def get_header_height(self):
        result = max(h.size_request()[1] for h in self.headers)
        return result

    def remove_partial_row_visibility(self):
        _, _, w, maxy, _ = self.window.get_geometry()

        height = self.get_header_height()
        for r in range(self.visible_rows_count):
            height += self.get_row_spacing(r)
            row_height = max(w.size_request()[1] for w in self.grid[r].values())
            height += row_height

        self.window.resize(w, height)

    def do_set_scroll_adjustments(self, h_adjustment, v_adjustment):
        #h_adjustment.connect("value-changed", self._scroll_value_changed)
        self._hadj = h_adjustment

        if v_adjustment:
            self._vscroll_handler_id = v_adjustment.connect(
                "value-changed", self.vscroll_value_changed)
            self._vadj = v_adjustment

    @guarded_by('populating')
    def vscroll_value_changed(self, adj):
        new_from_row = int(round(adj.value))
        if self.from_row != new_from_row:
            idle(self.populate, new_from_row)

    def set_cursor(self, row, col):
        need_scroll, w, from_row = self.get_jump_info(row, col)
        if need_scroll:
            idle(self.populate, from_row, False, (row, col))
        else:
            w.grab_focus()

    def fill_area_with_widgets(self):
        _, _, _, maxy, _ = self.window.get_geometry()

        self.visible_rows_count = 0

        height = self.get_header_height()
        row_count = len(self.grid)
        for r in range(row_count):
            height += max(w.size_request()[1] for w in self.grid[r].values())
            if r < row_count - 1:
                height += self.get_row_spacing(r + 1)

            self.visible_rows_count += 1

            if height >= maxy:
                return

        while height < maxy:
            row = len(self.grid)
            for col, c in enumerate(self.columns):
                w = self.create_widget(row, c)
                if row == 0:
                    w.first = True
                self.grid.setdefault(row, {})[col] = w
                self.attach(w, col, col + 1, row+1, row + 2,
                    xoptions=gtk.EXPAND|gtk.SHRINK|gtk.FILL, yoptions=0)

            height += max(w.size_request()[1] for w in self.grid[row].values())
            height += self.get_row_spacing(row)
            self.visible_rows_count += 1

    def set_model(self, model, dirty_row):
        self.model = model
        self.dirty_row = dirty_row
        if self.window:
            self.populate()
        else:
            self.must_populate_data = True

    @guard('populating')
    def populate(self, from_row=0, skip_focus=False, model_row_to_focus=None):
        if self.model is None:
            return

        self.from_row = from_row
        if self._vadj.page_size != self.visible_rows_count or self._vadj.upper != len(self.model):
            self._vadj.set_all(from_row, 0, len(self.model),
                1, self.visible_rows_count, self.visible_rows_count)

        if int(round(self._vadj.value)) != from_row:
            self._vadj.value = from_row

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
                        self.current_row = w.row

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
            self.current_row = self.get_focus_child().row

    def get_jump_info(self, row, col):
        if self.from_row <= row <= self.to_row:
            for r in self.grid.values():
                for c, column in enumerate(self.columns):
                    w = r[c]
                    if w.row == row and col == c:
                        return False, w, self.from_row
        else:
            if row < self.from_row:
                return True, None, row
            else:
                return True, None, self.from_row + row - self.to_row

        raise Exception("Can't get widget for (%d, %d)" % (row, col))

    def jump_to_error_widget(self, row, col):
        need_scroll, w, from_row = self.get_jump_info(row, col)
        if need_scroll:
            idle(self.populate, from_row, False, (row, col))
        else:
            self.current_row = row
            idle(w.grab_focus)
            idle(self.populate, from_row, True)

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
        else:
            self.current_row = None

    def on_activate(self, widget):
        if widget.column is self.columns[-1]:
            self.child_focus(gtk.DIR_DOWN)
        else:
            self.child_focus(gtk.DIR_RIGHT)

gobject.type_register(Grid)