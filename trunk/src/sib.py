
from commit_blob import commit_blob
from socketserver import SocketServer
from packetprepostprocessor import PacketPrePostprocessor
from jsonserver import JSONServer
from congest import CongestionManager

from multiprocessing import Queue, Manager
import logging
import time
import random
import json
import socket
import os


def cmd(method_name, params, to, blocking = False, congest=None, ver=1.0, frm=None, rpc_id=None, TTL=None):
	logging.debug('[method_name, params, to, blocking, congest, ver, frm, rpc_id, TTL]: %s' %([method_name, params, to, blocking, congest, ver, frm, rpc_id, TTL]))
	if rpc_id==None:
		rpc_id=random.randint(1,10000)
	msg_dict = dict()
	msg_dict.update({'jsonrpc':2.0})
	msg_dict.update({'method':method_name})
	msg_dict.update({'params':[ver, congest, params]})
	msg_dict.update({'id':rpc_id})
	logging.debug('msg_dict: %s' %(msg_dict))
	rpc_msg = json.dumps(msg_dict)
	s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	if frm!= None:
		s2.bind(('',frm))
	s2.setblocking(0)
	s2.sendto(rpc_msg, to)
	logging.debug('Sent msg: %s, to: %s, from: %s, rpcID: %d' %(rpc_msg, to, frm, rpc_id))
	
	ret_msg = None
	if blocking:
		ret_msg = s2.recv(65507)  #65507 is max UDP packet size for IPv4
	s2.close()
	return ret_msg


def print_all_commits(key, my_storage):
	cb = commit_blob()
	for root, dirs, files in os.walk(my_storage):
		for name in files:
			if name[0]=='_':  #commit filenames start with '_'
				cb.load(key, root, name)
				cb.display()
				
				
				


class SIB():
	"""Share Is Beautiful
	"""
	
	
	
	def __init__(self):
		logging.basicConfig(
				filename='SIB.log',
				format='%(asctime)s | %(process)d | %(processName)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s',
				level=logging.DEBUG)
		
		#shared objects for inter-process communication
		#TODO: WTH is there so much shared state?
		self.raw_in_queue = Queue()
		self.json_call_queue = Queue()
		self.json_out_queue = Queue()
		self.manager = Manager()
		self.json_response_dict = self.manager.dict()
		#self.listen_sockets = self.manager.list()
		self.new_sockets = Queue()
		self.congest_sent_queue = Queue()
		self.congest_recv_queue = Queue()
		self.congest_connect_state = self.manager.dict()
		
		self.ss = SocketServer()
		#self.ss.listen_sockets = self.listen_sockets
		self.ss.new_sockets = self.new_sockets
		self.ss.raw_in_queue = self.raw_in_queue
		
		self.pp = PacketPrePostprocessor()
		self.pp.raw_in_queue = self.raw_in_queue
		self.pp.json_queue = self.json_call_queue
		self.pp.json_response_dict = self.json_response_dict
		self.pp.json_out_queue = self.json_out_queue
		self.pp.congest_sent_queue = self.congest_sent_queue
		self.pp.congest_recv_queue = self.congest_recv_queue

		self.js = JSONServer()
		self.js.json_call_queue = self.json_call_queue
		self.js.json_response_dict = self.json_response_dict
		self.js.json_out_queue = self.json_out_queue
		self.js.congest_connect_state = self.congest_connect_state
		
		self.congest = CongestionManager()
		self.congest.shared_sent_queue = self.congest_sent_queue
		self.congest.shared_recv_queue = self.congest_recv_queue
		self.congest.connect_summary = self.congest_connect_state
		
		

	def display(self):
		"""Prints contents of SIB for debug purposes.
		"""
		#self.raw_in_queue = Queue()
		#self.json_call_queue = Queue()
		#self.json_out_queue = Queue()
		#self.json_response_dict = self.manager.dict()
		print'=========Printing details of SIB object========='
		print "raw_in_queue size: %s" %(self.raw_in_queue.qsize())
		print "json_call_queue size: %s" %(self.json_call_queue.qsize())
		print "json_out_queuesize: %s" %(self.json_out_queue.qsize())
		print "json_response_dict  size: %s" %(len(self.json_response_dict))
		print'------------------------------------------------------'
		
		
	
	def run_once(self):
		self.ss.serve_once()
		self.pp.run_pre_once()
		self.js.serve_once()
		self.pp.run_post_once()
		
	
		
	def run_forever(self):
		logging.info('serving forever')
		self.ss_proc = self.ss.serve_forever_process()
		self.pp.start_pre_pool(2)
		self.js.start_pool(2)
		self.pp.start_post_pool(2)
		self.congest_proc = self.congest.serve_forever_process()
		
		
	def terminate(self):
		logging.info('terminating all processes')
		self.ss_proc.terminate()
		self.congest_proc.terminate()
		self.pp.terminate()
		self.js.terminate()
	
	
	def process_for(self, t):
		"""Continue processing for t seconds.
		"""
		end = time.time()+t
		while(time.time() < end):
			self.process_all()
		
	
		
	def process_all(self):
		"""Continue processing packets if they are available.
		If there is nothing to process, wait 0.01 seconds for
		something to process.  If nothing shows up then return.
		"""
		logging.debug('starting process all')
		packets_processed = 0
		should_wait=True
		while(True):
			did_work=False
			if (self.ss.serve_once()):
				did_work=True
			if (self.pp.run_pre_once()):
				did_work=True
			if (self.js.serve_once()):
				packets_processed += 1
				did_work=True
			if (self.pp.run_post_once()):
				did_work=True
			self.congest.run_once()
			if did_work:
				should_wait=True
				continue
			if not should_wait:
				break
			time.sleep(0.01)
			should_wait=False
		logging.debug('packets processed: %d', packets_processed)
		
		



		
		

		
		
		
		
		
		
		
		
		