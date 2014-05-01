



from local_blob_manager import local_blob_manager
import xmlrpclib
import os
from commit_blob import commit_blob
import logging

class peer_manager():
	peers = None
	peer_dict=dict()
	storage_directory = None
	file_block_dict=dict()
	
	share_machine_dict = dict()  #maps share IDs to machine IDs
	share_key_dict = dict()  #maps share IDs to corresponding public keys (or certificates?)
	machine_address_dict = dict()  #maps machine IDs to url (IP:port)
	machine_proxy_dict = dict()  #maps machine IDs to xmlrpc proxy connections
	
	
	
	def __init__(self):
		pass
	
	
	
	def update_machine_address(self, machine_ID, url):
		self.machine_address_dict.update({machine_ID:url})
		
		
		
	def add_share_to_machine(self, share_ID, machine_ID):  #TODO: needs to be validated by a certificate each call?
		if not self.share_machine_dict.share_ID:
			new_m_ID = [machine_ID]
		else:
			old_m_ID = self.share_machine_dict.share_ID
			new_m_ID = old_m_ID.append(machine_ID)
		self.share_machine_dict.update({share_ID:new_m_ID})
		
	
	
	def connect_machine(self, machine_ID, url):
		logging.info('connecting to machine %s: %s', machine_ID, url)
		proxy = xmlrpclib.ServerProxy(url, allow_none=True)  #TODO: url here
		self.machine_proxy_dict.update({machine_ID:proxy})
		self.machine_address_dict.update({machine_ID:url})
		return proxy
	
	
	
	def connect_peer(self, peer_ID, url):
		logging.info('connecting to peer %s: %s', peer_ID, url)
		proxy = xmlrpclib.ServerProxy(url, allow_none=True)  #TODO: url here
		self.peer_dict.update({peer_ID:proxy})
		return proxy
	
	

	def collect_commit_dependencies(self, key, file_name, peer_ID, url = None):
		if (not (peer_ID in self.peer_dict)):
			self.connect_peer(peer_ID, url)
				
		bm = local_blob_manager()
		while True:
			files_needed = bm.blobs_to_restore_blob(key, self.storage_directory, file_name)
			if files_needed==None:
				return
			for need_file_name in files_needed:
				logging.debug('requesting file to fill dependency: %s', need_file_name)
				file_xmlrpc_data = (self.peer_dict[peer_ID]).get_file(need_file_name)
				f=open(os.path.join(self.storage_directory, need_file_name),'wb')
				f.write(file_xmlrpc_data.data)
				f.close()
			
	
	
	#xmlrpc function
	def push_update_to_peer(self, peer_ID, url = None):
		'''
		Loop through all blobs in storage directory and poll peer to see if they have it.
		If the peer does not have the file, send it to them.
		'''
		if (not (peer_ID in self.peer_dict)):
			self.connect_peer(peer_ID, url)
			
		for root, dirs, files in os.walk(self.storage_directory):
			for name in files:  
				if not (self.peer_dict[peer_ID]).has_file(name):
					f=open(os.path.join(root, name))
					(self.peer_dict[peer_ID]).save_file(name, xmlrpclib.Binary(f.read()))
					
		
		
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
	def get_file(self, file_name):
		logging.info('xmlrpc call.  file_name: %s', file_name)
		full_file_path = self.storage_directory + '/' + file_name
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
	def save_file(self, file_name, file_bytes):
		logging.info('xmlrpc call.  file_name: %s', file_name)
		full_file_name = self.storage_directory + '/' + file_name
		fp = open(full_file_name,'wb')
		fp.write(file_bytes.data)
		fp.close()
	
	
	
	def has_file(self, file_name):
		'''
		Polls the peer to see if they have a specific file.  Returns true if they do.
		'''
		full_file_name = self.storage_directory + '/' + file_name
		return os.path.isfile(full_file_name);
	
	
	
	#xmlrpc function
	def ping(self):
		logging.info('xmlrpc call.')
		return 'pong'
	
	
	
	#xmlrpc function
	def get_all_commits(self, return_url):
		logging.info('xmlrpc call. return url: %s', return_url)
		return_peer = self.connect_peer('temp_ID', return_url)
		files_sent=0
		#walk storage directory
		for root, dirs, files in os.walk(self.storage_directory):
			for name in files:
				if name[0]=='_':  #commit filenames start with '_'
					#call save_file on each commit
					f=open(os.path.join(root,name))
					return_peer.save_file(name, xmlrpclib.Binary(f.read()))
					files_sent+=1
		return files_sent
		
		
	
	
	"""
	def process_network_msg(self, msg_type, msg_args, msg_body):
		if msg_type == 'fb':
			self.process_file_block(msg_args, msg_body)
	
	
	
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