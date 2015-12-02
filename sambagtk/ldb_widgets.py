"""Defines special purpose widgets for viewing LDB databases. """
from gi.repository import Gtk, GObject
from  sambagtk import moderngtk, dialogs
import ldb
import os

class SearchBar(Gtk.Revealer):
    """This is like a Gtk.SearchBar (and styled similarly) but
        left-aligned and with a larger searchbox. """

    def __init__(self, toggle_item):
        super(SearchBar, self).__init__()
        container = Gtk.HBox() # Exta spacing
        toolbar = Gtk.HBox()
        toolbar.set_margin_top(3)
        toolbar.set_margin_bottom(3)
        container.pack_start(toolbar, expand=True, fill=True, padding=0)

        # Give this the same visual appearance as a Gtk.SearchBar. 
        container.get_style_context().add_class('search-bar')

        self.add(container)
        self.set_reveal_child(False)

        self.add_items(toolbar)
        toolbar.show_all()

        toggle_item.connect('clicked', self.toggled_cb)
        self.find_entry.connect('search-changed', self.trigger_search_changed)

    def add_items(self, toolbar):
        self.find_entry = Gtk.SearchEntry()
        toolbar.pack_start(self.find_entry, expand=True, fill=True, padding=3)

        # Placeholder for later items
        toolbar.pack_start(Gtk.VBox(), expand=True, fill=True, padding=3)

        # TODO add scope options, e.g. keys, value names, value contents, 
        #       whole string

    def toggled_cb(self, button):
        self.set_reveal_child(button.get_active())
        if button.get_active():
            self.find_entry.grab_focus()
            self.on_search_changed(self.find_entry.get_text())
        else:
            self.on_search_closed()

    def on_search_changed(self, text):
        """Event handler for text changes.
            Clients should override this as a property."""

    def on_search_closed(self):
        """Event handler for hiding the searchbar.
            Clients should override this as a property."""

    def trigger_search_changed(self, entry):
        self.on_search_changed(entry.get_text())

    def get_text(self):
        return self.find_entry.get_text()

class ActionedTreeView(object):
    CONTEXT_ALL = 0
    CONTEXT_BLANK = 1
    CONTEXT_SIDEBAR = 2
    CONTEXT_SEARCH = 3

    def __init__(self, treemodel, actions, vbox=None):
        if vbox is None:
            self.vbox = vbox = Gtk.VBox()
        self.treemodel = treemodel

        self.treeview = Gtk.TreeView()
        self.treeview.set_model(treemodel)
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(self.treeview)
        vbox.pack_start(scrolled, expand=True, fill=True, padding=0)

        toolbar = moderngtk.build_inline_toolbar()
        self.context_items = {}
        self.context_entries = {}
        for item in actions:
            if item:
                name, icon, tooltip, context, for_row, action = item
                if not context:
                    context = [self.CONTEXT_SIDEBAR]

                tool_item = Gtk.ToolButton(None, name)
                tool_item.set_icon_name(icon+'-symbolic') # use black&white icon
                tool_item.set_tooltip_text(tooltip)
                tool_item.connect('clicked', self.make_toolitem_handler(action))
                toolbar.add(tool_item)

                # We will need to enable and disable these options.
                # Also index the data to generate context menus. 
                for x in context + [self.CONTEXT_ALL]:
                    context_items = self.context_items.get(x, [])
                    context_items.append((for_row, tool_item))
                    self.context_items[x] = context_items

                    context_entries = self.context_entries.get(x, [])
                    context_entries.append(item)
                    self.context_entries[x] = context_entries
            else:
                # None represents a separator
                toolbar.add(Gtk.SeparatorToolItem())
        vbox.pack_start(toolbar, expand=False, fill=False, padding=0)

        self.set_context(self.CONTEXT_BLANK, False)

        self.treeview.connect('cursor_changed', self.cb_cursor_changed)
        self.treeview.connect('button-press-event', self.cb_button_pressed)

    def set_context(self, context, row_context=None):
        if context is not None:
            self.context = context
        if row_context is not None:
            self.row_context = row_context

        # Set tool item sensitivity appropriately. 
        for is_for_row, item in self.context_items.get(self.CONTEXT_ALL, []):
            item.set_sensitive(False)
        for is_for_row, item in self.context_items.get(self.context, []):
            if self.row_context or not is_for_row:
                item.set_sensitive(True)

    def get_row(self, path):
        if path is None:
            return None
        else:
            return self.treemodel.get(self.treemodel.get_iter(path),
                                        *range(self.treemodel.get_n_columns()))

    def make_toolitem_handler(self, action):
        def callback(button):
            path, column = self.treeview.get_cursor()
            action(self.get_row(path))
        return callback

    def make_menu_handler(self, action, data):
        def callback(widget):
            action(data)
        return callback

    def cb_cursor_changed(self, item):
        model, iter_ = item.get_selection().get_selected()
        self.set_context(None, iter_ is not None)

    def cb_button_pressed(self, treeview, event):
        if event.button == 3 and self.context in self.context_entries:
            x = int(event.x)
            y = int(event.y)
            pth_info = treeview.get_path_at_pos(x, y)

            if pth_info is not None:
                path, col, cellx, celly = pth_info
                path_str = ":".join(map(str, path))

                treeview.grab_focus()
                treeview.set_cursor(path, col, 0)

                data = self.get_row(Gtk.TreePath.new_from_string(path_str))
                is_row = True
            else:
                data = None
                is_row = False

            popup = Gtk.Menu()
            popup.attach_to_widget(treeview)
            for entry in self.context_entries[self.context]:
                if entry:
                    name, icon, tooltip, context, is_for_row, action = entry

                    if not is_for_row or is_row:
                        el = Gtk.ImageMenuItem.new_with_mnemonic(name)
                        el.set_image(Gtk.Image.new_from_icon_name(icon, 64))
                        el.connect('activate', 
                                    self.make_menu_handler(action, data))
                        popup.add(el)
            popup.show_all()
            popup.popup(None, None, None, None, event.button, event.time)
            return True

class EditorDialog(Gtk.Dialog):
    """Dialog wrapping a Gtk.TextView."""
    def __init__(self, *args, **kwargs):
        super(EditorDialog, self).__init__(*args, **kwargs)
        self.set_default_size(650, 500)

        self.text = Gtk.TextBuffer()
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(Gtk.TextView.new_with_buffer(self.text))
        self.vbox.pack_start(scrolled, expand=True, fill=True, padding=0)
        self.show_all()

    def get_text(self):
        return self.text.get_text(self.text.get_start_iter(),
                    self.text.get_end_iter(), False)

    def set_text(self, text):
        self.text.set_text(text)

class LdbURLDialog(dialogs.ConnectDialog):
    """Dialog that prompts for a LDB URL, and possibly username and password."""
    def __init__(self):
        super(LdbURLDialog, self).__init__("", 0, "", "")
        self.set_title("Connect to LDAP")
        self.transport_frame.hide()

    def get_ldb(self):
        print self.get_username(), self.get_password()
        return Ldb("ldap://"+self.get_server_address(), 0, [
                        "bindMech=simple",
                        "bindID=%s" % self.get_username(),
                        "bindSecret=%s" % self.get_password()
                    ])

class AddDnDialog(Gtk.Dialog):
    """Dialog that prompts for an a single line of text."""
    def __init__(self, dn=None, *args, **kwargs):
        super(AddDnDialog, self).__init__(*args, title=_("Enter DN"), **kwargs)
        self.set_default_geometry(-1, 400)
        self.dn = dn

        name_box = Gtk.HBox()
        self.vbox.pack_start(name_box, expand=False, fill=False, padding=9)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("RDN")
        name_box.pack_start(self.entry, expand=True, fill=True, padding=1)

        if dn:
            name_box.pack_start(Gtk.Label(","+str(dn)),
                                expand=False, fill=False, padding=1)

        # Attributes editor
        actions = [
            (_("Add"), 'list-add', _("Add an attribute"), 
                    None, False, self.on_add),
            (_("Delete"), 'list-remove', _("Delete selected attribute"),
                    None, True, self.on_remove)
        ]
        self.attrmodel = Gtk.ListStore(str, str, GObject.TYPE_BOOLEAN)
        new_iter = self.attrmodel.append(["", "", True])
        self.new_path = str(self.attrmodel.get_path(new_iter))
        treemanager = ActionedTreeView(self.attrmodel, actions, self.vbox)
        treemanager.set_context(ActionedTreeView.CONTEXT_SIDEBAR)
        self.treeview = treemanager.treeview

        self.columns = []
        for i, name in enumerate([_("_Name"), _("_Value")]):
            renderer = Gtk.CellRendererText()
            cur_col = Gtk.TreeViewColumn(name, renderer, text=i, editable=2)
            cur_col.set_sort_column_id(i)
            cur_col.set_resizable(True)

            self.columns.append(cur_col)
            self.treeview.append_column(cur_col)
            renderer.connect('edited', self.on_row_edited, i)
        self.treeview.set_headers_clickable(True)

        self.show_all()
        self.set_response_sensitive(Gtk.ResponseType.OK, False)

        # Connect signals
        self.entry.connect('changed', self.on_entry_changed)

    def get_message(self, db):
        dn = self.entry.get_text()
        if self.dn:
            dn += "," + str(self.dn)
        msg = ldb.Message(ldb.Dn(db, dn))

        iter_ = self.attrmodel.get_iter_first()
        while iter_:
            name, value = self.attrmodel.get(iter_, 0, 1)
            if name:
                msg[name] = value
            iter_ = self.attrmodel.iter_next(iter_)

        return msg

    def on_entry_changed(self, editable):
        self.set_response_sensitive(Gtk.ResponseType.OK, 
                                    bool(editable.get_text()))

    def on_row_edited(self, cell, path_str, text, column):
        """Ensures there's always a blank row at the end for adding attrs."""
        # Save the data
        iter_ = self.attrmodel.get_iter_from_string(path_str)
        self.attrmodel.set_value(iter_, column, text)

        if path_str == self.new_path and text:
            # Edited the empty row, create a new one.
            iter_ = self.attrmodel.append(["", "", True])
            self.new_path = str(self.attrmodel.get_path(iter_))
        elif path_str != self.new_path and not text:
            # Remove the row if emptied, as long as it's not the new row.
            iter_ = self.attrmodel.get_iter_from_string(path_str)
            name, value = self.attrmodel.get(iter_, 0, 1)

            if not name and not value:
                self.attrmodel.remove(iter_)

    def on_add(self, data):
        """Activates editing on the new row."""
        self.treeview.set_cursor(Gtk.TreePath.new_from_string(self.new_path),
                                self.columns[0], True)

    def on_remove(self, data):
        """Removes the selected row."""
        path, column = self.treeview.get_cursor()
        self.attrmodel.remove(self.attrmodel.get_iter(path))

class AddAttrDialog(Gtk.Dialog):
    """Dialog for adding an attribute to a DN."""
    def __init__(self, *args, **kwargs):
        super(AddAttrDialog, self).__init__(*args, **kwargs)

        self.attr_entry = Gtk.Entry()
        self.attr_entry.set_placeholder_text(_("Name"))
        self.vbox.add(self.attr_entry)
        self.value_entry = Gtk.Entry()
        self.value_entry.set_placeholder_text(_("Value"))
        self.vbox.add(self.value_entry)

        self.show_all()

    def get_data(self):
        return self.attr_entry.get_text(), self.value_entry.get_text()

def Ldb(*args):
    """Create a new LDB object.

    :param url: LDB URL to connect to.
    """
    ret = ldb.Ldb()
    path = os.getenv("LDB_MODULES_PATH")
    if path is not None:
        ret.set_modules_dir(path)
    ret.connect(*args)
    return ret
