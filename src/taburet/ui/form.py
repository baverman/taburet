from . import guard, guarded_by

class BadValueException(Exception): pass

class DirtyRow(dict):
    def __init__(self, fields, on_commit=None, on_error=None):
        super(DirtyRow, self).__init__()
        self.row = None
        self.on_commit = on_commit
        self.on_error = on_error
        self.fields = fields

        for f in fields:
            f.init_widget(self)

    def set_row(self, row):
        if self.row != row:
            if not self.flush():
                return False

        self.row = row
        for f in self.fields:
            f.set_value(row)

        return True

    def flush(self):
        if self and self.row is not None:
            for f in self.fields:
                if f.name in self:
                    try:
                        f.update_row_value(self, self.row)
                    except BadValueException, e:
                        if self.on_error:
                            self.on_error(self, self.row, f, e)
                        return False

            if self.on_commit:
                self.on_commit(self, self.row)

            self.clear()

        return True

    def clear(self):
        super(DirtyRow, self).clear()
        self.row = None

    def field_changed(self, f):
        self[f.name] = f.get_dirty_value()


class Field(object):
    def __init__(self, name, widget, editable=True, default='', on_change=None):
        self.name = name
        self.widget = widget
        self.editable = editable
        self.default = default
        self.on_change = on_change

    def init_widget(self, dirty_row):
        self.widget.set_editable(self.editable)
        self.widget.props.can_focus = self.editable
        self.widget.connect_after('changed', self.on_changed, dirty_row)

    @guard('changing')
    def set_value(self, row):
        self._set_value(row)

    def _set_value(self, row):
        try:
            self.widget.set_text(str(row[self.name]))
        except KeyError:
            self.widget.set_text(self.default)

    @guard('changing')
    def set_dirty_value(self, row):
        self.widget.set_text(row[self.name])

    def update_row_value(self, dirty_row, row):
        row[self.name] = dirty_row[self.name]

    @guarded_by('changing')
    def on_changed(self, entry, dirty_row):
        dirty_row.field_changed(self)
        if self.on_change:
            self.on_change(self, dirty_row)

    def get_dirty_value(self):
        return self.widget.get_text()