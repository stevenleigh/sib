


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
		self.root_node=None
	
	class TreeNode():
		"""Structure for manipulating directory trees.
		"""
		def __init__(self):
			self.name = ''
			self.node_type = ''  #'file', or 'folder'
			self.hash_hex = ''
			self.size = 0
			self.children = None  #child TreeNodes
	
	
	@staticmethod		
	def serilaize(t, depth=0):
		"""Serializes the tree structure into a text format
		"""
		if t.node_type == 'file':
			out_str = '%s/%s/%s/%d\n' %(' '*depth, t.name, t.hash_hex, t.size)
		elif t.node_type == 'folder':
			out_str = ' '*depth + '/' + t.name + '\n'
	
			for child in t.children:
				out_str.append(tree_blob.serialize(child, depth+1))
		else:
			logging.error('invalid TreeNode type: %s'%(t.node_type))
		
		return out_str
	
	
	@staticmethod	
	def deserialize(tree_text, t, depth=0,):
		"""Deserializes the tree format from text into a tree of TreeNodes
		"""
		while True:
			line, sep, remainder = tree_text.partition('\n')
			if depth<line.find('/'):
				return tree_text
			child = tree_blob.TreeNode()
			if line.count('/')==3:
				[useless, child.name, child.hash_hex, child.size] = line.split('/')
				tree_text = remainder
			elif line.count('/')==1:
				[useless, child.name] = line.split('/')  #TODO: add folder hash
				tree_text = tree_blob.deserialize(remainder, child, depth+1)
			else:
				logging.error('invalid tree backslashes')
			t.children.append(child)
		
	
	
	def get_folders(self):
		pass
	
	def get_files(self):
		pass
		
	def get_node(self, full_name, node_type, root_node = None):
		if root_node == None:
			root_node = self.root_node
		depth = len(full_name.split('/'))
		name, sep, remainder = full_name.partition('/')
		for c in root_node.children:
			if depth>0 and c.name==name:
				return self.get_node(remainder, node_type, c)
			elif depth==0 and c.name==name and c.node_type == node_type:
				return c  #node found
		return None  #node not found

			
	def has_node(self, full_name, node_type):
		if self.get_node(full_name, node_type) == None:
			return False
		return True
	
			
	def add_node(self, full_name, node_type, hash_hex=None, size=None):
		parent_folder, sep, child_name = folder.rpartition('/')
		parent = self.get_node(parent_folder, 'folder')
		child = tree_blob.TreeNode()
		child.name = child_name
		child.node_type = node_type
		parent.children.append(child)

	
	def rm_node(self, full_name, node_type):
		parent_folder, sep, child_name = folder.rpartition('/')
		parent = self.get_node(parent_folder, 'folder')
		child = self.get_node(full_name, node_type)
		parent.children.remove(child)
		
	
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
		
		
		
	def write_directory_structure(self, key, storage_directory, working_directory_path, make_folders=True, tree_text=None):
		"""Creates folders for tree structure stored in opcodes.
		Also returns a list of all files and corresponding hashes
		"""
		
		file_listing=[]  #stores full file names and corresponding hashes
		
		if tree_text == None:
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
	
	
	@staticmethod
	def folder_list(tree_text):
		"""Returns a list of all folders in tree text.
		"""
		
		folder_list=[]
		
		path = ''		
		folders=[]
		for line in tree_text.split('\n'):
			if line.count('/')==3:
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
			folder_list.append(path)
				
		return folder_list
			

		
	def file_hashes(self, key, storage_directory):
		"""Return a list of unique file hashes identified in this tree.
		"""
		file_listing=self.write_directory_structure(key, storage_directory, None, False)
		file_hashes=[]
		for (path, file_name, hash_hex, file_size) in file_listing:
			file_hashes.append(hash_hex)
		file_hashes = list(set(file_hashes))  #get unique values
		return file_hashes


	@staticmethod
	def merge(tree_text_A, tree_text_B, tree_text_common_ancestor):
		"""Merges two trees."""
		
		"""
		Algorithm
		--------------
		A: update commit
		B: old commit
		C: common ancestor commit
		N: new tree
		-store trees from A, B, C, and N in easily traversable data structure
		-iterate through folders and files from A (from top down.  these iterations only add to wd)
		    -if B has it
		        -no change necessary
		        -add to N as is
		    -if C has it, but B doesn't 
		        -means B deleted file/folder
		        -don't add to N
		    -if neither C nor B have it
		        -means A added it
		        -push change to wd
		        -add to N
		    -if B has same file name and path, but different hash as A
		        -attempt merge
		        -add merged file(s) to N
		
		-iterate through folders and files from B (from bottom up.  these iterations only delete from wd)
		    -if neither C nor A have it
		        -means B added it
		        -add to N
		        -no change necessary
		    -if C has it, but A doesn't 
		        -means A deleted file/folder
		        -delete file/folder from wd
		
		-commit wd as merge
		
		-issues with algorithm
		    -B moves file, A edits file
    """
		folder_list_A = tree_blob.folder_list(tree_text_A)
		folder_list_B = tree_blob.folder_list(tree_text_B)
		folder_list_common_ancestor = tree_blob.folder_list(tree_text_common_ancestor)
		
		temp_tb = tree_blob()
		
		file_listing_A = temp_tb.write_directory_structure(None, '', '', False, tree_text_A)
		file_listing_B = temp_tb.write_directory_structure(None, '', '', False, tree_text_B)
		file_listing_common_ancestor = temp_tb.write_directory_structure(None, '', '', False, tree_text_common_ancestor)
		
			
			
			


















			
			
			
			
			
			
