

import socket
from multiprocessing import Process
import time
from blob import blob
import json
import os
from peer_manager import peer_manager


class network_manager():
	command_port = None
	command_socket = None
	storage_directory=''
	in_buff = bytearray()
	message_type=None
	
	pm = peer_manager
		
		
	def __init__(self, pm):
		self.pm=pm
		
		
	
	def run(self):
		print'server running'
		self.listen()
		self.read_socket_data()
		#self.read_network_data()
	
	
	
	def close(self):
		self.command_socket.close()
	
	
	
	def listen(self):
		#listen for a connection on this port
		self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.command_socket.bind(('', self.command_port))  #listen for any IP on the given port
		print 'Listening...'
		self.command_socket.listen(5)
		self.command_socket, addr = self.command_socket.accept()
		print 'Connected by', addr
		time.sleep(0.1)  #wait for client socket to do something
		
		
		
	def read_socket_data(self):
		
		#Header format:
		#first 4 bytes are base 10 length of proceeding JSON object
		#JSON formatted list.
		#first list element: string, message type
		#second list element: int, length of message following JSON object
		#third list element: another list containing message specific arguments
		#This point is the end of the JSON object.  Anything after is the message 
		#	and can be in any format (not necessarily JSON).
		
		while True:
			while(len(self.in_buff)<4):
				self.in_buff += self.wait_for_new_data()
			#if(len(self.in_buff)<4):
			#	continue
			header_len = int(self.in_buff[:4])
			self.in_buff = self.in_buff[4:]
			print 'Message header length: %d' %(header_len)
			while(len(self.in_buff)<header_len):  #wait for full header to transfer
				self.in_buff += self.wait_for_new_data()
			[msg_type, msg_len, msg_args] = json.loads((self.in_buff[:header_len]).decode('utf-8'))
			print'Message header: %s' %((self.in_buff[:header_len]).decode('utf-8'))
			self.in_buff = self.in_buff[header_len:]
			
			if msg_len>0:
				while(len(self.in_buff)<msg_len):  #wait for full message to arrive
					self.in_buff += self.wait_for_new_data()
				msg = self.in_buff[:msg_len]
				self.in_buff = self.in_buff[msg_len:]
			
			self.pm.process_network_msg(msg_type, msg_args, msg)			
				
			
	
	
	def wait_for_new_data(self):
		print 'waiting for new socket data'
		while True:
			new_bytes=self.command_socket.recv(1<<15)
			if len(new_bytes) > 0:
				#print 'new bytes: %s' %(new_bytes)
				return new_bytes
			time.sleep(0.1)  #poll 10 times per sec			
	
	
	
	def connect(self, host, port):
		#initiate a connection to this IP and port
		self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.command_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.command_socket.connect((host, port))
		
		
		
	def send_msg(self, msg_type, msg_args, msg_body=None):
		msg_header = json.dumps([msg_type, len(msg_body), msg_args])
		full_msg_header = '%4d%s' %(len(msg_header), msg_header)
		
		self.command_socket.sendall(full_msg_header)
		if msg_body!=None:
			self.command_socket.sendall(msg_body)
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	