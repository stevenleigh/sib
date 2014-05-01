

from packet import Packet

import socket
import copy
import time
import multiprocessing
from multiprocessing import Process
import logging


class PacketPrePostprocessor():
	"""Reads packets from raw_in_queue.  Does any pre-processing
	necessary on packets (decrypting, formatting into JSON, etc.)
	and pushes packets to json_queue.
	"""
	
	
	def __init__(self):
		self.process_pool_pre = []  #make processor pool here
		self.process_pool_post = []  #make processor pool here
		self.raw_in_queue = None
		self.json_queue = None
		self.json_out_queue = None
		self.json_response_dict = None
		self.congest_sent_queue = None
		self.congest_recv_queue = None
		
	
	
	def start_pre_pool(self, processes=None):
		if processes == None:
			processes = multiprocessing.cpu_count()
		
		for i in range(0,processes):
			proc = Process(target=self.run_pre_forever)
			proc.start()
			self.process_pool_pre.append(proc)
	
	
			
	def start_post_pool(self, processes=None):
		if processes == None:
			processes = multiprocessing.cpu_count()
			
		for i in range(0,processes):
			proc = Process(target=self.run_post_forever)
			proc.start()
			self.process_pool_post.append(proc)
			
			
		
	def terminate(self):
		for p in self.process_pool_pre:
			p.terminate()
		for p in self.process_pool_post:
			p.terminate()
	
	
	
	def run_pre_forever(self):
		"""This method would run in every process in the process pool.
		"""
		logging.info('running packet preprocessor forever')
		while True:
			if not self.run_pre_once():
				time.sleep(0.1)
			
			
			
	def run_pre_once(self):
		if self.raw_in_queue.empty():
			#logging.debug('raw_in_queue empty')
			return False
		p = self.raw_in_queue.get()  #blocks here until an item is put on the queue  @TODO: catch the exception here
		p.decrypt()
		p.deserialize()
		#logging.debug('packet in raw_in_queue: %s'%(p))
		if 'method' in p.json_RPC_object:
			self.json_queue.put(p)
		elif 'result' in p.json_RPC_object:
			rpc_id = p.json_RPC_object.get('id')
			p_copy = copy.deepcopy(p)
			self.json_response_dict.update({rpc_id: p})
			self.congest_recv_queue.put(p_copy)
			
		else:
			#@TODO:  should never happen.  Means malformatted packet.
			logging.error('malformatted JSONRPC packet')
			pass
		return True
		
		
	def run_post_forever(self):
		"""This method would run in every process in the process pool.
		"""
		logging.info('running packet postprocessor forever')
		while True:
			if not self.run_post_once():
				time.sleep(0.1)
			
			
			
	def run_post_once(self):
		if self.json_out_queue.empty():
			return False
		p = self.json_out_queue.get()  #blocks here until an item is put on the queue  @TODO: catch the exception here
		p.serialize()
		p.encrypt()
		
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		p.write_to_socket(s)
		
		p.send_time = time.time()
		self.congest_sent_queue.put(p)
		return True
			
	
	