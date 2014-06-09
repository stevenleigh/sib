#!/usr/bin/python

import socket

# ------ PACKET STRUCTURE ------ #
#
# L<msg_len>\r
# <message>
#
# For example :
#
# L30\r
# This is a message of length 30 

HEADER_MAX_LEN = 18

def send(conn, data):
	data_len = len(data)
	header = "L" + str(data_len) + "\r"
	if len(header) > HEADER_MAX_LEN:
		raise RuntimeError("Attempted to create packet with header longer than HEADER_MAX_LEN:".format(HEADER_MAX_LEN))
	conn.sendall(header.encode())
	conn.sendall(data.encode())

def receive(conn):
	head = conn.recv(1).decode()
	if not head:
		return None
	if head != "L":
		raise RuntimeError("Malformed packet detected")
	
	bytes_recd = 0
	p_len = ""
	while True:
		c = conn.recv(1).decode()
		if c == '\r':
			break
		p_len += c
		bytes_recd += 1
		if bytes_recd >= HEADER_MAX_LEN:
			raise RuntimeError("Malformed packet header detected")
	
	bytes_recd = 0
	data = ""
	while bytes_recd < int(p_len):
		chunk = conn.recv(min(int(p_len) - bytes_recd, 4096)).decode()
		if chunk == '':
			raise RuntimeError("Socket connection broken")
		data += chunk
		bytes_recd = bytes_recd + len(chunk)
	return data