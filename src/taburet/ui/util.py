import gtk
import gobject

def idle_callback(callable, args):
    args, kwargs = args
    callable(*args, **kwargs)
    return False

def idle(callable, *args, **kwargs):
    return gobject.idle_add(idle_callback, callable, (args, kwargs))

def debug(func):
    return func
    def inner(*args):
        print func.__name__, args[1:]
        return func(*args)
    
    return inner

def refresh_gui():
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)