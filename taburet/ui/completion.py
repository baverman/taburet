import weakref

import gtk
from gtk.keysyms import Escape, Up, Down, Return, KP_Up, KP_Enter, KP_Down

def entry_changed(entry, completion_ref):
    completion = completion_ref()

    completion.block_selection = True
    completion.tree.set_model(None)
    completion.model.clear()
    completion.on_fill(completion.model, entry.get_text())
    completion.tree.set_model(completion.model)

    completion.resize_popup_window(entry)
    if len(completion.model):
        if entry is not completion.entry:
            completion.show(entry)

        completion.block_selection = False
    else:
        if entry is completion.entry:
            completion.hide()

def default_fill_func(model, iter):
    pass

def defult_select_func(entry, model, iter, final):
    entry.set_text(model.get_value(iter, 0))
    entry.set_position(-1)

def make_simple_completion(choices):
    def fill(model, key):
        added = {}
        if not key:
            return

        key = unicode(key, 'utf-8').lower()

        for c in choices:
            if c not in added and ( key == '*' or c.lower().startswith(key) ):
                added[c] = True
                model.append((c, ))

        for c in choices:
            if c not in added and ( key == '*' or key in c.lower() ):
                model.append((c, ))

    model = gtk.ListStore(str)
    completion = Completion(model)
    completion.on_fill = fill
    column = completion.column
    cell = gtk.CellRendererText()
    column.pack_start(cell)
    column.set_attributes(cell, text=0)

    return completion


class Completion(object):
    def __init__(self, model):
        self.on_fill = default_fill_func
        self.on_select = defult_select_func

        self.model = model

        self.entry = None
        self.block_selection = True

        self.tree = gtk.TreeView()
        self.tree.set_headers_visible(False)
        #self.tree.set_hover_selection(True)
        self.tree.append_column(gtk.TreeViewColumn())

        self.tree_selection = self.tree.get_selection()
        self.tree_selection.connect('changed', self.on_selection_changed)

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        self.sw.add(self.tree)

        self.popup = gtk.Window(gtk.WINDOW_POPUP)
        self.popup.set_resizable(False)
        self.popup.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_COMBO)
        self.popup.connect('key-press-event', self.on_key_event)
        self.popup.connect('key-release-event', self.on_key_event)
        self.popup.connect('button-press-event', self.on_button_event)

        frame = gtk.Frame()
        frame.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        frame.add(self.sw)
        frame.show_all()

        self.popup.add(frame)

    @property
    def column(self):
        """:rtype: gtk.TreeViewColumn()"""
        return self.tree.get_column(0)

    def attach_to_entry(self, entry):
        entry.completion_changed_hid = entry.connect_after(
            'changed', entry_changed, weakref.ref(self))

    def resize_popup_window(self, entry):
        x, y = entry.window.get_origin()
        self.tree.set_size_request(-1, -1)
        w, h = self.tree.size_request()
        _, eh = entry.size_request()

        screen = entry.get_screen()
        monitor_num = screen.get_monitor_at_window(entry.window)
        sg = screen.get_monitor_geometry(monitor_num)

        h = min(h, sg.height / 3)
        self.tree.set_size_request(w, h)

        pw, ph = self.popup.size_request()
        if x + pw > sg.x + sg.width:
            x = sg.x + sg.width - pw

        if y + ph + eh <= sg.y + sg.height:
            y += eh
        else:
            y -= ph

        self.popup.move(x, y)
        self.popup.resize(*self.popup.size_request())

    def show(self, entry):
        self.entry = entry

        if self.popup.get_mapped():
            return

        if not entry.get_mapped():
            return

        if not entry.has_focus():
            return

        toplevel = entry.get_toplevel()
        toplevel.get_group().add_window(self.popup)

        self.tree.grab_focus()
        self.tree_selection.unselect_all()

        self.popup.set_screen(entry.get_screen())
        self.popup.show()

        self.popup.grab_add()
        gtk.gdk.pointer_grab(self.popup.window, True,
            gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_RELEASE_MASK,
            None, None, gtk.gdk.CURRENT_TIME)


    def hide(self):
        self.entry = None

        if not self.popup.get_mapped():
            return

        gtk.gdk.pointer_ungrab(gtk.gdk.CURRENT_TIME)
        self.popup.grab_remove()
        self.popup.hide()

    def select(self, is_next):
        model, iter = self.tree_selection.get_selected()
        if not iter:
            self.tree_selection.select_path((0, ))
            self.tree.scroll_to_cell((0, ))
        else:
            path = list(model.get_path(iter))
            path[0] += 1 if is_next else -1
            path = tuple(path)
            if path[0] >= 0 and path[0] < len(model):
                self.tree_selection.select_path(path)
                self.tree.scroll_to_cell(path)

    def on_selection_changed(self, selection):
        if not self.block_selection and self.entry:
            self.update_entry_value_by_selection(False)

    def update_entry_value_by_selection(self, final):
        model, iter = self.tree_selection.get_selected()
        if iter:
            self.entry.handler_block(self.entry.completion_changed_hid)
            self.on_select(self.entry, model, iter, final)
            self.entry.handler_unblock(self.entry.completion_changed_hid)
            return True

        return False

    def activate_selection(self):
        self.update_entry_value_by_selection(True)
        entry = self.entry
        self.hide()
        entry.activate()

    def on_key_event(self, popup, event):
        if event.keyval in (KP_Down, Down):
            if event.type == gtk.gdk.KEY_PRESS:
                self.select(True)
        if event.keyval in (KP_Up, Up):
            if event.type == gtk.gdk.KEY_PRESS:
                self.select(False)
        if event.keyval in (Return, KP_Enter):
            if event.type == gtk.gdk.KEY_PRESS:
                self.activate_selection()
        elif event.type == gtk.gdk.KEY_PRESS and event.keyval == Escape:
            self.hide()
        else:
            self.entry.event(event)

        return True

    def on_button_event(self, popup, event):
        self.hide()
        return True