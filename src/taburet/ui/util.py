import gtk
import gobject

def idle_callback(callable, args):
    args, kwargs = args
    callable(*args, **kwargs)
    return False

def idle(callable, *args, **kwargs):
    return gobject.idle_add(idle_callback, callable, (args, kwargs))

depth = [0]
def debug(func):
    def inner(*args, **kwargs):
        print '   '*depth[0], func.__name__, args[1:], kwargs
        depth[0] += 1
        try:
            result = func(*args)
        except:
            raise
        finally:
            depth[0] -= 1

        return result

    return inner

def refresh_gui():
    while gtk.events_pending():
        gtk.main_iteration_do(block=False)

def guard(name):
    def decorator(func):
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
