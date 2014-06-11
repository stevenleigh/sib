#!/usr/bin/python

import sys
import threading
import fcntl
import logging
import socket
import json

import socketio

# ------ MISC ------ #

DEBUG = True
lock_file		= 0
UI_LK_FILE 		= ".ui_lk"
SETTINGS_FILE 	= '.sib_settings.JSON'

# ------ COMMANDS ------ #
GET_CONFIG 	= "get_conf"
SET_CONFIG	= "set_conf"

def check_singleton():
	global lock_file
	try:
		lock_file = open(UI_LK_FILE, "w+")
		fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

		return True
	except Exception as e:
		logging.error("Failed to aquire exclusive lock on file: " + UI_LK_FILE)

		return False


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

class updateThread(threading.Thread):
	def __init__(self, domain, port, page, key, value):
		threading.Thread.__init__(self)
		self.domain = domain
		self.port = port
		self.page = page
		self.key = key
		self.value = value
	def run(self):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: Updating sib server with page:{1} key:{2} value:{3}".format(t, self.page, self.key, self.value))
		conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		conn.connect((self.domain, self.port))
		socketio.send(conn, SET_CONFIG)
		socketio.send(conn, self.page)
		socketio.send(conn, self.key)
		socketio.send(conn, json.dumps(self.value))
		conn.close()

class Model(object):
	conn = -1
	config = -1

	def __init__(self, settings):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: Model constructor init".format(t))
		logging.basicConfig(level=settings['logging_level'])

		self.connect_to_sib('localhost', settings['port'])
		self.load_all_config()
		self.disconnect_from_sib()

	def connect_to_sib(self, domain, port):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: Connecting to SIB, domain:{1} port:{2}".format(t, domain, port))
		self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.conn.connect((domain, port))

	def disconnect_from_sib(self):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: Diconnecting from SIB".format(t))
		self.conn.close()

	def load_all_config(self):
		if DEBUG:
			t = threading.current_thread();
			print("{0}: Loading SIB configuration".format(t))
		socketio.send(self.conn, GET_CONFIG)
		config_str = socketio.receive(self.conn)
		if DEBUG:
			print("-------------------------------------------------------------------")
			print(config_str)
			print("-------------------------------------------------------------------")
		self.config = json.loads(config_str)
	
	def get_config(self, page, key):
		try:
			value = self.config['SETTINGS'][page][key]
			if DEBUG:
				t = threading.current_thread();
				print("{0}: Config for page:{1} key:{2} is {3}".format(t, page, key, value))
			
			return value
		except Exception as e:
			logging.error("Failed to retrieve value for page:{1} key:{2}".format(t, page, key))
			
			return None

	def set_config(self, page, key, value):
		try:
			tmp = self.config['SETTINGS'][page]
		except Exception as e:
			if DEBUG:
				t = threading.current_thread();
				print("{0}: Page {1} does not exist in config".format(t, page))
			return
		try:
			tmp = self.config['SETTINGS'][page][key]
		except Exception as e:
			if DEBUG:
				t = threading.current_thread();
				print("{0}: Key {1} of page {2} does not exist in config".format(t, key, page))
			return
		
		key_type = type(self.config['SETTINGS'][page][key])
		value_type = type(value)
		if value_type != key_type:
			if DEBUG:
				t = threading.current_thread();
				print("{0}: Failed to set value={1} for page:{2} key:{3}: TypeError".format(t, value, page, key))
			return
		
		self.config['SETTINGS'][page][key] = value
		if DEBUG:
			t = threading.current_thread();
			print("{0}: Config for page:{1} key:{2} is {3}".format(t, page, key, value))
		thread = updateThread('localhost', settings['port'], page, key, value)
		thread.start()
		
def main():
	pass

if __name__ == '__main__':
	isSingleton = check_singleton()
	if isSingleton == False:
		logging.info("Detected another instance of SIB gui running, exiting")
		sys.exit(0)
	settings = load_settings()
	model = Model(settings)
	val = model.get_config('GENERAL', 'Launch_on_startup')
	model.set_config('UNTRUSTED_PEERS', 'Cap_untrusted_peers', True)
	model.set_config('UNTRUSTED_PEERS', 'Untrusted_peers_cap', 400)
