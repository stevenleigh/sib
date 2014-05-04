

from packet import Packet
from autosync import AutoSync
from watchdog.observers import Observer
from local_blob_manager import local_blob_manager

import logging
import os
import time
import multiprocessing
from multiprocessing import Process, Manager
import random
from Crypto import Random

class JSONServer():
	

	def __init__(self):
		self.json_call_queue = None
		self.json_response_dict = None  #JSON responses are pushed here indexed by rpc ID
		self.json_out_queue = None  #packets of JSON responses are pushed here awaiting postprocessing and transmission
		self.process_pool = []
		self.congest_connect_state = None
		self.storage_directory = ""
		self.a_s_list = []  #list of autoSync objects
		self.command_port = None
		
		#Objects shared across processes
		self.my_machine_ID = ""
		self.manager = Manager()
		self.share_machine_dict = self.manager.dict()  #maps share IDs to machine IDs
		#self.share_key_dict = self.manager.dict()  #maps share IDs to corresponding public keys (or certificates?)  #TODO: implement
		self.machine_address_dict = self.manager.dict()  #maps machine IDs to url (IP:port)
		self.autosync_share_working_directory_dict = self.manager.dict()  #lists all autosynced working directories for a given share 
		
		#register JSONRPC functions
		self.method_dict = dict()  #function pointers to registered JSONRPC functions
		self.register_func('ping', self.ping)
		self.register_func('get_file', self.get_file)
		self.register_func('save_file_block', self.save_file_block)
		self.register_func('update_machine_address', self.update_machine_address)
		self.register_func('add_share_to_machine', self.add_share_to_machine)
		self.register_func('has_file', self.has_file)
		self.register_func('push_update_to_peer', self.push_update_to_peer)
		self.register_func('register_auto_sync', self.register_auto_sync)
		self.register_func('commit', self.commit)
		self.register_func('restore', self.restore)
		self.register_func('sync_new_commit', self.sync_new_commit)
		
	
	def start_pool(self, processes=None):
		if processes == None:
			processes = multiprocessing.cpu_count()
			
		for i in range(0,processes):
			proc = Process(target=self.serve_forever)
			proc.start()
			self.process_pool.append(proc)
		logging.info('JSONServer pool %d processes started' %(processes))
			
			
	def terminate(self):
		for p in self.process_pool:
			p.terminate()
			

	def serve_forever(self):
		Random.atfork()
		while True:
			if not self.serve_once():
				time.sleep(0.1)  #if no work was done, poll 10 times per sec
			
			
	def serve_once(self):
		if self.json_call_queue.empty():
			return False
		p_call = self.json_call_queue.get()  #block here
		name = p_call.json_RPC_object["method"]
		params = p_call.json_RPC_object["params"]
		rpc_id = p_call.json_RPC_object.get("id")
		logging.debug('JSONRPC call.  self.my_machine_ID: %s, method: %s, params: %s, rpc_id: %s, packet: %s'%(self.my_machine_ID, name, params, rpc_id, p_call))
		if name not in self.method_dict:
			logging.error('JSONRPC method does not exist: ' %(name))
			return True
		p_response = self.method_dict[name](params, rpc_id, p_call)  #call JSONRPC function
		if rpc_id == None or p_response == None:  #don't respond if RPC notify
			return True
		self.json_out_queue.put(p_response)  #queue response
		return True
		
		
	
	def register_func(self, name, func):
		"""Register a JSONRPC function
		"""
		self.method_dict.update({name: func})
		

	
	#################################
	#public JSONRPC functions
	#################################
	
	def ping(self, params, rpc_id, packet):
		[ver, congest, args] = params
		[reply_machine_ID] = args
		logging.info('jsonrpc call. [reply_machine_ID]: %s' %(args))
		
		return_address = self.machine_address_dict[reply_machine_ID]
		packet.json_RPC_object = dict(jsonrpc="2.0", result="pong", id=rpc_id)
		packet.to_address = return_address
		return packet
	
	
	
	def get_file(self, params, rpc_id, packet):
		[ver, congest, args] = params
		[reply_machine_ID, share_ID, file_name] = args
		logging.info('jsonrpc call. [reply_machine_ID, share_ID, file_name]: %s' %(args))
		return_address = self.machine_address_dict[reply_machine_ID]
		
		#send ack
		packet.json_RPC_object = dict(jsonrpc="2.0", result=True, id=rpc_id)  #@TODO: send file size  #@TODO: send new rpc_id for file chuncks
		packet.to_address = return_address
		self.json_out_queue.put(packet)
		
		self.transfer_file(share_ID, file_name, return_address)
		
		
	
	def save_file_block(self, params, rpc_id, packet):
		"""Instructs peer to save this block of the file.  
		File blocks are always sent in sizes divisible by 64 bytes.
		The maximum size of a UDP packet has to be less than 512MB,
		so, accounting for the header info the maximum binary payload should
		be less than 380 bytes.  Bytes are sent in sets of 64 to reduce the
		accounting overhead.
		params: share_ID
				file_name
				file_offset (offset from beginning of file in multiples of 64 bytes)
		packet binary payload contains file block data
		"""
		[ver, congest, args] = params
		[reply_machine_ID, share_ID, file_name, file_offset] = args
		logging.info('jsonrpc call.  [reply_machine_ID, share_ID, file_name, file_offset]: %s' %(args))
		
		
		full_file_name = os.path.join(self.storage_directory, share_ID, file_name)
		fp = open(full_file_name,'ab')
		fp.seek(64*file_offset)
		fp.write(packet.binary_blob)
		fp.close()
		
		if rpc_id == None:
			return None
		
		packet.json_RPC_object = dict(jsonrpc="2.0", result=True, id=rpc_id)
		return_address = self.machine_address_dict[reply_machine_ID]
		packet.to_address = return_address
		packet.binary_blob = None
		return packet

	
	
	def update_machine_address(self, params, rpc_id, packet):
		[ver, congest, args] = params
		[machine_ID, url, port] = args
		self.machine_address_dict.update({machine_ID:(url,port)})
		logging.info('Machine address dict updated: %s' %(self.machine_address_dict))
		#TODO: packet response
		
		
	def add_share_to_machine(self, params, rpc_id, packet):  #TODO: needs to be validated by a certificate each call?
		[ver, congest, args] = params
		[share_ID, machine_ID] = args
		if not share_ID in self.share_machine_dict:
			new_m_ID = [machine_ID]
		else:
			new_m_ID = self.share_machine_dict[share_ID]
			new_m_ID.append(machine_ID)
		self.share_machine_dict.update({share_ID:new_m_ID})
		logging.info('Share %s added to machine %s' %(share_ID, machine_ID))
		if not (machine_ID == self.my_machine_ID):
			return
		if not os.path.exists(os.path.join(self.storage_directory, share_ID)):  #make local storage directories if necessary
			os.makedirs(os.path.join(self.storage_directory, share_ID))
			logging.info('New share on localhost: %s' %(share_ID))
		#TODO: packet response
		
	
	def has_file(self, params, rpc_id, packet):
		"""
		Polls the peer to see if they have a specific file.  Returns true if they do.
		"""
		[ver, congest, args] = params
		[reply_machine_ID, share_ID, file_name] = args
		full_file_name = os.path.join(self.storage_directory, share_ID, file_name)
		
		response = os.path.isfile(full_file_name)
		
		packet.json_RPC_object = dict(jsonrpc="2.0", result=response, id=rpc_id)
		packet.to_address = self.machine_address_dict[reply_machine_ID]
		packet.binary_blob = None
		return packet

	
		
	
	def push_update_to_peer(self, params, rpc_id, packet):
		'''
		Loop through all blobs in storage directory and poll peer to see if they have it.
		If the peer does not have the file, send it to them.
		If machine_ID is None then send updates to all machines with share.
		If current_commit is not None, then a sync_new_commit is sent to each peer
		'''
		[ver, congest, args] = params
		[share_ID, machine_ID, current_commit] = args
		logging.info('Pushing update for %s to %s and updated to commit: %s' %(share_ID, machine_ID, current_commit))
		
		#Find all machines to push this update to
		to_transfer = dict()
		if machine_ID == None:
			logging.debug('dict: %s' %(self.share_machine_dict))
			if share_ID not in self.share_machine_dict:
				logging.error('No machines with this share')
				return
			logging.debug(self.share_machine_dict[share_ID])
			to_machines = self.share_machine_dict[share_ID]
		else:
			to_machines = [machine_ID]
		#delete my_machine_ID from to_machines
		if (self.my_machine_ID in to_machines):
			to_machines.remove(self.my_machine_ID)
		if len(to_machines)==0:
			logging.info('No other machines have this share.  Updates will not be pushed.')
			return
		logging.debug('Machines to push to: %s'%(to_machines))
		logging.debug('share path: %s' %(os.path.join(self.storage_directory, share_ID)))
		
		#send has_file query for all files.
		for root, dirs, files in os.walk(os.path.join(self.storage_directory, share_ID)):
			logging.debug('files: %s' %(files))
			for name in files:
				logging.debug('name: %s' %(name))
				for machine in to_machines:
					address = self.machine_address_dict[machine]
					rpc_id=random.randint(1,1000000) #TODO: rpc_id collisions could occur
					p = Packet()
					p.json_RPC_object = dict(jsonrpc="2.0", method="has_file", params=[1.0, None, [self.my_machine_ID, share_ID, name]], id=rpc_id)
					p.to_address = address
					self.send_block_choke(p, address, 3)
					to_transfer.update({rpc_id:[name, machine]})  #TODO: rpc_id collisions could occur
		
		logging.info('Sent has_file to %s for following files: %s' %(to_machines, to_transfer.keys()))
		time.sleep(5)  #wait for responses from peer
		
		logging.debug('json_response_dict: %s'%(self.json_response_dict))
		
		#send the file if the query comes back negative
		for item in to_transfer.items():
			[rpc_id, [name, machine]] = item
			if rpc_id not in self.json_response_dict:
				continue
			resp_packet = self.json_response_dict.pop(rpc_id)
			resp_value = resp_packet.json_RPC_object["result"]
			if not resp_value:
				#peer doesn't have this file, so send it
				self.transfer_file(share_ID, name, self.machine_address_dict[machine])
			del to_transfer[rpc_id]
		
		logging.info('No response for following files: %s' %(to_transfer.items()))
		
		if current_commit == None:
			return
		
		time.sleep(5)  #wait for responses from peer
		#Tell machines to update to current commit
		for machine in to_machines:
			address = self.machine_address_dict[machine]
			rpc_id=random.randint(1,1000000) #TODO: rpc_id collisions could occur
			p = Packet()
			p.json_RPC_object = dict(jsonrpc="2.0", method="sync_new_commit", params=[1.0, None, [current_commit, share_ID]], id=rpc_id)
			p.to_address = address
			self.send_block_choke(p, address, 3)
		
		
					
			
	def register_auto_sync(self, params, rpc_id, packet):
		"""Sets up a daemon to perform commits whenever files have been changed in a given directory.
		Commits are then pushed to all relevant machines.
		"""
		[ver, congest, args] = params
		[key, monitoring_directory, share_ID, user_name, min_update_interval] = args
		logging.debug('Initializing auto sync')
		logging.debug('[key, monitoring_directory, share_ID, user_name, min_update_interval]'%(args))
		
		a_s = AutoSync(key, monitoring_directory, self.storage_directory, share_ID, user_name, self.my_machine_ID, self.command_port, self.json_response_dict, min_update_interval)
		observer = Observer()
		observer.schedule(a_s, monitoring_directory, recursive=True)
		observer.start()
		self.a_s_list.append(a_s)  #maintain reference to autosync object so it isn't garbage collected
		
		working_directory_list = [monitoring_directory]
		if share_ID in self.autosync_share_working_directory_dict:
			working_directory_list.extend(self.autosync_share_working_directory_dict[share_ID])
			working_directory_list = list(set(working_directory_list))  #make list unique
		self.autosync_share_working_directory_dict.update({share_ID:working_directory_list})
	
	
	
	def commit(self, params, rpc_id, packet):
		"""
		"""
		#@TODO:  Ensure only authenticated users can access this command
		[ver, congest, args] = params
		[key, working_directory, share_ID, user_name, commit_msg, parent_commit_hash, other_parent_commit_hash] = args
		logging.debug('[key, working_directory, share_ID, user_name, commit_msg, parent_commit_hash, other_parent_commit_hash]: ' \
					%([key, working_directory, share_ID, user_name, commit_msg, parent_commit_hash, other_parent_commit_hash]))
					
		#@TODO:  If share_ID is None, look through all shares for the parent_commit_hash and use its share
		bm = local_blob_manager()
		commit_hash = bm.commit_directory(key, working_directory, os.path.join(self.storage_directory, share_ID), 
						user_name, commit_msg, parent_commit_hash, other_parent_commit_hash)
		
		#@TODO: packet response is to myself for it is stored in shared object json_response_dict for use with autosync.  Allow responding to other machines?
		return_address = ('localhost', self.command_port)
		packet.json_RPC_object = dict(jsonrpc="2.0", result=commit_hash, id=rpc_id)
		packet.to_address = return_address
		return packet
	
	
	
	def restore(self, params, rpc_id, packet):
		"""
		"""
		#@TODO:  Ensure only authenticated users can access this command
		[ver, congest, args] = params
		[key, working_directory, commit_hash] = args
		bm = local_blob_manager()
		#@TODO:  look for version already in working_directory and do differential update
		bm.restore_directory(key, working_directory, self.storage_directory, commit_hash)
		#@TODO: packet response?
		
		
	
	def sync_new_commit(self, params, rpc_id, packet):
		"""
		"""
		[ver, congest, args] = params
		[commit_hash, share_ID] = args
		logging.debug('[commit_hash, share_ID]: %s'%([commit_hash, share_ID]))
		key=b'Sixteen byte key'  #@TODO:  what do I do about this key?
		#@TODO:  this should sync by updating directory, not overwriting it.
		
		if share_ID not in self.autosync_share_working_directory_dict:
			logging.error('No autosync directories with share_ID: %s' %(share_ID))
			return
		
		if commit_hash[0] != '_':
			commit_hash = '_' + commit_hash
		
		full_file_name = os.path.join(self.storage_directory, share_ID, commit_hash)
		if not os.path.isfile(full_file_name):
			logging.error('commit does not exist.  path: %s' %(full_file_name))
			return
		
		bm = local_blob_manager()
		working_directory_list = self.autosync_share_working_directory_dict[share_ID]
		logging.debug('directories to sync: %s' %(working_directory_list))
		for working_directory in working_directory_list:
			file_list, mod_times, last_commit_hash = local_blob_manager.read_commit_meta(working_directory)
			logging.debug('parent sync hash: %s'%(last_commit_hash))
			if commit_hash == last_commit_hash:
				logging.debug('Working directory already contains desired commit')
				continue
			bm.restore_directory(key, working_directory, os.path.join(self.storage_directory, share_ID), commit_hash)
			
		
		
	
	
	#################################
	#JSONRPC helper functions
	#################################
	
	def transfer_file(self, share_ID, file_name, return_address, start_offset=0, end_offset=999999999999, block_skip=1):
		"""Sends a piece of a file to a peer in pieces.
		Initiated by JSONRPC: get_file()
		start_offset: start sending file from this offset
		end_offset: if this bytes is reached, send no more.
		block_skip: send a block, then skip this many blocks, then send the next etc.
		"""
		#continue to send all file blocks
		full_file_path = os.path.join(self.storage_directory, share_ID, file_name)
		f = open(full_file_path, 'rb')
		f.seek(start_offset)
		block_size = 5
		file_offset = start_offset
		
		logging.debug('start_offset: %d, end_offset: %d' %(start_offset, end_offset))
		
		while (file_offset < end_offset):  #@TODO: stop sending if given signal from return_address
			logging.debug('file_offset: %d' %(file_offset))
			block_bytes = f.read(64*block_size)
			if block_bytes == "":
				logging.debug('no bytes read from file')
				break
			p_out_block = Packet()
			p_out_block.json_RPC_object = dict(jsonrpc="2.0", method="save_file_block", params=[1.0, None, [self.my_machine_ID, share_ID, file_name, file_offset]], )  #id=rpc_id
			p_out_block.binary_blob = block_bytes
			p_out_block.to_address = return_address
			
			self.send_block_choke(p_out_block, return_address, 3)
			
			time.sleep(0.002)
			file_offset+=block_size
		
		logging.debug('finished file transfer')
		f.close()
		
	
		
	def send_block_choke(self, p, address, timeout=0):
		"""Attempt to queue packet p for sending over the network.
		If the connection is choked this call will block until timeout,
		or until the connection becomes un-choked after which the packet
		will be queued.  Returns True if packet was sent, False otherwise.
		"""
		#@TODO:  Create a similar function (or same function with new parameters) that
		#blocks until the JSONRPC response is received, and then returns the result
		end_time = timeout + time.time()
		if not address in self.congest_connect_state:
			self.json_out_queue.put(p)  #no congestion info on connection, so just send packet
			return True
		
		congest_state = self.congest_connect_state[address]
		while(congest_state == 'choke'):  #don't send packets if connection is choked
			if time.time()>end_time:
				return False
			time.sleep(0.01)
			congest_state = self.congest_connect_state[address]
			
		#connection has become unchoked
		self.json_out_queue.put(p)
		return True	
		
	
	
	
	
	
	
	
	
	
	
	