



from local_blob_manager import local_blob_manager
from auto_sync import auto_sync
from watchdog.observers import Observer
import xmlrpclib
import os
import logging
import json



class peer_manager():
	
	
	
	#shouldn't be xmlrpc
	def __init__(self):
		self.storage_directory = None
		self.file_block_dict=dict()
		self.my_machine_ID = ''
		
		self.share_machine_dict = dict()  #maps share IDs to machine IDs
		self.share_key_dict = dict()  #maps share IDs to corresponding public keys (or certificates?)
		self.machine_address_dict = dict()  #maps machine IDs to url (IP:port)
		self.machine_proxy_dict = dict()  #maps machine IDs to xmlrpc proxy connections
	
	
	
	#shouldn't be xmlrpc
	def save_peer_info(self):
		f=open('config.txt','w')
		json.dump([self.my_machine_ID, self.storage_directory, self.share_machine_dict, \
			self.share_key_dict, self.machine_address_dict], f)
		f.close()
		return json.dumps([self.my_machine_ID, self.storage_directory, self.share_machine_dict, \
			self.share_key_dict, self.machine_address_dict])
	
	
	
	#shouldn't be xmlrpc
	def load_peer_info(self, config_file = 'config.txt'):
		f=open('config.txt','r')
		[self.my_machine_ID, self.storage_directory, self.share_machine_dict, \
			self.share_key_dict, self.machine_address_dict] = json.load(f)
		f.close()

	
	
	
	def update_machine_address(self, machine_ID, url):
		self.machine_address_dict.update({machine_ID:url})
		
		
		
	def add_share_to_machine(self, share_ID, machine_ID):  #TODO: needs to be validated by a certificate each call?
		if not share_ID in self.share_machine_dict:
			new_m_ID = [machine_ID]
		else:
			new_m_ID = self.share_machine_dict[share_ID]
			new_m_ID.append(machine_ID)
		self.share_machine_dict.update({share_ID:new_m_ID})
		if not (machine_ID == self.my_machine_ID):
			return
		if not os.path.exists(os.path.join(self.storage_directory, share_ID)):  #make local storage directories if necessary
			os.makedirs(os.path.join(self.storage_directory, share_ID))
		
	
	
	def connect_machine(self, machine_ID, url):
		logging.info('connecting to machine %s: %s', machine_ID, url)
		proxy = xmlrpclib.ServerProxy(url, allow_none=True)  #TODO: url here
		self.machine_proxy_dict.update({machine_ID:proxy})
		self.machine_address_dict.update({machine_ID:url})
		return proxy
	
	

	def collect_commit_dependencies(self, key, file_name, share_ID):
		if not (share_ID in self.share_machine_dict):
			print 'Error: share ID not associated with any machines.  Call add_share_to_machine()'
			return
		
		machine_proxy = self.machine_proxy_dict[(self.share_machine_dict[share_ID])[0]]  #use first machine proxy in list.  TODO# use all proxies at once
		
				
		bm = local_blob_manager()
		while True:
			files_needed = bm.blobs_to_restore_blob(key, os.path.join(self.storage_directory, share_ID), file_name)
			if files_needed==None:
				return
			for need_file_name in files_needed:
				logging.debug('requesting file to fill dependency: %s', need_file_name)
				file_xmlrpc_data = machine_proxy.get_file(share_ID, need_file_name)
				f=open(os.path.join(self.storage_directory, share_ID, need_file_name),'wb')
				f.write(file_xmlrpc_data.data)
				f.close()
			
	
	
	#xmlrpc function
	def push_update_to_peer(self, share_ID, machine_ID=None):
		'''
		Loop through all blobs in storage directory and poll peer to see if they have it.
		If the peer does not have the file, send it to them.
		If machine_ID is None then send updates to all machines with share.
		'''
		#TODO: make use of threads so machine_proxy xmlrpc calls are non-blocking.  
		#Typical network latency could slow this function to a crawl for large numbers of files.
		#Should be easy to pop all file names in a queue and process in parallel with threads.
		machine_proxy = (self.machine_proxy_dict[machine_ID])	
		for root, dirs, files in os.walk(os.path.join(share_ID, self.storage_directory)):
			for name in files:  
				if not machine_proxy.has_file(share_ID, name):
					f=open(os.path.join(root, name))
					machine_proxy.save_file(share_ID, name, xmlrpclib.Binary(f.read()))
					
		
		
	#xmlrpc function	
	def pull_updates_from_peer(self):
		#connect to peer
		pass
	
	
	
	#xmlrpc function
	def remove_outdated_from_peer(self):
		pass
	
	
	
	#xmlrpc function
	def get_file_block(self, file_name, block_number, block_length=1<<14):
		full_file_path = self.storage_directory + '/' + file_name
		#file_size = os.stat(full_file_path).st_size  #TODO: what happends when read past end of file?
		f = open(full_file_path, 'rb')
		f.seek(block_number*block_length)
		block_bytes = f.read(block_length)
		f.close()
		return block_bytes
	
	
	
	#xmlrpc function
	def get_file(self, share_ID, file_name):
		logging.info('xmlrpc call: share_ID: %s, file_name: %s', share_ID, file_name)
		full_file_path = os.path.join(self.storage_directory, share_ID, file_name)
		#file_size = os.stat(full_file_path).st_size  #TODO: what happends when read past end of file?
		f = open(full_file_path, 'rb')
		#block_bytes = f.read()
		transmit_string = xmlrpclib.Binary(f.read())
		f.close()
		return transmit_string
	
	
	
	#xmlrpc function
	def accept_file_block(self):
		pass
	
	
	
	#xmlrpc function
	def save_file(self, share_ID, file_name, file_bytes):
		logging.info('xmlrpc call:  file_name: %s', file_name)
		full_file_name = os.path.join(self.storage_directory, share_ID, file_name)
		fp = open(full_file_name,'wb')
		fp.write(file_bytes.data)
		fp.close()
	
	
	
	#xmlrpc function
	def has_file(self, share_ID, file_name):
		"""
		Polls the peer to see if they have a specific file.  Returns true if they do.
		"""
		full_file_name = os.path.join(self.storage_directory, share_ID, file_name)
		return os.path.isfile(full_file_name);
	
	
	
	#xmlrpc function
	def ping(self):
		logging.info('xmlrpc call: ping')
		return 'pong'
	
	
	
	#xmlrpc function
	def get_all_commits(self, share_ID, return_machine_ID):
		logging.info('xmlrpc call: share_ID: %s, return_machine_ID: %s', share_ID, return_machine_ID)
		if not (return_machine_ID in self.machine_proxy_dict):
			print 'Error: no proxy associated with return_machine_ID. Call connect_machine(), or update_machine_address()?'
			return
		
		return_peer = self.machine_proxy_dict[return_machine_ID]
		files_sent=0
		#walk storage directory
		for root, dirs, files in os.walk(os.path.join(self.storage_directory, share_ID)):
			for name in files:
				if name[0]=='_':  #commit filenames start with '_'
					#call save_file on each commit
					f=open(os.path.join(root,name))
					#TODO: make the calls to return_peer non-blocking, or xmlrpc multicall to avoid latency issues
					#TODO: check if peer already has file
					return_peer.save_file(share_ID, name, xmlrpclib.Binary(f.read()))
					files_sent+=1
		return files_sent
		
		
	
	
	def register_auto_sync(self, key, monitoring_directory, share_ID, user_name, min_update_interval=10):
		"""Sets up a daemon to perform commits whenever files have been changed in a given directory.
		Commits are then pushed to all relevant machines.
		
		"""
		a_s = auto_sync(key, monitoring_directory, self.storage_directory, share_ID, user_name, self.my_machine_ID, min_update_interval)
		observer = Observer()
		observer.schedule(a_s, monitoring_directory, recursive=True)
	 	observer.start()
	
	"""

	
	
	
	def process_file_block(self, msg_args, msg):
		#Store transfered blocks an allocated file.
		#Store a set indicating which blocks were transfered in a dict using filenames as keys.
		print 'processing file block'
		file_name, file_length, block_number, block_length, block_hash = msg_args
		
		#TODO: check block hashes.  send block request if fail
		if not file_name in self.file_block_dict:
			empty_blocks = range(0,int(1 + (file_length/block_length)))
			
			full_file_name = self.storage_directory + '/' + file_name
			fp = open(full_file_name,'wb')
			fp.write('0'*file_length)
			self.file_block_dict.update({file_name : [empty_blocks, fp]})
			
		
		empty_blocks, fp = self.file_block_dict[file_name]
		fp.seek(block_number*block_length)
		fp.write(msg)
		empty_blocks.remove(block_number)
		if empty_blocks==[]:
			print 'finished file transfer: %s' %(file_name)
			fp.close()
			del self.file_block_dict[file_name]
		self.file_block_dict[file_name]=[empty_blocks, fp]
		
		
		
		
	def send_full_blob(self, file_name, file_size=None, block_length=1<<14):
		full_file_path = self.storage_directory + '/' + file_name
		if file_size == None:
			file_size = os.stat(full_file_path).st_size
			
		for block_number in range(0, int(1.0 + file_size/block_length)):
			self.send_blob_block(file_name, file_size, block_number, block_length)

	
	
	def send_blob_block(self, file_name, file_size=None, block_number=0, block_length=1<<14):
		full_file_path = self.storage_directory + '/' + file_name
		if file_size == None:
			file_size = os.stat(full_file_path).st_size
		file_name = file_name
		f = open(full_file_path, 'rb')
		f.seek(block_number*block_length)
		block_bytes = f.read(block_length)
				
		#TODO: block or message hashing?  or is TCP error checking enough?
		block_hash = 1  #TODO: code this
		
		msg_args = [file_name, file_size, block_number, block_length, block_hash]
		
		self.nm.send_msg('fb', msg_args, block_bytes)
		
	"""	