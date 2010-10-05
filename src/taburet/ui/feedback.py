import gtk
import gobject

def create_message_dialog(message):
    dialog = gtk.Window(gtk.WINDOW_POPUP)
    dialog.set_border_width(5)
    
    box = gtk.HBox(False, 0)
    
    icon = gtk.Image()
    icon.set_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)
    box.pack_start(icon)
    
    label = gtk.Label()
    label.set_text(message)
    label.set_padding(5, 0)
    box.pack_start(label)
    
    box.show_all()
    dialog.add(box)
    
    return dialog
    
def show_message(window, message, timeout):
    
    dialog = create_message_dialog(message)
    
    dialog.set_transient_for(window)
    
    pw, ph = window.get_size()
    px, py = window.get_position()
 
    w, h = dialog.get_size()
    
    dialog.move(px + pw - w, py + ph - h)
    dialog.present()
    
    gobject.timeout_add(timeout, hide_message, dialog)
    
def hide_message(dialog):
    dialog.destroy()
    return True