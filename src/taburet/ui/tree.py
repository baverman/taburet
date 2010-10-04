import gtk

from .util import idle

def process_focus_like_access(treeview, path, current_column):
    columns = treeview.get_columns()
    for i, c in enumerate(columns):
        if c == current_column:
            break
        
    if i >= len(columns):
        return

    model = treeview.get_model()
    
    while True:
        i += 1
        if i >= len(columns):
            next_iter = model.iter_next(model.get_iter(path))
            if not next_iter:
                process_row_change(treeview, True)
                
                model.append_new()
                
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

def process_edit_done(treeview, new_text, path, column):
    model = treeview.get_model()
    
    if not model.dirty_row_path:
        model.dirty_row_path = (int(path),)
        model.dirty_data.clear()
    
    model.dirty_data[column.get_name()] = new_text
    
def process_row_change(treeview, force=False):
    path, _ = treeview.get_cursor()
    model = treeview.get_model()
    
    if model.dirty_row_path and ( force or model.dirty_row_path != path ):
        row = model.get_row_from_path(model.dirty_row_path)
        
        old_values = {}
        for k, v in model.dirty_data.iteritems():
            rm = getattr(model.rowmodel, k)
            old_values[k] = rm.to_string(row)
            rm.from_string(row, v)
            
        model.rowmodel.row_changed(model, row, old_values)
        
        model.dirty_row_path = None

def on_treeview_cursor_changed(treeview):
    path, column = treeview.get_cursor()

def on_treeview_focus_out(treeview, *args):
    print 'focus-out'
    treeview.editable_cursor = treeview.get_cursor()

def on_treeview_focus_in(treeview, *args):
    print 'focus-in'
    try:
        path, model = treeview.editable_cursor
        idle(treeview.set_cursor, path, model, True)
    except AttributeError:
        pass

def on_key_press_event(editable, event):
    if event.keyval == gtk.keysyms.Tab:
        editable.emit('editing-done')
        return True
        
    return False

def init_editable_treeview(treeview, model):
    treeview.set_model(model)
    treeview.columns_autosize()
    
    if getattr(treeview, 'edit_init_done', False):
        model.column_order = treeview.column_order
        return
    
    def treeview_edit_done(renderer, path, new_text, column):
        process_edit_done(treeview, new_text, path, column)
        return process_focus_like_access(treeview, path, column)
    
    def treeview_cursor_changed(treeview):
        return process_row_change(treeview)
        
    def general_editing_started(renderer, editable, path):
        editable.connect('key-press-event', on_key_press_event)

    treeview.column_order = []
    for idx, c in enumerate(treeview.get_columns()):
        cname = c.get_name()
        renderer = c.get_cell_renderers()[0]
        rm = getattr(model.rowmodel, cname)
        for k, v in rm.get_properties().iteritems(): 
            renderer.set_property(k, v)
        
        renderer.connect('edited', treeview_edit_done, c)
        c.set_attributes(renderer, text=idx)
        
        if hasattr(rm, 'on_editing_started'):
            renderer.connect('editing-started', rm.on_editing_started)
        
        renderer.connect('editing-started', general_editing_started)
        
        treeview.column_order.append(cname)
        
    model.column_order = treeview.column_order

    treeview.connect('cursor-changed', treeview_cursor_changed)
    treeview.connect_after('cursor-changed', on_treeview_cursor_changed)
#    treeview.connect_after('focus-in-event', on_treeview_focus_in)
#    treeview.connect('focus-out-event', on_treeview_focus_out)

    treeview.edit_init_done = True