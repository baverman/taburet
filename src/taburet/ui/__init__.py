import gtk


class CommonApp(object):
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def gtk_widget_hide(self, widget, data=None):
        widget.hide()
        return True
        