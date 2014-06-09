#!/usr/bin/python

# Echo server program
import socket
import socketio

CONFIG_FILE=".sib_config.JSON"

# ------ COMMANDS ------ #
GET_CONFIG 	= "get_conf"

HOST = 'localhost'                  # Symbolic name meaning all available interfaces
PORT = 46781              			# Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print('Connected by', addr)

settings_file = open(CONFIG_FILE, 'r')
contents = settings_file.read()
contents_length = len(contents)
print("Length: {0}".format(contents_length))

while True:
	data = socketio.receive(conn)
	if not data:
		break
	print("received:{0}".format(data))
	if data == GET_CONFIG:
		print("received send all config command")
		socketio.send(conn, contents)

conn.close()