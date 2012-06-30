#  main.py
#  
# Copyright (C) 2010 Sergio Martins <sergio97@gmail.com>
# Copyright (C) 2012 Jelmer Vernooij <jelmer@samba.org>
# Copyright (C) 2012 Dhananjay Sathe <dhananjaysathe@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  

import sys
import os.path
import getopt

from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GLib


import pygwsam                     #################  TODO : Local###
import pygwregedit
import pygwcrontab
import pygwsvcctl
import pygwshare

from dialogs import AboutDialog
from sam import SAMConnectDialog   #################################


class SambaUtilities(object):

    def __init__(self, connection_args={}, additional_connection_arguments={}):

        self.create()

        # these are the old windows of the utilities. We reparent the main
        # widget so these arn't displayed but we need the handle so we can
        # call functions and grab objects
        self.sam_window = None
        self.regedit_window = None
        self.svcctl_window = None
        self.crontab_window = None
        self.srvsvc_window = None
        self.srvsvc_init= False

        self.connection_args = connection_args
        self.additional_connection_args = {} #arguments not supported by all utilities, such as domain_index
        self.additional_connection_args.update(
                                  {"info_callback":self.server_info_callback}) #to save info or get updated info
        self.print_redirect_sring = ""

        self.update_sensitivity()
        self.window.show()
        self.push_status_message("Utility started successfully.")
        self.utilites_notebook.grab_focus() #So switching to the regedit tab doesn't automatically focus the keys tree view

        if (connection_args.has_key("connect_now") and
        connection_args["connect_now"]):
            self.on_connect_all_button_clicked(None)


    def create(self):
        builder = Gtk.Builder()
        builder.add_from_file("main.ui")

        # dictionary for connections
        connections = {"on_main_window_destroy":
                            Gtk.main_quit,
                       "on_main_window_key_press_event":
                            self.on_main_window_key_press_event,
                       "on_connect_all_item_activate":
                            self.on_connect_all_button_clicked,
                       "on_disconnect_all_item_activate":
                            self.on_disconnect_all_button_clicked,
                       "on_quit_item_activate":
                            self.on_quit_item_activate,
                       "on_clear_log_activate":
                            self.on_clear_log_activate,
                       "on_connection_info_item_activate":
                            self.on_connection_info_item_activate,
                       "on_about_item_activate":
                            self.on_about_item_activate,
                       "on_connect_all_button_clicked":
                            self.on_connect_all_button_clicked,
                       "on_disconnect_all_button_clicked":
                            self.on_disconnect_all_button_clicked,
                       "on_clear_log_button_clicked":
                            self.on_clear_log_activate,
                       "on_utility_notebook_switch_page":
                            self.on_utility_notebook_switch_page,

                       }
        #Make the connections
        builder.connect_signals(connections)

        #Handles
        self.window = builder.get_object("main_window")
        self.menubar_viewport = builder.get_object("menubar_viewport")
        self.menubar = builder.get_object("menubar")
        self.connect_all_item = builder.get_object("connect_all_item")
        self.disconnect_all_item = builder.get_object("disconnect_all_item")

        self.toolbar_viewport = builder.get_object("toolbar_viewport")
        self.toolbar = builder.get_object("toolbar")
        self.connect_all_button = builder.get_object("connect_all_button")
        self.disconnect_all_button= builder.get_object("disconnect_all_button")

        self.utilites_notebook = builder.get_object("utility_notebook")

        self.server_label = builder.get_object("server_label")
        self.username_label = builder.get_object("username_label")
        self.status_label = builder.get_object("status_label")
        self.messages_textview = builder.get_object("messages_textview")

        self.sam_viewport = builder.get_object("sam_viewport")
        self.srvsvc_viewport = builder.get_object("srvsvc_viewport")
        self.svcctl_viewport = builder.get_object("svcctl_viewport")
        self.crontab_viewport = builder.get_object("crontab_viewport")
        self.regedit_viewport = builder.get_object("regedit_viewport")

        self.progressbar = builder.get_object("progressbar")
        self.statusbar = builder.get_object("statusbar")


    def init_sam_page(self):

        args = self.connection_args.copy()
        if self.additional_connection_args.has_key("domain_index"):
            args.update({"domain_index":
                        self.additional_connection_args["domain_index"]})
        if self.additional_connection_args.has_key("info_callback"):
            args.update({"info_callback":
                    self.additional_connection_args["info_callback"]})

        self.sam_window = pygwsam.SAMWindow(**args) #start up the utility
        self.sam_window.users_groups_notebook.reparent(self.sam_viewport) #reparent the main widget into a notebook tab
        self.sam_viewport.show_all() #unhide all widgets

        #We'll be displaying this later. We need to unparent it before attaching it to another container
        self.sam_window.menubar.unparent()
        self.sam_window.toolbar.unparent()
        self.sam_window.statusbar = self.statusbar #we simply tell the utility to use our status bar instead

        self.set_status("User tab initialized.")
        self.update_sensitivity()

    def init_srvsvc_page(self):

        args = self.connection_args.copy()
        if self.additional_connection_args.has_key("info_callback"):
            args.update({"info_callback":
                        self.additional_connection_args["info_callback"]})

        self.srvsvc_window = pygwshare.ShareWindow(**args) #start up the utility
        self.srvsvc_window.portablity_box.reparent(self.srvsvc_viewport) #reparent the main widget into a notebook tab
        self.srvsvc_viewport.show_all() #unhide all widgets

        #We'll be displaying this later. We need to unparent it before attaching it to another container

        self.srvsvc_window.menubar.unparent()
        self.srvsvc_window.toolbar.unparent()
        self.srvsvc_window.statusbar = self.statusbar #we simply tell the utility to use our status bar instead

        self.set_status("Share Manager tab initialized.")
        self.update_sensitivity()

    def init_regedit_page(self):
        args = self.connection_args.copy()
        if self.additional_connection_args.has_key("info_callback"):
            args.update({"info_callback":
                        self.additional_connection_args["info_callback"]})
        self.regedit_window = pygwregedit.RegEditWindow(**args) #start up the utility
        self.regedit_window.hpaned.reparent(self.regedit_viewport) #reparent the main widget into a notebook tab
        self.regedit_viewport.show_all() #unhide all widgets

        self.regedit_window.menubar.unparent()
        self.regedit_window.toolbar.unparent()
        self.regedit_window.progressbar = self.progressbar
        self.regedit_window.statusbar = self.statusbar

        self.set_status("Regedit tab initialized.")
        self.update_sensitivity()

    def init_svcctl_page(self):
        args = self.connection_args.copy()
        if self.additional_connection_args.has_key("info_callback"):
            args.update({"info_callback":
                        self.additional_connection_args["info_callback"]})
        self.svcctl_window = pygwsvcctl.SvcCtlWindow(**args) #start up the utility
        self.svcctl_window.scrolledwindow.reparent(self.svcctl_viewport) #reparent the main widget into a notebook tab
        self.svcctl_viewport.show_all() #unhide all widgets

        self.svcctl_window.menubar.unparent()
        self.svcctl_window.toolbar.unparent()
        self.svcctl_window.progressbar = self.progressbar
        self.svcctl_window.statusbar = self.statusbar

        self.set_status("Services tab initialized.")
        self.update_sensitivity()

    def init_crontab_page(self):
        args = self.connection_args.copy()
        if self.additional_connection_args.has_key("info_callback"):
            args.update({"info_callback":
                        self.additional_connection_args["info_callback"]})
        self.crontab_window = pygwcrontab.CronTabWindow(**args) #start up the utility
        self.crontab_window.scrolledwindow.reparent(self.crontab_viewport) #reparent the main widget into a notebook tab
        self.crontab_viewport.show_all() #unhide all widgets

        self.crontab_window.menubar.unparent()
        self.crontab_window.toolbar.unparent()
        self.crontab_window.statusbar = self.statusbar

        self.set_status("Scheduled tasks tab initialized.")
        self.update_sensitivity()

    def sam_initialized(self):
        return self.sam_window is not None

    def regedit_initialized(self):
        return self.regedit_window is not None

    def srvsvc_initialized (self):
        return self.srvsvc_window is not None

    def svcctl_initialized(self):
        return self.svcctl_window is not None

    def crontab_initialized(self):
        return self.crontab_window is not None

    def update_sensitivity(self):
        sam_connected = (self.sam_initialized() and
                        self.sam_window.connected())
        srvsvc_connected = (self.srvsvc_initialized() and
                           self.srvsvc_window.connected())
        regedit_connected = (self.regedit_initialized() and
                            self.regedit_window.connected())
        svcctl_connected = (self.svcctl_initialized() and
                           self.svcctl_window.connected())
        crontab_connected = (self.crontab_initialized() and
                            self.crontab_window.connected())
        all_connected = (sam_connected and regedit_connected and
                         svcctl_connected and crontab_connected and
                         srvsvc_connected )
        all_disconnected = ((not sam_connected) and
                            (not regedit_connected) and
                            (not svcctl_connected) and
                            (not crontab_connected) and
                            (not srvsvc_connected) )

        self.connect_all_button.set_sensitive(not all_connected)
        self.disconnect_all_button.set_sensitive(not all_disconnected)
        self.connect_all_item.set_sensitive(not all_connected)
        self.disconnect_all_item.set_sensitive(not all_disconnected)

        self.server_label.set_text(self.connection_args.has_key("server") and
                                  self.connection_args["server"] or "Unknown")
        self.username_label.set_text(self.connection_args.has_key("username")
                            and self.connection_args["username"] or "Unknwon")
        if (all_connected):
            self.status_label.set_text("All connected")
        elif (all_disconnected):
            self.status_label.set_text("All disconnected")
        else:
            connected_utilities = []
            if sam_connected:
                connected_utilities.append("User Manager")
            if srvsvc_connected:
                connected_utilities.append("Share Manager")
            if regedit_connected:
                connected_utilities.append("Registry Editor")
            if svcctl_connected:
                connected_utilities.append("Services Manager")
            if crontab_connected:
                connected_utilities.append("Task Scheduler")
            if len(connected_utilities) > 1:
                connected_utilities[-1] = "and %s" % connected_utilities[-1]
            self.status_label.set_text("%s %s" % (", ".join(
                                        connected_utilities), "connected."))

    def server_info_callback(self, server = "", username = "",
                            transport_type = None):
        if server:
            self.connection_args.update({"server":server})
        if username:
            self.connection_args.update({"username":username})
        if transport_type:
            self.connection_args.update({"transport_type":transport_type})

    def run_message_dialog(self, type, buttons, message, parent = None):
        if (parent == None):
            parent = self.window

        message_box = Gtk.MessageDialog(parent, Gtk.DialogFlags.MODAL,
                                       type, buttons, message)
        response = message_box.run()
        message_box.hide()

        return response

    def run_connect_all_dialog(self):
        """Runs the connection dialog and saves connection arguments to self.connection_args

        returns True if arguments were uptained successfully"""
        #TODO in this function: handle domain selection
        args = {}
        #args and their default values
        important_args = {"server":"", "username":"", "transport_type":0, }
        for item in important_args.keys():
                args.update(self.connection_args.has_key(item) and
                            {item:self.connection_args[item]} or
                            {item:important_args[item]})

        dialog = SAMConnectDialog(**args)
        dialog.show_all()

        # loop to handle the failures
        while True:
            response_id = dialog.run()

            if (response_id != Gtk.ResponseType.OK):
                dialog.hide()
                return False
            else:
                server = dialog.get_server_address()
                username = dialog.get_username()
                if server != "" and username != "":
                    self.connection_args.update({"server":server})
                    self.connection_args.update({"username":username})
                    self.connection_args.update({"transport_type":
                                                dialog.get_transport_type()})
                    self.connection_args.update({"password":
                                               dialog.get_password()})
                    self.connection_args.update({"connect_now":True})
                    self.additional_connection_args.update({"domain_index":0}) #TODO: get domain index
                    break
                else:
                    self.run_message_dialog(Gtk.MessageType.ERROR,
                                           Gtk.ButtonsType.OK,
                                           "You must enter a server address and username.")


        dialog.hide()
        return True

    def write(self, string): #Make this class a writeable object. Used so we can redirect print statements
        if string == '\n':
            self.push_status_message(self.print_redirect_sring)
            print >>sys.__stdout__, self.print_redirect_sring #also print the string normally
            self.print_redirect_sring = ""
        else:
            self.print_redirect_sring += string

    def push_status_message(self, message):
        """Pushes a message to the status textview in the main tab. This function inserts a \"\\n\" for you."""
        buffer = self.messages_textview.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(),
                              buffer.get_end_iter(), True)
        text += message + "\n"
        buffer.set_text(text)

        #scroll to the bottom
        self.messages_textview.scroll_to_iter(buffer.get_end_iter(),
                                            0.0, False, 0.5, 0.5 )      #set as per previous gtk2 standards

    def set_status(self, message):
        self.statusbar.pop(0)
        self.statusbar.push(0, message)
        self.push_status_message(message)

    def on_main_window_key_press_event(self, widget, event):
        current_page = self.utilites_notebook.get_current_page()

        if current_page == 1:
            self.sam_window.on_key_press(widget, event)
        elif current_page == 2:
            self.srvsvc_window.on_key_press(widget, event)
        elif current_page == 3:
            self.regedit_window.on_key_press(widget, event)
        elif current_page == 4:
            self.svcctl_window.on_key_press(widget, event)
        elif current_page == 5:
            self.crontab_window.on_key_press(widget, event)

    def on_utility_notebook_switch_page(self, widget, page, page_num):
        if page_num == 0: #main page

            #Menubar
            children = self.menubar_viewport.get_children()
            self.menubar_viewport.remove(children[0])
            self.menubar_viewport.add(self.menubar)
            self.menubar_viewport.show_all()
            #Toolbar
            children = self.toolbar_viewport.get_children()
            self.toolbar_viewport.remove(children[0])
            self.toolbar_viewport.add(self.toolbar)
            self.toolbar_viewport.show_all()

            self.update_sensitivity()

        elif page_num == 1: #Sam page
            if self.sam_viewport.get_child() == None:
                self.init_sam_page()

            #Menubar
            children = self.menubar_viewport.get_children()
            self.menubar_viewport.remove(children[0])
            self.menubar_viewport.add(self.sam_window.menubar)
            self.menubar_viewport.show_all()

            #Toolbar
            children = self.toolbar_viewport.get_children()
            self.toolbar_viewport.remove(children[0])
            self.toolbar_viewport.add(self.sam_window.toolbar)
            self.toolbar_viewport.show_all()


        elif page_num == 2: #Share page
            if self.srvsvc_viewport.get_child() == None:
                self.init_srvsvc_page()

            #Menubar
            children = self.menubar_viewport.get_children()
            self.menubar_viewport.remove(children[0])
            self.menubar_viewport.add(self.srvsvc_window.menubar)
            self.menubar_viewport.show_all()

            #Toolbar
            children = self.toolbar_viewport.get_children()
            self.toolbar_viewport.remove(children[0])
            self.toolbar_viewport.add(self.srvsvc_window.toolbar)
            self.toolbar_viewport.show_all()

            self.srvsvc_window.hide()

        elif page_num == 3: #Regedit page
            if self.regedit_viewport.get_child() == None:
                self.init_regedit_page()

            #Menubar
            children = self.menubar_viewport.get_children()
            self.menubar_viewport.remove(children[0])
            self.menubar_viewport.add(self.regedit_window.menubar)
            self.menubar_viewport.show_all()

            #Toolbar
            children = self.toolbar_viewport.get_children()
            self.toolbar_viewport.remove(children[0])
            self.toolbar_viewport.add(self.regedit_window.toolbar)
            self.toolbar_viewport.show_all()

        elif page_num == 4: #Services page
            if self.svcctl_viewport.get_child() == None:
                self.init_svcctl_page()

            #Menubar
            children = self.menubar_viewport.get_children()
            self.menubar_viewport.remove(children[0])
            self.menubar_viewport.add(self.svcctl_window.menubar)
            self.menubar_viewport.show_all()

            #Toolbar
            children = self.toolbar_viewport.get_children()
            self.toolbar_viewport.remove(children[0])
            self.toolbar_viewport.add(self.svcctl_window.toolbar)
            self.toolbar_viewport.show_all()

        elif page_num == 5: #Crontab page
            if self.crontab_viewport.get_child() == None:
                self.init_crontab_page()

            #Menubar
            children = self.menubar_viewport.get_children()
            self.menubar_viewport.remove(children[0])
            self.menubar_viewport.add(self.crontab_window.menubar)
            self.menubar_viewport.show_all()

            #Toolbar
            children = self.toolbar_viewport.get_children()
            self.toolbar_viewport.remove(children[0])
            self.toolbar_viewport.add(self.crontab_window.toolbar)
            self.toolbar_viewport.show_all()

    def on_connect_all_button_clicked(self, widget):

        if (self.connection_args.has_key("connect_now") and
        self.connection_args["connect_now"]):
            #if the user specified --connect-now then we probably have enough arguments to connect

            if self.sam_initialized():
                if not self.sam_window.connected():
                    self.sam_window.on_connect_item_activate(None,
                                                       **self.connection_args)
            else:
                self.init_sam_page()

            if self.srvsvc_initialized():
                if not self.srvsvc_window.connected():
                    self.srvsvc_window.on_connect_item_activate(None,
                                                       **self.connection_args)
            else:
                self.init_srvsvc_page()
                self.srvsvc_window.hide()

            if self.regedit_initialized():
                if not self.regedit_window.connected():
                    self.regedit_window.on_connect_item_activate(None,
                                                       **self.connection_args)
            else:
                self.init_regedit_page()

            if self.svcctl_initialized():
                if not self.svcctl_window.connected():
                    self.svcctl_window.on_connect_item_activate(None,
                                                       **self.connection_args)
            else:
                self.init_svcctl_page()

            if self.crontab_initialized():
                if not self.crontab_window.connected():
                    self.crontab_window.on_connect_item_activate(None,
                                                       **self.connection_args)
            else:
                self.init_crontab_page()

        else:
            if self.run_connect_all_dialog():
                self.on_connect_all_button_clicked(None)

    def on_disconnect_all_button_clicked(self, widget):
        if self.sam_initialized():
            self.sam_window.on_disconnect_item_activate(None)
        if self.srvsvc_initialized():
            self.srvsvc_window.on_disconnect_item_activate(None)
        if self.regedit_initialized():
            self.regedit_window.on_disconnect_item_activate(None)
        if self.svcctl_initialized():
            self.svcctl_window.on_disconnect_item_activate(None)
        if self.crontab_initialized():
            self.crontab_window.on_disconnect_item_activate(None)
        self.update_sensitivity()

    def on_connection_info_item_activate(self, widget):
        #TODO: display connection info (via a dialog or custom window?)
        self.push_status_message("This is not implemented yet!")
        pass

    def on_clear_log_activate(self, widget):
        self.messages_textview.get_buffer().set_text("")


    def on_about_item_activate(self, widget):
        dialog = AboutDialog(
                             "Main",
                             "A tool to display other utilities in a simple, unified window.",
                             None
                             )
        dialog.run()
        dialog.hide()


    def on_quit_item_activate(self, widget):
        Gtk.main_quit()

#************ END OF CLASS ***************

def PrintUseage():
    print "Usage: %s [OPTIONS]" % (str(os.path.split(__file__)[-1]))
    print "All options are optional. The user will be queried for additional information if needed.\n"
    print "  -s  --server\t\tspecify the server to connect to."
    print "  -u  --user\t\tspecify the user."
    print "  -p  --password\tThe password for the user."
    print "  -t  --transport\tTransport type.\n\t\t\t\t0 for RPC, SMB, TCP/IP\n\t\t\t\t1 for RPC, TCP/IP\n\t\t\t\t2 for localhost."
    print "  -c  --connect-now\tSkip the connect dialog."

def ParseArgs(argv):
    arguments = {}

    try: #get arguments into a nicer format
        opts, args = getopt.getopt(argv, "chu:s:p:t:", ["help", "user=", "server=", "password=", "connect-now", "transport="])
    except getopt.GetoptError:
        PrintUseage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            PrintUseage()
            sys.exit(0)
        elif opt in ("-s", "--server"):
            arguments.update({"server":arg})
        elif opt in ("-u", "--user"):
            arguments.update({"username":arg})
        elif opt in ("-p", "--password"):
            arguments.update({"password":arg})
        elif opt in ("-t", "--transport"):
            arguments.update({"transport_type":int(arg)})
        elif opt in ("-c", "--connect-now"):
            arguments.update({"connect_now":True})
    return (arguments)


if __name__ == "__main__":
    arguments = ParseArgs(sys.argv[1:])
    GLib.threads_init()
    Gdk.threads_init()
    main_window = SambaUtilities(arguments)
    sys.stdout = main_window #redirect print statements to the write() function of this class
    Gtk.main()

