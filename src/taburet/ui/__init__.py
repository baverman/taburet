import gtk

def debug(func):
    return func
    def inner(*args):
        print func.__name__, args[1:]
        return func(*args)
    
    return inner

def process_focus_like_access(treeview):
    path, current_column = treeview.get_cursor()
    columns = treeview.get_columns()
    for i, c in enumerate(columns):
        if c == current_column:
            break
        
    if i >= len(columns):
        return
    
    while True:
        i += 1
        if i >= len(columns):
            model = treeview.get_model()
            next_iter = model.iter_next(model.get_iter(path))
            if not next_iter:
                break
            
            path = model.get_string_from_iter(next_iter)
            i = -1
            continue
        
        next_column = columns[i]
        if next_column.get_cell_renderers()[0].props.editable:
            treeview.set_cursor(path, next_column, True)
            break

def enable_edit_for_columns(treeview, *indexes):
    columns = treeview.get_columns()
    for i in indexes:
        columns[i].get_cell_renderers()[0].props.editable = True
        
class CommonApp(object):
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def gtk_widget_hide(self, widget, data=None):
        widget.hide()
        return True
    
    
class EditableListTreeModel(gtk.GenericTreeModel):
    def __init__(self, data, columns):
        gtk.GenericTreeModel.__init__(self)
        self.data = data
        
        self.columns = []
        self.types = []
        for fmt, type in columns:
            self.types.append(type)
            self.columns.append(fmt) 

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    
    def on_get_n_columns(self):
        return 3
    
    def on_get_column_type(self, index):
        return self.types[index]
    
    def on_get_path(self, node):
        return node
    
    def on_get_iter(self, path):
        return path if self.data else None 
    
    def on_get_value(self, node, column):
        
        if not len(self.data):
            return None
        
        return self.columns[column] % self.data[node[0]]
    
    def on_iter_next(self, node):
        if self.data:
            next = node[0] + 1
            if next < len(self.data):
                return (next,)
        
        return None

    def on_iter_children(self, node):
        pass
    
    def on_iter_has_child(self, node):
        return node == None
    
    def on_iter_n_children(self, node):
        if node == None:
            return len(self.data)
        else:
            return 0
    
    def on_iter_nth_child(self, node, n):
        if node == None:
            return (n,)
        else:
            return None
    
    def on_iter_parent(self, node):
        return None  