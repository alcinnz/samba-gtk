# Samba GTK+ frontends
#
# Copyright (C) 2010 Sergio Martins <sergio97@gmail.com>
# Copyright (C) 2011 Jelmer Vernooij <jelmer@samba.org>
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
#

"""svcctl related dialogs."""

from gi.repository import GObject
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import GdkPixbuf

import sys
import os
from sambagtk.dialogs import ConnectDialog

from samba.dcerpc import svcctl

class Service(object):

    def __init__(self):
        self.name = ""
        self.display_name = ""
        self.description = ""

        self.state = svcctl.SVCCTL_STOPPED
        self.check_point = 0
        self.wait_hint = 0

        self.accepts_pause = False
        self.accepts_stop = False

        self.start_type = svcctl.SVCCTL_AUTO_START
        self.path_to_exe = ""
        self.account = None # local system account
        self.account_password = None # don't change
        self.allow_desktop_interaction = False

        self.start_params = ""
        # TODO: implement hw_profiles functionality
        #self.hw_profile_list = [["Profile 1", True], ["Profile 2", False]]

        self.handle = -1

    @staticmethod
    def get_state_string(state):
        return {
            svcctl.SVCCTL_CONTINUE_PENDING: _("Continue pending"),
            svcctl.SVCCTL_PAUSE_PENDING: _("Pause pending"),
            svcctl.SVCCTL_PAUSED: _("Paused"),
            svcctl.SVCCTL_RUNNING: _("Running"),
            svcctl.SVCCTL_START_PENDING: _("Start pending"),
            svcctl.SVCCTL_STOP_PENDING: _("Stop pending"),
            svcctl.SVCCTL_STOPPED: _("Stopped")
            }[state]

    @staticmethod
    def get_start_type_string(start_type):
        return {
            svcctl.SVCCTL_BOOT_START: _("Start at boot"),
            svcctl.SVCCTL_SYSTEM_START: _("Start at system startup"),
            svcctl.SVCCTL_AUTO_START: _("Start automatically"),
            svcctl.SVCCTL_DEMAND_START: _("Start manually"),
            svcctl.SVCCTL_DISABLED: _("Disabled"),
            }.get(start_type, "")

    def list_view_representation(self):
        return [self.name, self.display_name, self.description,
                Service.get_state_string(self.state),
                Service.get_start_type_string(self.start_type)]


class ServiceEditDialog(Gtk.Dialog):

    def __init__(self, service = None):
        super(ServiceEditDialog, self).__init__()

        if (service is None):
            self.brand_new = True
            self.service = Service()
        else:
            self.brand_new = False
            self.service = service

        self.create()

        if (not self.brand_new):
            self.service_to_values()
        self.update_sensitivity()

    def create(self):
        self.set_title(_("Edit service %s") % self.service.name)
        self.set_border_width(5)
        self.set_resizable(False)
        self.set_decorated(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_modal(True)
        self.set_size_request(450, 350)

        notebook = Gtk.Notebook()
        self.vbox.pack_start(notebook, True, True, 0)

        # general tab
        grid = Gtk.Grid()
        grid.set_border_width(5)
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)
        notebook.append_page(grid, Gtk.Label(_("General")))

        label = Gtk.Label(_("Name"), xalign=0, yalign=0.5)
        grid.attach(label, 0, 0, 1, 1)

        label = Gtk.Label(_("Display name"), xalign=0, yalign=0.5)
        grid.attach(label, 0, 1, 1, 1)

        label = Gtk.Label(_("Description"), xalign=0, yalign=0.5)
        grid.attach(label, 0, 2, 1, 1)

        label = Gtk.Label(_("Path to executable"), xalign=0, yalign=0.5)
        grid.attach(label, 0, 3, 1, 1)

        label = Gtk.Label(_("Startup type"), xalign=0, yalign=0.5)
        grid.attach(label, 0, 4, 1, 1)

        label = Gtk.Label(_("Start parameters"), xalign=0, yalign=0.5)
        grid.attach(label, 0, 5, 1, 1)

        self.name_label = Gtk.Label(xalign=0, yalign=0.5)
        grid.attach(self.name_label, 1, 0, 1, 1)

        self.display_name_entry = Gtk.Entry()
        self.display_name_entry.set_editable(False)
        grid.attach(self.display_name_entry, 1, 1, 1, 1)

        scrolledwindow = Gtk.ScrolledWindow(None, None)
        scrolledwindow.set_property('shadow_type', Gtk.ShadowType.IN)
        scrolledwindow.set_size_request(0, 50)
        grid.attach(scrolledwindow, 1, 2, 1, 1)

        self.description_text_view = Gtk.TextView()
        self.description_text_view.set_editable(False)
        self.description_text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolledwindow.add(self.description_text_view)

        self.exe_path_entry = Gtk.Entry()
        self.exe_path_entry.set_editable(False)
        grid.attach(self.exe_path_entry, 1, 3, 1, 1)

        self.startup_type_combo = Gtk.ComboBoxText()
        self.startup_type_combo.append_text(Service.get_start_type_string(
                    svcctl.SVCCTL_BOOT_START))
        self.startup_type_combo.append_text(Service.get_start_type_string(
                    svcctl.SVCCTL_SYSTEM_START))
        self.startup_type_combo.append_text(Service.get_start_type_string(
                    svcctl.SVCCTL_AUTO_START))
        self.startup_type_combo.append_text(Service.get_start_type_string(
                    svcctl.SVCCTL_DEMAND_START))
        self.startup_type_combo.append_text(Service.get_start_type_string(
                    svcctl.SVCCTL_DISABLED))
        grid.attach(self.exe_path_entry, 1, 4, 1, 1)

        self.start_params_entry = Gtk.Entry()
        self.start_params_entry.set_activates_default(True)
        grid.attach(self.exe_path_entry, 1, 5, 1, 1)

        # log on tab
        #table = gtk.Table(8, 3, False)
        grid = Gtk.Grid()
        grid.set_border_width(5)
        grid.set_column_spacing(5)
        grid.set_row_spacing(5)
        notebook.append_page(grid, Gtk.Label(_("Log On")))

        self.local_account_radio = Gtk.RadioButton.new_with_mnemonic_from_widget(
                                None, _("_Local System account"))
        grid.attach(self.local_account_radio, 0, 0, 1, 1)

        self.allow_desktop_interaction_check = Gtk.CheckButton.new_with_mnemonic(
                                _("Allo_w service to interact with desktop"))
        grid.attach(self.allow_desktop_interaction_check, 0, 1, 2, 1)

        self.this_account_radio = Gtk.RadioButton.new_with_mnemonic_from_widget(
                                self.local_account_radio, _("_This account:"))
        grid.attach(self.this_account_radio, 0, 2, 1, 1)

        self.account_entry = Gtk.Entry()
        self.account_entry.set_activates_default(True)
        grid.attach(self.account_entry,  1, 2, 1, 1)

        label = Gtk.Label(_("Password:"), xalign=0, yalign=0.5)
        grid.attach(label, 0, 3, 1, 1)

        self.password_entry = Gtk.Entry()
        self.password_entry.set_activates_default(True)
        self.password_entry.set_visibility(False)
        grid.attach(self.password_entry, 1, 3, 1, 1)

        label = Gtk.Label(_("Confirm password:"), xalign=0 , yalign=0.5)
        grid.attach(label, 0, 4, 1, 1)

        self.confirm_password_entry = Gtk.Entry()
        self.confirm_password_entry.set_activates_default(True)
        self.confirm_password_entry.set_visibility(False)
        grid.attach(self.confirm_password_entry, 1, 4, 1, 1)

        # TODO: implement hw profiles functionality
        label = Gtk.Label(_("You can enable or disable this service "
                            "for the hardware profiles listed below :"))
        #table.attach(label, 0, 3, 5, 6, 0, 0, 0, 5)

        scrolledwindow = Gtk.ScrolledWindow(None, None)
        scrolledwindow.set_property('shadow_type',Gtk.ShadowType.IN)
        #table.attach(scrolledwindow, 0, 3, 6, 7, gtk.FILL | gtk.EXPAND,
        #               gtk.FILL | gtk.EXPAND, 0, 0)

        self.profiles_tree_view = Gtk.TreeView()
        scrolledwindow.add(self.profiles_tree_view)

        column = Gtk.TreeViewColumn()
        column.set_title(_("Hardware profile"))
        renderer = Gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.profiles_tree_view.append_column(column)
        column.add_attribute(renderer, 'text', 0)

        column = Gtk.TreeViewColumn()
        column.set_title(_("Status"))
        renderer = Gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.profiles_tree_view.append_column(column)
        column.add_attribute(renderer, 'text', 1)

        self.profiles_store = Gtk.ListStore(GObject.TYPE_STRING,
                                            GObject.TYPE_STRING)
        self.profiles_store.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.profiles_tree_view.set_model(self.profiles_store)

        hbox = Gtk.HBox(2, False)
#        table.attach(hbox, 0, 1, 7, 8, 0, 0, 0, 0)

        self.enable_button = Gtk.Button(_("Enable"))
        hbox.pack_start(self.enable_button, False, False, 0)

        self.disable_button = Gtk.Button(_("Disable"))
        hbox.pack_start(self.disable_button, False, False, 0)

        # dialog buttons

        self.action_area.set_layout(Gtk.ButtonBoxStyle.END)

        self.cancel_button = Gtk.Button(_("Cancel"), Gtk.STOCK_CANCEL)
        self.cancel_button.set_can_default(True)
        self.add_action_widget(self.cancel_button, Gtk.ResponseType.CANCEL)

        self.apply_button = Gtk.Button(_("Apply"), Gtk.STOCK_APPLY)
        self.apply_button.set_can_default(True)
        # Disabled for new group
        self.apply_button.set_sensitive(not self.brand_new)
        self.add_action_widget(self.apply_button, Gtk.ResponseType.APPLY)

        self.ok_button = Gtk.Button(_("OK"), Gtk.STOCK_OK)
        self.ok_button.set_can_default(True)
        self.add_action_widget(self.ok_button, Gtk.ResponseType.OK)

        self.set_default_response(Gtk.ResponseType.OK)

        # signals/events
        self.local_account_radio.connect('toggled',
                                          self.on_local_account_radio_clicked)
        #self.profiles_tree_view.get_selection().connect("changed",
        #           self.on_profiles_tree_view_selection_changed)
        #self.enable_button.connect("clicked", self.on_enable_button_click)
        #self.disable_button.connect("clicked", self.on_disable_button_click)

    def check_for_problems(self):
        if (self.password_entry.get_text() != 
                self.confirm_password_entry.get_text() and 
                self.this_account_radio.get_active()):
            return _("The password was not correctly confirmed.")

        return None

    def update_sensitivity(self):
        local_account = self.local_account_radio.get_active()

        self.allow_desktop_interaction_check.set_sensitive(local_account)
        self.account_entry.set_sensitive(not local_account)
        self.password_entry.set_sensitive(not local_account)
        self.confirm_password_entry.set_sensitive(not local_account)

#        profile = self.get_selected_profile()
#        if (profile is None):
#            self.enable_button.set_sensitive(False)
#            self.disable_button.set_sensitive(False)
#        else:
#            self.enable_button.set_sensitive(not profile[1])
#            self.disable_button.set_sensitive(profile[1])

    def service_to_values(self):
        if (self.service is None):
            raise Exception("service not set")

        self.name_label.set_text(self.service.name)
        self.display_name_entry.set_text(self.service.display_name)
        self.description_text_view.get_buffer().set_text(
                            self.service.description)
        self.exe_path_entry.set_text(self.service.path_to_exe)

        temp_dict = {svcctl.SVCCTL_BOOT_START:0,
                     svcctl.SVCCTL_SYSTEM_START:1,
                     svcctl.SVCCTL_AUTO_START:2,
                     svcctl.SVCCTL_DEMAND_START:3,
                     svcctl.SVCCTL_DISABLED:4}

        self.startup_type_combo.set_active(temp_dict[self.service.start_type])
        self.start_params_entry.set_text(self.service.start_params)

        if (self.service.account is None):
            self.local_account_radio.set_active(True)
            self.allow_desktop_interaction_check.set_active(
                            self.service.allow_desktop_interaction)
        else:
            self.this_account_radio.set_active(True)
            self.account_entry.set_text(self.service.account)

            if (self.service.account_password is not None):
                self.password_entry.set_text(self.service.account_password)
                self.confirm_password_entry.set_text(
                            self.service.account_password)

        #self.refresh_profiles_tree_view()

    def values_to_service(self):
        if (self.service is None):
            raise Exception("service not set")

        temp_dict = {svcctl.SVCCTL_BOOT_START:0,
                    svcctl.SVCCTL_SYSTEM_START:1,
                    svcctl.SVCCTL_AUTO_START:2,
                    svcctl.SVCCTL_DEMAND_START:3,
                    svcctl.SVCCTL_DISABLED:4}

        self.service.start_type = temp_dict[self.startup_type_combo.get_active()]
        self.service.start_params = self.start_params_entry.get_text()

        if (self.local_account_radio.get_active()):
            self.service.account = None
            self.service.account_password = None
            self.service.allow_desktop_interaction =  \
                            self.allow_desktop_interaction_check.get_active()
        else:
            self.service.account = self.account_entry.get_text()
            self.service.account_password = self.password_entry.get_text()

#        del self.service.hw_profile_list[:]
#
#        iter = self.profiles_store.get_iter_first()
#        while (iter is not None):
#            name = self.profiles_store.get_value(iter, 0)
#            enabled = self.profiles_store.get_value(iter, 1)
#            self.service.hw_profile_list.append([name, 
#                            [False, True][enabled == "Enabled"]])
#            iter = self.profiles_store.iter_next(iter)

#    def refresh_profiles_tree_view(self):
#        model, paths = self.profiles_tree_view.get_selection(
#                            ).get_selected_rows()
#
#        self.profiles_store.clear()
#        for profile in self.service.hw_profile_list:
#            self.profiles_store.append((profile[0],
#                            ["Disabled", "Enabled"][profile[1]]))
#
#        if (len(paths) > 0):
#            self.profiles_tree_view.get_selection().select_path(paths[0])

#    def get_selected_profile(self):
#        (model, iter) = self.profiles_tree_view.get_selection().get_selected()
#        if (iter is None): # no selection
#            return None
#        else:
#            name = model.get_value(iter, 0)
#            return [profile
#                    for profile in self.service.hw_profile_list
#                    if profile[0] == name
#                    ][0]

    def on_local_account_radio_clicked(self, widget):
        self.update_sensitivity()

#    def on_enable_button_click(self, widget):
#        profile = self.get_selected_profile()
#        if (profile is None): # no selection
#            return
#
#        profile[1] = True
#        self.refresh_profiles_tree_view()
#
#    def on_disable_button_click(self, widget):
#        profile = self.get_selected_profile()
#        if (profile is None): # no selection
#            return
#
#        profile[1] = False
#        self.refresh_profiles_tree_view()
#
#    def on_profiles_tree_view_selection_changed(self, widget):
#        self.update_sensitivity()

class ServiceControlDialog(Gtk.Dialog):
    def __init__(self, service, control):
        super(ServiceControlDialog, self).__init__()

        self.service = service
        self.control = control
        self.cancel_callback = None
        self.progress_speed = 0.1

        self.create()

    def create(self):
        self.set_title(_("Service Control"))
        self.set_border_width(10)
        self.set_resizable(False)
        self.set_size_request(400, 150)
        self.set_decorated(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_modal(True)

        self.control_label = Gtk.Label()
        self.control_label.set_markup("<b>" + 
                    ServiceControlDialog.get_control_string(self) +
                    "</b> " + self.service.display_name + "...")
        self.control_label.set_padding(10, 10)
        self.control_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.vbox.pack_start(self.control_label, False, True, 5)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.vbox.pack_start(self.progress_bar, False, True, 5)

        # dialog buttons
        self.action_area.set_layout(Gtk.ButtonBoxStyle.CENTER)

        self.close_button = Gtk.Button(_("Close"), Gtk.STOCK_CLOSE)
        self.close_button.set_can_default(True)
        self.add_action_widget(self.close_button, Gtk.ResponseType.CANCEL)

        self.set_default_response(Gtk.ResponseType.CANCEL)


        # signals/events
        self.close_button.connect('clicked', self.on_close_button_clicked)

    def get_control_string(self):
        if (self.control is None):
            return _("Starting")
        elif (self.control == svcctl.SVCCTL_CONTROL_STOP):
            return _("Stopping")
        elif (self.control == svcctl.SVCCTL_CONTROL_PAUSE):
            return _("Pausing")
        elif (self.control == svcctl.SVCCTL_CONTROL_CONTINUE):
            return _("Resuming")
        else:
            return ""

    def set_close_callback(self, close_callback):
        self.close_callback = close_callback

    def progress(self, to_the_end = False):
        fraction = self.progress_bar.get_fraction()

        if ((fraction + self.progress_speed >= 1.0) or to_the_end):
            self.progress_bar.set_fraction(1.0)
        else:
            self.progress_bar.set_fraction(fraction + self.progress_speed)

    def set_progress_speed(self, progress_speed):
        self.progress_speed = progress_speed

    def on_close_button_clicked(self, widget):
        if (self.close_callback is not None):
            self.close_callback()


class SvcCtlConnectDialog(ConnectDialog):
    def __init__(self, server, transport_type, username, password):

        super(SvcCtlConnectDialog, self).__init__(
                    server, transport_type, username, password)
        self.set_title(_("Connect to Samba Service Manager"))
