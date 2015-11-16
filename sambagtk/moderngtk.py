"""
Helps Samba-GTK applications with modern GTK3 widgets
like the Headerbar and Infobars. 
"""
from gi.repository import Gtk
import os

def build_toolbar(window, vbox):
    """Creates a headerbar or toolbar appropriately for a window."""
    # Headerbars are vital to look native on GNOME3 and elementary OS
    # BUT they often look hideous elsewhere. 
    # To solve this I've resorted to detecting these desktops by name,
    # which is fine because it's only a minor visual issue if the check fails.
    desktop = set(os.getenv("XDG_CURRENT_DESKTOP","").split(":"))
    if desktop.intersection({"Pantheon", "GNOME"}):
        toolbar = Gtk.HeaderBar()
        window.set_titlebar(toolbar)
        toolbar.set_custom_title(Gtk.Box()) # Don't display a title.
        toolbar.set_show_close_button(True)
    else:
        toolbar = Gtk.Toolbar()
        vbox.pack_start(self.toolbar, expand=False, fill=False, padding=0)
    return toolbar

class InfoBar(Gtk.Revealer):
    """Abstraction over a typical Gtk.InfoBar widget hierarchy."""
    def __init__(self, *args, **kwargs):
        super(InfoBar, self).__init__(*args, **kwargs)

        self.infobar = Gtk.InfoBar()
        self.infobar.set_show_close_button(True)
        self.label = Gtk.Label()
        self.infobar.get_content_area().add(self.label)
        self.add(self.infobar)
        
        self.infobar.connect('close', self.hide_cb)
        self.infobar.connect('response', self.hide_cb)
        self.set_reveal_child(False)
   
    def hide_cb(self, *__):
        self.set_reveal_child(False)
    
    def display_message(self, msg, severity=Gtk.MessageType.ERROR):
        self.infobar.set_message_type(severity)
        self.label.set_markup(str(msg))
        self.set_reveal_child(True)

def build_inline_toolbar(treeview=None):
    toolbar = Gtk.Toolbar()
    
    toolbar.get_style_context().add_class("inline-toolbar") # For elementary
    toolbar.get_style_context().add_class(Gtk.STYLE_CLASS_INLINE_TOOLBAR)
    toolbar.get_style_context().set_junction_sides(Gtk.JunctionSides.TOP)
    toolbar.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
    
    box = None
    if treeview:
        scrolled = Gtk.ScrolledWindow()
        scrolled.add(treeview)
        
        box = Gtk.VBox()
        box.pack_start(scrolled, expand=True, fill=True, padding=0)
        box.pack_start(toolbar, expand=False, fill=False, padding=0)
    
    return toolbar, box
