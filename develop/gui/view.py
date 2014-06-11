#!/usr/bin/python

from gi.repository import Gtk as gtk
import threading
import logging
import json

import model

# ------ UI ------ #

WINDOW_TITLE					= "SIB Preferences"

GENERAL_TAB_STR					= "General"
STORAGE_TAB_STR					= "Storage"

LAUNCH_ON_STARTUP_STR			= "Launch SIB on startup"
ENABLE_WEB_ACCESS_STR 			= "Enable web access"
ENABLE_AUTO_BACKUP_AND_SYNC_STR	= "Enable automatic backup and sync"
ENABLE_NOTIFICATIONS_STR 		= "Enable notifications"
NOTIFY_SYNCD_STR				= "Notify when a file/folder is syncd amongst trusted devices"
NOTIFY_BACKUP_STR				= "Notify when a file/folder backup is complete"
NOTIFY_FULL_STR					= "Notify when allocated peer storage is close to full"

# ------ MISC ------ #

DEBUG = True
SETTINGS_FILE 	= '.sib_settings.JSON'

def load_settings():
	try:
		settings_file = open(SETTINGS_FILE, 'r')
		contents = settings_file.read()

		return json.loads(contents)
	except Exception as e:
		logging.warning("Failed to parse settings file, using default settings")
		default_settings = load_default_settings()

		return default_settings;	

def load_default_settings():
	return json.loads('{							\
							"logging_level" : 20, 	\
							"port" 			: 46781	\
						}')

class NoteBookView(gtk.Window):
	def __init__(self, settings):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: NoteBookView constructor init".format(t))
		logging.basicConfig(level=settings['logging_level'])

		self.init_view()

	def init_view(self):
		gtk.Window.__init__(self, title=WINDOW_TITLE)

		notebook = gtk.Notebook()
		notebook.set_border_width(10)
		self.add(notebook)

		generalView = GeneralView()
		notebook.append_page(generalView, generalView.label)
		storageView = StorageView()
		notebook.append_page(storageView, storageView.label)

class GeneralView(gtk.Frame):
	def __init__(self):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: View constructor init".format(t))

		self.init_label()
		self.init_view()

	def init_view(self):
		gtk.Frame.__init__(self, shadow_type=0)

		self.set_border_width(20)
		grid = gtk.Grid(orientation=gtk.Orientation.VERTICAL, row_spacing=8)
		self.add(grid)

		self.check_launch_sib_on_startup_checkbox = gtk.CheckButton(LAUNCH_ON_STARTUP_STR)
		self.enable_web_access_checkbox = gtk.CheckButton(ENABLE_WEB_ACCESS_STR)
		self.enable_auto_back_sync_checkbox = gtk.CheckButton(ENABLE_AUTO_BACKUP_AND_SYNC_STR)
		self.enable_notifications_checkbox = gtk.CheckButton(ENABLE_NOTIFICATIONS_STR)

		self.alignment_notify_syncd = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
		self.alignment_notify_syncd.set_padding(0, 0, 20, 0)
		self.alignment_notify_syncd.add(gtk.CheckButton(NOTIFY_SYNCD_STR))
		self.alignment_notify_backup = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
		self.alignment_notify_backup.set_padding(0, 0, 20, 0)
		self.alignment_notify_backup.add(gtk.CheckButton(NOTIFY_BACKUP_STR))
		self.alignment_notify_full = gtk.Alignment(xalign=0.0, yalign=0.0, xscale=0.0, yscale=0.0)
		self.alignment_notify_full.set_padding(0, 0, 20, 0)
		self.alignment_notify_full.add(gtk.CheckButton(NOTIFY_FULL_STR))

		grid.add(self.check_launch_sib_on_startup_checkbox)
		grid.add(self.enable_web_access_checkbox)
		grid.add(self.enable_auto_back_sync_checkbox)
		grid.add(self.enable_notifications_checkbox)
		grid.add(self.alignment_notify_syncd)
		grid.add(self.alignment_notify_backup)
		grid.add(self.alignment_notify_full)

		# FOR CONTROLLER?
		self.enable_notifications_checkbox.connect("clicked", self.enable_notifications_changed)

		self.set_notification_checkbox_state()

	def init_label(self):
		self.label = gtk.Label(GENERAL_TAB_STR)

	def enable_notifications_changed(self, event):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: Enable notifications click event".format(t))

		self.set_notification_checkbox_state()

	def set_notification_checkbox_state(self):
		if self.enable_notifications_checkbox.get_active():
			self.alignment_notify_syncd.set_sensitive(True)
			self.alignment_notify_backup.set_sensitive(True)
			self.alignment_notify_full.set_sensitive(True)
		else:
			self.alignment_notify_syncd.set_sensitive(False)
			self.alignment_notify_backup.set_sensitive(False)
			self.alignment_notify_full.set_sensitive(False)

class StorageView(gtk.Frame):
	def __init__(self):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: View constructor init".format(t))

		self.init_label()
		self.init_view()

	def init_view(self):
		gtk.Frame.__init__(self, shadow_type=0)

		self.set_border_width(20)
		grid = gtk.Grid(orientation=gtk.Orientation.VERTICAL, row_spacing=6)
		self.add(grid)

	def init_label(self):
		self.label = gtk.Label(STORAGE_TAB_STR)

def main():
	settings = load_settings()
	view = NoteBookView(settings)
	view.connect("delete-event", gtk.main_quit)
	view.show_all()
	gtk.main()

if __name__ == '__main__':
	main()