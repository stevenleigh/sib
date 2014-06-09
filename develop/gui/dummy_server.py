#!/usr/bin/python

# Echo server program
import json
import socket
import socketio

CONFIG_FILE=".sib_config.JSON"

# ------ COMMANDS ------ #
GET_CONFIG 	= "get_conf"
SET_CONFIG	= "set_conf"

HOST = 'localhost'                  # Symbolic name meaning all available interfaces
PORT = 46781              			# Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)

while True:
	conn, addr = s.accept()
	print('Connected by', addr)

	settings_file = open(CONFIG_FILE, 'r')
	contents = settings_file.read()
	settings_file.close()

	config = json.loads(contents)

	while True:
		data = socketio.receive(conn)
		if not data:
			break
		print("received:{0}".format(data))
		if data == GET_CONFIG:
			print("received send all config command")
			socketio.send(conn, contents)
		if data == SET_CONFIG:
			print("received set config command")
			page = socketio.receive(conn)
			key = socketio.receive(conn)
			value = socketio.receive(conn)
			print("Received page:{0} key:{1} value:{2}".format(page, key, value))
			config['SETTINGS'][page][key] = json.loads(value)
			settings_file = open(CONFIG_FILE, 'w')
			settings_file.write(json.dumps(config, sort_keys=True, indent=4, separators=(',', ': ')))
			settings_file.close()

	conn.close()