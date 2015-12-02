# Samba GTK+ frontends
#
# Copyright (C) 2010 Sergio Martins <sergio97@gmail.com>
# Copyright (C) 2011 Jelmer Vernooij <jelmer@samba.org>
# Copyright (C) 2011 Dhananjay Sathe <dhananjaysathe@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk
from gi.repository import GdkPixbuf
import samba
import os
import sys
from ConfigParser import RawConfigParser

from moderngtk import get_resource

class AboutDialog(Gtk.AboutDialog):

    def __init__(self, name, description, icon=None):
        super(AboutDialog, self).__init__()
        self.set_icon_name('help-about')

        license_text = \
"""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>."""

        authors = ["Sergio Martins <Sergio97@gmail.com>",
                    "Calin Crisan <ccrisan@gmail.com>",
                    "Dhananjay Sathe <dhananajaysathe@gmail.com>",
                    "Jelmer Vernooij <jelmer@samba.org>",
                    "Adrian Cochrane <adrianc@catalyst.net.nz>"]
        copyright_text = "Copyright \xc2\xa9 2012 Dhananjay Sathe <dhananjaysathe@gmail.com>"

        print bool(icon)
        if icon:
            theme = Gtk.IconTheme.get_default()
            logo = theme.load_icon(icon, Gtk.IconSize.DIALOG, 0)
        else:
            filepath = get_resource('samba-logo-small.png')
            logo = GdkPixbuf.Pixbuf.new_from_file(filepath)
        self.set_property("program-name",name)
        self.set_property("logo",logo)
        self.set_property("version",samba.version)
        self.set_property("comments",description)
        self.set_property("wrap_license",True)
        self.set_property("license",license_text)
        self.set_property("authors",authors)
        self.set_property("copyright",copyright_text)

class ConnectDialog(Gtk.Dialog):
    """Connect Dialog"""
    CONFFILE = os.path.expanduser("~/.samba-gtk/connections")
    def __init__(self, server, transport_type, username, password):
        super(ConnectDialog, self).__init__()

        self.config = RawConfigParser()
        if os.path.exists(self.CONFFILE):
            self.config.read([self.CONFFILE])
            print self.config.sections()

        self.server_address = server or self.get_config("Server")
        self.username = username or self.get_config("Username")
        self.password = password or self.get_config("Password")
        self.transport_type = transport_type
        if self.transport_type is None:
            self.transport_type = self.get_config("Transport")
        self.domains = self.get_config("Domain") #required for sam manager
        self.create()
        self.show_all()

        self.update_sensitivity()

    def get_config(self, value):
        if self.config.has_option("Connection", value):
            ret = self.config.get("Connection", value)
            return ret
        else:
            return ""

    def save_config(self):
        """Call this to let the dialog remember previous settings."""
        if not self.config.has_section("Connection"):
            self.config.add_section("Connection")

        self.config.set("Connection", "Server",    self.get_server_address())
        self.config.set("Connection", "Username",  self.get_username())
        self.config.set("Connection", "Password",  self.get_password())
        self.config.set("Connection", "Transport", self.get_transport_type())

        path = os.path.dirname(self.CONFFILE)
        if not os.path.exists(path):
            os.mkdir(path)
        with open(self.CONFFILE, 'w') as f:
            self.config.write(f)

    def mod_create(self):
        # Interface to modify the builtin create to extend the gui
        pass

    def create(self):
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_modal(True)
        self.set_border_width(5)
        self.set_icon_name(Gtk.STOCK_CONNECT)
        self.set_resizable(False)
        self.set_decorated(True)

        self.vbox.set_spacing(5)

        # artwork

        self.artwork = Gtk.VBox()

        self.samba_image_filename = get_resource('samba-logo-small.png')
        self.samba_image = Gtk.Image()
        self.samba_image.set_from_file(self.samba_image_filename)
        self.artwork.pack_start(self.samba_image, expand=True, fill=True,
                                padding=0)

        label = Gtk.Label(_("Opening Windows to A Wider World"))
        box = Gtk.HBox()
        box.pack_start(label, expand=True, fill=True, padding=0)
        self.artwork.pack_start(box, expand=True, fill=True, padding=3)

        self.vbox.pack_start(self.artwork, expand=False, fill=True, padding=0)

        ########################### end of artwork TODO :

        # server frame
        self.server_frame = Gtk.Frame()
        self.server_frame.set_property('label', _("Server"))
        self.vbox.pack_start(self.server_frame, expand=False, fill=True,
                            padding=0)

        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_row_spacing(4)
        grid.set_property('border-width', 5)
        self.server_frame.add(grid)

        label = Gtk.Label(_("Server address:"), xalign=1, yalign=0.5)
        grid.attach(label, 0, 0, 1, 1)

        self.server_address_entry = Gtk.Entry()
        self.server_address_entry.set_text(self.server_address)
        self.server_address_entry.set_property('activates-default', True)
        self.server_address_entry.set_property('tooltip-text',
                                        _("Enter the Server Address"))
        grid.attach(self.server_address_entry, 1, 0, 1, 1)

        label = Gtk.Label(_("Username:"), xalign=1, yalign=0.5)
        grid.attach(label, 0, 1, 1, 1)

        self.username_entry = Gtk.Entry()
        self.username_entry.set_text(self.username)
        self.username_entry.set_property('activates-default', True)
        self.username_entry.set_property('tooltip-text',
                                            _("Enter your Username"))
        grid.attach(self.username_entry, 1, 1, 1, 1)

        label = Gtk.Label(_("Password:"), xalign=1, yalign=0.5)
        grid.attach(label, 0, 2, 1, 1)

        self.password_entry = Gtk.Entry()
        self.password_entry.set_text(self.password)
        self.password_entry.set_property('activates-default', True)
        self.password_entry.set_property('tooltip-text',
                                        _("Enter your Password"))
        self.password_entry.set_visibility(False)

        grid.attach(self.password_entry, 1, 2, 1, 1)

        # transport frame

        self.transport_frame = Gtk.Frame()
        self.transport_frame.set_property('label', _("Transport type"))
        self.vbox.pack_start(self.transport_frame, False, True, 0)

        vbox = Gtk.VBox()
        vbox.set_property('border-width', 5)
        self.transport_frame.add(vbox)

        self.rpc_smb_tcpip_radio_button = \
                        Gtk.RadioButton.new_with_label_from_widget(None,
                                _("RPC over SMB over TCP/IP"))
        self.rpc_smb_tcpip_radio_button.set_tooltip_text(
                                _("ncacn_np type : Recomended (default)"))
        # Default according MS-SRVS specification
        self.rpc_smb_tcpip_radio_button.set_active(self.transport_type == 0)
        vbox.pack_start(self.rpc_smb_tcpip_radio_button, True, True, 0)

        self.rpc_tcpip_radio_button = Gtk.RadioButton.new_with_label_from_widget(
                            self.rpc_smb_tcpip_radio_button,
                            _("RPC over TCP/IP"))
        self.rpc_tcpip_radio_button.set_tooltip_text(_("ncacn_ip_tcp type"))
        self.rpc_tcpip_radio_button.set_active(self.transport_type == 1)
        vbox.pack_start(self.rpc_tcpip_radio_button, True, True, 0)

        self.localhost_radio_button = Gtk.RadioButton.new_with_label_from_widget(
                            self.rpc_tcpip_radio_button, _("Localhost"))
        self.localhost_radio_button.set_tooltip_text(_("ncacn_ip_tcp type"))
        # MS-SRVS specification
        self.localhost_radio_button.set_active(self.transport_type == 2)
        vbox.pack_start(self.localhost_radio_button, True, True, 0)

        # dialog buttons
        self.action_area.set_layout(Gtk.ButtonBoxStyle.END)

        self.cancel_button = Gtk.Button(_("Cancel"), Gtk.STOCK_CANCEL)
        self.cancel_button.set_tooltip_text(_("Cancel and Quit"))
        self.add_action_widget(self.cancel_button, Gtk.ResponseType.CANCEL)

        self.connect_button = Gtk.Button(_("Connect"), Gtk.STOCK_CONNECT)
        self.connect_button.set_can_default(True)
        self.cancel_button.set_tooltip_text(_("OK / Connect to Server"))
        self.add_action_widget(self.connect_button, Gtk.ResponseType.OK)

        self.set_default_response(Gtk.ResponseType.OK)

        # signals/events

        self.rpc_smb_tcpip_radio_button.connect('toggled',
                                        self.on_radio_button_toggled)
        self.rpc_tcpip_radio_button.connect('toggled',
                                        self.on_radio_button_toggled)
        self.localhost_radio_button.connect('toggled',
                                        self.on_radio_button_toggled)
        self.mod_create()

    def get_server_address(self):
        if self.get_transport_type() is 2:
            return '127.0.0.1'
        return (self.server_address_entry.get_text().strip() or
                self.server_address )

    def get_username(self):
        return (self.username_entry.get_text().strip() or
                self.username)

    def get_password(self):
        return (self.password_entry.get_text() or
                self.password)

    def update_sensitivity(self):
        server_required = not self.localhost_radio_button.get_active()
        self.server_address_entry.set_sensitive(server_required)

    def get_transport_type(self):
        if self.rpc_smb_tcpip_radio_button.get_active():
            return 0
        elif self.rpc_tcpip_radio_button.get_active():
            return 1
        else:
            return 2

    def on_radio_button_toggled(self, widget):
        self.update_sensitivity()
