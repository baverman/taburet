from os.path import join, dirname
import functools
from datetime import datetime

import gtk
import gobject

depth = [0]
def debug(func=None):
    print_first = func is True
    def decorated(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            print '   '*depth[0], func.__name__, args[0 if print_first else 1:], kwargs
            depth[0] += 1
            try:
                result = func(*args)
            except:
                raise
            finally:
                depth[0] -= 1

            return result
        return inner

    if func is not True:
        return decorated(func)
    else:
        return decorated

def idle_callback(callable, args):
    args, kwargs = args
    callable(*args, **kwargs)
    return False

def idle(callable, *args, **kwargs):
    options = {}
    if 'priority' in kwargs:
        options['priority'] = kwargs['priority']
        del kwargs['priority']
    return gobject.idle_add(idle_callback, callable, (args, kwargs), **options)

def join_to_file_dir(filename, *args):
    return join(dirname(filename), *args)

def refresh_gui():
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)

def guard(name):
    def decorator(func):
        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            setattr(self, name, True)
            try:
                func(self, *args, **kwargs)
            except:
                raise
            finally:
                setattr(self, name, False)

        return inner

    return decorator

def guarded_by(name, result=None):
    def decorator(func):
        def inner(self, *args, **kwargs):
            if getattr(self, name, False):
                return result
            else:
                return func(self, *args, **kwargs)

        return inner

    return decorator

def create_calendar_dialog(title=None, parent=None, flags=gtk.DIALOG_MODAL,
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_APPLY, gtk.RESPONSE_APPLY),
        date=None):

    dlg = gtk.Dialog(title, parent, flags, buttons)
    cal = gtk.Calendar()
    dlg.vbox.pack_start(cal, False, False)
    cal.show()

    def set_date(date):
        cal.props.year = date.year
        cal.props.month = date.month - 1
        cal.props.day = date.day

    def get_date():
        return datetime(cal.props.year, cal.props.month + 1, cal.props.day)

    dlg.set_date = set_date
    dlg.get_date = get_date

    dlg.set_date(date or datetime.now())

    return dlg

class CommonApp(object):
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def gtk_widget_hide(self, widget, data=None):
        widget.hide()
        return True


class BuilderAware(object):
    def __init__(self, glade_file):
        self.gtk_builder = gtk.Builder()
        self.gtk_builder.add_from_file(glade_file)
        self.gtk_builder.connect_signals(self)

    def __getattr__(self, name):
        obj = self.gtk_builder.get_object(name)
        if not obj:
            raise AttributeError('Builder have no %s object' % name)

        setattr(self, name, obj)
        return obj