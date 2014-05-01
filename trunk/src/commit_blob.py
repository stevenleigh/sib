

from blob import * 
import urllib2
import datetime
import os
import json

class commit_blob(blob):
	
	def __init__(self):
		super(commit_blob, self ).__init__()
		self.blob_type='commit'
		self.my_hash=''
		self.tree_hash=''
		self.parent_hash=''
		self.other_parent_hash=''
		self.user_name=''
		self.IP=''
		self.date=''
		self.msg=''
	
	
	
	def create(self, key, user_name, msg, tree_hash, parent_commit=None, other_parent_commit=None):
		self.user_name = user_name
		self.msg = msg
		self.tree_hash=tree_hash
		self.parent_hash=parent_commit
		self.other_parent_hash=other_parent_commit
		#self.IP = urllib2.urlopen('http://icanhazip.com').read()  #@TODO: get public IP address in a more reliable way
		self.date=datetime.datetime.utcnow().ctime()
		self.my_hash = self.compute_hash(key, json.dumps([self.blob_type, self.tree_hash, self.parent_hash, 
														self.other_parent_hash, self.user_name, self.IP, 
														self.date, self.msg]))
		
		
		
	def display(self):
		print'=========Printing details of commit blob object========='
		print 'my_hash: %s' %self.my_hash
		print 'parent_hash: %s' %self.parent_hash
		print 'blob_type: %s' %self.blob_type
		print 'user_name: %s' %(self.user_name)
		print 'IP: %s' %(self.IP)
		print 'date: %s' %(self.date)
		print 'message: %s' %self.msg
		print'------------------------------------------------------'
			
		
		
	def store(self, key, path=None, max_percent_size_increase=0):	
		bytes_to_write = json.dumps([self.blob_type, [self.tree_hash, self.parent_hash,
									self.other_parent_hash, self.user_name, self.IP, 
									self.date, self.msg]])
		
		logging.debug("File string for encrypting: %s" %(bytes_to_write.decode("utf-8")))
		self.write(key, bytes_to_write, path, max_percent_size_increase)
		
		
		
	def load(self, key, storage_directory, commit_hash):
		commit_hash = self.find_full_hash(storage_directory, commit_hash)
		if commit_hash[0]!='_':
			commit_hash = '_' + commit_hash
		full_file_name = os.path.join(storage_directory, commit_hash)
		self.my_hash = commit_hash
		decrypted_bytes=self.read(key, full_file_name)
		
		[self.blob_type, [self.tree_hash, self.parent_hash, 
		self.other_parent_hash, self.user_name, self.IP, 
		self.date, self.msg]] = json.loads(decrypted_bytes)
		

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		