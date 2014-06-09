#!/usr/bin/python

import sys
import fcntl
import logging
import socket
import socketio
import json

# ------ MISC ------ #

DEBUG = True
lock_file		= 0
UI_LK_FILE 		= ".ui_lk"
SETTINGS_FILE 	= '.sib_settings.JSON'

# ------ COMMANDS ------ #
GET_CONFIG 	= "get_conf"

def check_singleton():
	global lock_file
	try:
		lock_file = open(UI_LK_FILE, "w+")
		fcntl.lockf(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

		return True
	except Exception as e:
		logging.error("Failed aquire exclusive lock on file: " + UI_LK_FILE)

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

class Model():
	conn = -1
	config = -1

	def __init__(self, settings):
		if DEBUG:
			print("Model constructor init")
		logging.basicConfig(level=settings['logging_level'])

		self.connect_to_sib('localhost', settings['port'])
		self.load_all_config()
		self.disconnect_from_sib()

	def connect_to_sib(self, domain, port):
		if DEBUG:
			print("Connecting to SIB, domain:{0}, port:{1}".format(domain, port))
		self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.conn.connect((domain, port))

	def disconnect_from_sib(self):
		if DEBUG:
			print("Diconnecting from SIB")
		self.conn.close()

	def load_all_config(self):
		if DEBUG:
			print("Loading SIB configuration")
		socketio.send(self.conn, GET_CONFIG)
		config_str = socketio.receive(self.conn)
		if DEBUG:
			print("-------------------------------------------------------------------")
			print(config_str)
			print("-------------------------------------------------------------------")
		config = json.loads(config_str)
		

if __name__ == '__main__':
	isSingleton = check_singleton()
	if isSingleton == False:
		logging.info("Detected another instance of SIB gui running, exiting")
		sys.exit(0)
	settings = load_settings()
	model = Model(settings)
	