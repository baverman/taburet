import gtk, gobject

class EditableListTreeModel(gtk.GenericTreeModel):
    def __init__(self, data, rowmodel):
        gtk.GenericTreeModel.__init__(self)
        self.data = data

        self.rowmodel = rowmodel

        self.append_new()
                
        self.dirty_row_path = None
        self.dirty_data = {}

    def append_new(self):
        if hasattr(self.rowmodel, 'new'):
            self.data.append(self.rowmodel.new())
            path = (len(self.data) - 1, )
            iter = self.get_iter(path)
            self.row_inserted(path, iter)

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
