import gtk
from taburet.ui.completion import Completion

choices = [
    'sdfasfasdfasdf',
    'ssssdgsdfgsdfg',
    'sddffsadfasdf',
    'aaaaaaaaa',
    'bbbbbbbbbbb',
    'nnnnnnnnnnnn',
    'jjjjjjjjjjjjj'
]
choices.sort()

def fill(model, key):
    added = {}
    if not key:
        return

    for c in choices:
        if c not in added and ( key == '*' or c.startswith(key) ):
            added[c] = True
            model.append((c, ))

    for c in choices:
        if c not in added and ( key == '*' or key in c ):
            model.append((c, ))

def select(model, iter):
    return model.get_value(iter, 0)

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
window.set_position(gtk.WIN_POS_CENTER)
window.set_default_size(100, 100)

entry = gtk.Entry()
window.add(entry)

model = gtk.ListStore(str)
completion = Completion(model, fill, select)
column = completion.column
cell = gtk.CellRendererText()
column.pack_start(cell)
column.set_attributes(cell, text=0)

completion.attach_to_entry(entry)

window.show_all()

window.connect('delete-event', lambda *args:gtk.main_quit())

gtk.main()