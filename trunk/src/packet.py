"""File documentation
"""

import json
import logging
import socket
import base64

class Packet():
	"""Class documentation
	"""
	
	address_key_dict = None  #dict to keep track of encryption keys for addresses.  Static across all packets.  Must be thread safe.
	
	def __init__(self):
		self.json_RPC_object = None  #formatted something like this: {"jsonrpc": "2.0", "method": "subtract","params": [version#, {congestion object}, [method_param_1, method_param_2 ...]], "id": 3}
		
		self.from_address = None  #packet header info when packet is received
		self.to_address = None  #info on where to send this packet
		self.binary_blob = None  #blob of binary data to append to json_RPC_object
		#self.congestion_object = None  #JSON object storing congestion info.  eg. {transmit timestamp, packet_number}
		self.raw_bytes = None
		self.send_time = None
		self.recv_time = None
		
	def __str__(self):
		text = '\n'
		text += '=========Printing details of packet object=========\n'
		text += "json_RPC_object: %s\n" %(self.json_RPC_object)
		if self.from_address == None:
			text += 'from_address: None\n'
		else:
			text += 'from_address: (' + str(self.from_address[0]) + ':' + str(self.from_address[1]) + ')\n' 
		if self.to_address == None:
			text += 'to_address: None\n'
		else:
			text += 'to_address: (' + str(self.to_address[0]) + ':' + str(self.to_address[1]) + ')\n' 
		if self.binary_blob == None:
			text += 'b64 binary_blob: None\n'
		else:
			text += "b64 binary_blob: %s\n" %(base64.b64encode(self.binary_blob))
		#print "congestion_object: %s" %(self.congestion_object)
		if self.raw_bytes == None:
			text += "b64 raw_bytes: None\n"
		else:
			text += "b64 raw_bytes: %s\n" %(base64.b64encode(self.raw_bytes))
		text += '------------------------------------------------------\n'
		#print text
		return text

		
	def display(self):
		print str(self)
	
	
	def read_from_socket(self, sock_fd):
		"""Reads the given socket and populates member variables.
		Socket must be readable.
		"""
		logging.debug('reading from socket')
		sock = socket.fromfd(sock_fd, socket.AF_INET, socket.SOCK_DGRAM)
		(self.raw_bytes, self.from_address) = sock.recvfrom(65507)  #65507 is max UDP packet size for IPv4
		
	
	
	def write_to_socket(self, sock):
		"""Writes state info to socket.
		"""
		logging.debug('writing packet to socket: %s'%(self))
		bytes_sent = sock.sendto(self.raw_bytes, self.to_address)
		#logging.debug('packet JSON: %s', self.json_RPC_object)
		#logging.debug('bytes to send: %d, bytes sent: %d', len(self.raw_bytes), bytes_sent)
		#logging.debug(select.select([],[sock],[]))
		if bytes_sent != len(self.raw_bytes):
			logging.info('bytes not written to socket')	
		
		
	def deserialize(self):
		"""Converts raw bytes read from packet to useful python objects.
		This is the deserialization format:
		{"jsonrpc": "2.0", "method": "subtract","params": [version#, {congestion object}, method_param_1, method_param_2 ...], "id": 3} binary_payload
		{version #, {JSON congestion object}, {JSON RPC object}} binary_payload
		"""
		#logging.debug('deserializing: %s', self.raw_bytes)
		last_curly = self.find_closing_curly(self.raw_bytes)
		self.json_RPC_object = json.loads(self.raw_bytes[:last_curly])
		#version = main_json_dict['version']
		#self.congestion_object = main_json_dict['congestion'] 
		#self.json_RPC_object = main_json_dict['json']
		self.binary_blob = self.raw_bytes[last_curly:]
		logging.debug('deserialized: %s' %(self))
		
		
	
	def serialize(self):
		"""
		"""
		self.raw_bytes = json.dumps(self.json_RPC_object)
		if self.binary_blob!=None:
			self.raw_bytes += self.binary_blob
		
		
		
		
	def decrypt(self):
		"""Decrypts packet
		"""
		pass
	
	
	def encrypt(self):
		"""Encrypts packet
		"""
		pass 
		
		
	def find_closing_curly(self, s):
		"""finds the end of a JSON object denoted by a final closing curly bracket '}'
		Returns the index of the bracket.
		"""
		#logging.debug('s: %s', s)
		levels=1
		i=1
		len_s = len(s)
		while(levels>0 and i<len_s):
			if s[i]=='{':
				levels+=1
			elif s[i]=='}':
				levels-=1
			i+=1
		#logging.debug('i: %d', i)
		return i
		
		
		
		
		
		
		
		
		