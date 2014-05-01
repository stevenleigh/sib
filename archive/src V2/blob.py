###super class for blobs



from Crypto.Hash import SHA224
from Crypto import Random
from Crypto.Cipher import AES
import os
import logging


class blob:
	blob_type=''
	my_hash=''
	parent_hash=''
	storage_directory=''

	
	
	def display(self):
		""""print class details, mainly for debug purposes"""
		print 'error: implement display method for blob subclass'



	def write(self, key, bytes_to_write, path=None, max_percent_size_increase=0):
		protocol_version=1
		
		#TODO: add random bites to end of byte stream here
		
		#TODO: compress byte stream here
		
		encrypted_bytes_to_write = self.encrypt(key, bytes_to_write)  #encrypt 	
		
		#create file and write bytes
		
		file_name='%s' %(self.my_hash)
		if self.blob_type=='commit':
			file_name = '_'+file_name
			
		#TODO: make first 2 bytes of file name a folder name
		if path==None:
			if self.storage_directory=='':
				file_path = file_name
			else:
				file_path = os.path.join(self.storage_directory, file_name)
		else:
			file_path = os.path.join(path, file_name)
		f=open(file_path,'w')
		f.write(encrypted_bytes_to_write)
		
		return self.my_hash
		

	
	def read(self, key, full_file_name):
		block_size=len(key)
		
		self.storage_directory, file_name = os.path.split(full_file_name)
		file_hash =  file_name
		if file_hash[0]=='_':
			file_hash=file_hash[1:]
		self.my_hash=file_hash
		f=open(full_file_name,'r')
		
		
		#decrypt file
		iv=f.read(block_size)
		cipher = AES.new(key, AES.MODE_CBC, iv)
		decrypted_bytes = cipher.decrypt(f.read())
		
		#remove padded zeros off end
		while(decrypted_bytes[len(decrypted_bytes)-1]=='0'):
			decrypted_bytes = decrypted_bytes[:len(decrypted_bytes)-1]  #TODO: how do we know the true message doesn't end in '0'?
		
		#TODO: decompress byte stream here
		
		logging.debug("Decoded file string: %s" %(decrypted_bytes.decode("utf-8")))
		
		return decrypted_bytes
	
	
	
	def compute_hash(self, key, byte_stream):
		""""compute file hash"""
		h = SHA224.new()
		h.update(key)
		h.update(byte_stream)
		return h.hexdigest()
	

		
	def encrypt(self, key, in_bytes):
		#encrypt a stream of bytes
		
		block_size=len(key)
		in_bytes+=b'0' * (block_size-(len(in_bytes)%block_size))  #pad message is zeros
		iv = Random.new().read(block_size)  #generate IV
		cipher = AES.new(key, AES.MODE_CBC, iv)
		encrypted_bytes = iv + cipher.encrypt(buffer(in_bytes,0))
		return encrypted_bytes
		
		
		
	def find_full_hash(self, directory, hash_prefix):
		if len(hash_prefix) >= 56:
			return hash_prefix  #already full hash
		if hash_prefix[0] == '_':  #remove preceding underscore if it exists
			hash_prefix = hash_prefix[1:]
		
		for root, dirs, files in os.walk(directory):
			for name in files:
				compare_name = name
				if compare_name[0] == '_':  #remove preceding underscore if it exists
					compare_name = name[1:]
				compare_name=compare_name[0:len(hash_prefix)]
				if compare_name == hash_prefix:
					return name
		logging.debug('Couldn\'t find full hash for: %s' %hash_prefix)
		return None
	
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
