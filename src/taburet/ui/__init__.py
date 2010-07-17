import gtk

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
        
        
class CommonApp(object):
    def gtk_main_quit(self, widget):
        gtk.main_quit()

    def gtk_widget_hide(self, widget, data=None):
        widget.hide()
        return True    