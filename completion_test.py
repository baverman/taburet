import gtk
from taburet.ui.completion import make_simple_completion

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

window = gtk.Window(gtk.WINDOW_TOPLEVEL)
window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
window.set_position(gtk.WIN_POS_CENTER)
window.set_default_size(100, 100)

entry = gtk.Entry()
window.add(entry)

completion = make_simple_completion(choices)
completion.attach_to_entry(entry)

window.show_all()

window.connect('delete-event', lambda *args:gtk.main_quit())

gtk.main()