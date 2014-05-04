


from file_blob import file_blob
import os
import string
import logging

class tree_blob (file_blob):
	
	def __init__(self):
		super(tree_blob, self ).__init__()
		self.blob_type='tree'
		self.blob_pointers=()
		self.blob_names=()
		
	
	def create_tree_text(self, key, directory_path):
		logging.info('encoding directory structure into text format for path: %s', directory_path)
		tree_text=''
		depth=0  #keep track of depth of directory, and indicate such using tabs
		root_depth = len(string.split(directory_path,'/'))
		for dir_name, dir_names, file_names in os.walk(directory_path):
			if '/.sib' in dir_name:  #ignore .sib folder
				continue			
			depth = len(string.split(dir_name,'/')) - root_depth
			(head,tail) = os.path.split(dir_name)
			tree_text+= ' '*depth + '/' + tail + '\n'
			# print path to all filenames.
			depth = depth + 1
			for file_name in file_names:
				file_path = os.path.join(dir_name, file_name) 
				file = open(file_path,'r')
				file_text = file.read()
				file_hash=self.compute_hash(key, file_text)  #TODO: does this use tonnes of CPU?  Consider Queue and multiprocessing
				file_size = len(file_text)  #file size is used for finding potential file blob matches later on
				line = '%s/%s/%s/%d\n' %(' '*depth, file_name, file_hash, file_size)
				tree_text+=line
				#tree_text+=' '*depth + '/' + file_name + '/' + file_hash + '/' + file_size + '\n'
				
				
		print '\n===\n' + tree_text + '\n==='
		logging.debug('\n%s', tree_text)
		return tree_text
		
		
		
	def write_directory_structure(self, key, storage_directory, working_directory_path, make_folders=True):
		"""Creates folders for tree structure stored in opcodes.
		Also returns a list of all files and corresponding hashes
		"""
		
		file_listing=[]  #stores full file names and corresponding hashes
		
		tree_text = self.apply_delta(key, storage_directory)
		
		path = ''		
		folders=[]
		for line in tree_text.split('\n'):
			if line.count('/')==3:
				[useless, file_name, hash_hex, file_size] = line.split('/')
				file_size = int(file_size)
				file_listing.append((path, file_name, hash_hex, file_size))
				continue  #this line is a file, not a directory
			elif line.count('/')!=1:
				continue  #this line is not a file, or a directory...?
			depth = line.find('/')
			while len(folders)>depth:
				folders.pop()
				
			folders.append(line[depth:])
			path = ''
			for folder_name in folders:
				path+= folder_name.decode('utf-8')
			if not make_folders:
				continue
			if not os.path.exists(working_directory_path + path):
				os.mkdir(working_directory_path + path) 
				
		return file_listing
			
			

		
	def file_hashes(self, key, storage_directory):
		"""Return a list of unique file hashes identified in this tree.
		"""
		file_listing=self.write_directory_structure(key, storage_directory, None, False)
		file_hashes=[]
		for (path, file_name, hash_hex, file_size) in file_listing:
			file_hashes.append(hash_hex)
		file_hashes = list(set(file_hashes))  #get unique values
		return file_hashes

		
			
			
			
			
			
			
			
			
			
			
