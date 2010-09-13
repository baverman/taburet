import gtk, gobject

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
                process_row_change(treeview, True)
                break
            
            path = model.get_string_from_iter(next_iter)
            i = -1
            continue
        
        next_column = columns[i]
        if next_column.get_cell_renderers()[0].props.editable:
            treeview.set_cursor(path, next_column, True)
            break

def process_edit_done(treeview, new_text):
    path, column = treeview.get_cursor()

    model = treeview.get_model()
    
    if not model.dirty_row_path:
        model.dirty_row_path = path
        model.dirty_data.clear()
    
    model.dirty_data[column.get_name()] = new_text
    
def process_row_change(treeview, force=False):
    path, _ = treeview.get_cursor()
    model = treeview.get_model()
    
    if model.dirty_row_path and ( force or model.dirty_row_path != path ):
        row = model.get_row_from_path(model.dirty_row_path)
        
        data = {}
        for k, v in model.dirty_data.iteritems():
            data[k] = getattr(model.rowmodel, k).from_string(v)
            
        model.rowmodel.row_changed(model, row, data)
        
        model.dirty_row_path = None

def init_editable_treeview(treeview, model):
    treeview.set_model(model)
    
    if getattr(treeview, 'edit_init_done', False):
        model.column_order = treeview.column_order
        return
    
    def treeview_edit_done(renderer, path, new_text):
        process_edit_done(treeview, new_text)
        return process_focus_like_access(treeview)
    
    def treeview_cursor_changed(treeview):
        return process_row_change(treeview)

    treeview.column_order = []
    for idx, c in enumerate(treeview.get_columns()):
        cname = c.get_name()
        renderer = c.get_cell_renderers()[0]
        rm = getattr(model.rowmodel, cname)
        for k, v in rm.get_properties().iteritems(): 
            renderer.set_property(k, v)
        
        renderer.connect('edited', treeview_edit_done)
        c.set_attributes(renderer, text=idx)
        treeview.column_order.append(cname)
        
    model.column_order = treeview.column_order

    treeview.connect('cursor-changed', treeview_cursor_changed)
    treeview.edit_init_done = True


class CommonApp(object):
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def gtk_widget_hide(self, widget, data=None):
        widget.hide()
        return True
    
    
class EditableListTreeModel(gtk.GenericTreeModel):
    def __init__(self, data, rowmodel):
        gtk.GenericTreeModel.__init__(self)
        self.data = data

        self.rowmodel = rowmodel
        
        if hasattr(rowmodel, 'new'):
            self.data.append(rowmodel.new())
        
        self.dirty_row_path = None
        self.dirty_data = {}

    def get_row_from_path(self, path):
        if not len(self.data):
            return None

        return self.data[path[0]]

    def on_get_flags(self):
        return gtk.TREE_MODEL_LIST_ONLY
    
    def on_get_n_columns(self):
        return 3
    
    def on_get_column_type(self, index):
        return gobject.TYPE_STRING
    
    def on_get_path(self, node):
        return node
    
    def on_get_iter(self, path):
        return path if self.data else None 
    
    def on_get_value(self, node, column):
        if not len(self.data):
            return None
        
        field = self.column_order[column]
        if self.dirty_row_path and self.dirty_row_path == node and field in self.dirty_data: 
            return self.dirty_data[field]
        
        return getattr(self.rowmodel, field).to_string(self.data[node[0]])
    
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
