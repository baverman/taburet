import gtk
import gobject

def create_message_widget(message):
    widget = gtk.InfoBar()
    widget.set_message_type(gtk.MESSAGE_WARNING)

    box = gtk.HBox(False, 0)

    icon = gtk.Image()
    icon.set_from_stock(gtk.STOCK_DIALOG_WARNING, gtk.ICON_SIZE_MENU)
    box.pack_start(icon, False)

    label = gtk.Label()
    label.set_text(message)
    label.set_padding(5, 0)
    box.pack_start(label, False)

    widget.get_content_area().add(box)

    return widget

def show_message(box, message, timeout):
    box = find_box_for(box)
    widget = create_message_widget(message)
    box.pack_start(widget, False)
    widget.show_all()
    gobject.timeout_add(timeout, hide_message, widget)

def hide_message(widget):
    if widget and widget.get_parent():
        widget.get_parent().remove(widget)
        widget.destroy()

    return False

def find_box_for(widget):
    for w in widget.get_toplevel().get_children():
        if isinstance(w, gtk.VBox):
            return w

    return None