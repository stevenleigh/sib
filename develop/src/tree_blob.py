


from file_blob import file_blob
import os
import string
import logging

class tree_blob (file_blob):
	
	def __init__(self):
		super(tree_blob, self).__init__()
		self.blob_type='tree'
		self.blob_pointers=()
		self.blob_names=()
		self.root_node=None
		
		
	def __str__(self):
		out_text = super(tree_blob, self).__str__()
		if self.root_node == None:
			return out_text
		
		out_text+= '\n'
		out_text+='=========Printing details of tree blob object=========\n'
		out_text+=self.serialize_tree()
		out_text+= '------------------------------------------------------'
		return out_text

	
	class TreeNode():
		"""Structure for manipulating directory trees.
		"""
		def __init__(self):
			self.name = ''
			self.node_type = ''  #'file', or 'folder'
			self.hash_hex = ''
			self.size = 0
			self.children = []  #child TreeNodes
	
	
	def serialize_tree(self):
		"""Serializes the tree structure into a machine and human readable text format
		"""
		out_str = ''
		for path, node in self.walk():
			depth = path.count('/')
			if node.node_type == 'file':
				out_str += '%s/%s/%s/%d\n' %(' '*depth, node.name, node.hash_hex, node.size)
			elif node.node_type == 'folder':
				out_str += ' '*depth + '/' + node.name + '\n'
		return out_str
		
	
	def build_tree(self, key, storage_directory):  #TODO: call this on load
		tree_text = self.apply_delta(key, storage_directory)
		self.deserialize_tree(tree_text, None, 0)
	
	
	def deserialize_tree(self, tree_text, t, depth=0):
		"""Deserializes the tree format from text into a tree of TreeNodes
		"""		
		while True:
			if tree_text == None:
				return
			line, sep, remainder = tree_text.partition('\n')
			logging.debug('line: %s'%(line))
			if '/' not in line:
				return
			if depth>line.find('/'):
				return tree_text
			child = tree_blob.TreeNode()
			if line.count('/')==3:
				[useless, child.name, child.hash_hex, child.size] = line.split('/')
				child.size = int(child.size)
				child.node_type = 'file'
				tree_text = remainder
			elif line.count('/')==1:
				[useless, child.name] = line.split('/')  #TODO: add folder hash
				child.node_type = 'folder'
				tree_text = self.deserialize_tree(remainder, child, depth+1)
			else:
				logging.error('invalid tree backslashes')
			if depth == 0:
				self.root_node = child
				return
			else:
				t.children.append(child)  #TODO: when/how to make root node?
		
	
	def walk(self, node=None, full_path=''):
		if node == None:
			node = self.root_node
			full_path = node.name
		else:
			full_path = full_path + '/' + node.name
		yield full_path, node
		children = list(node.children)  #make copy of list in case tree is modified during iteration
		for c in children:
			for path, n in self.walk(c, full_path):
				yield path, n
	
		
	def get_node(self, full_name, node_type, node = None):
		if node == None:
			logging.debug('[full_name, node_type]: %s'%([full_name, node_type]))
			node = self.root_node
		name, sep, remainder = full_name.partition('/')
		if node.name != name:
			return None
		depth = len(full_name.split('/'))
		logging.debug('[depth, name, remainder]: %s'%([depth, name, remainder]))
		if depth > 1:
			for c in node.children:
				ret_node = self.get_node(remainder, node_type, c)
				if ret_node != None:
					return ret_node
		if depth == 1 and node.node_type == node_type:
			return node
		if node == self.root_node:
			logging.error('Couldn\'t find node.  [full_name, node_type]: %s'%([full_name, node_type]))
			logging.error('%s'%(self.__str__()))
		return None 
			
					
	def has_node(self, full_name, node_type):
		if self.get_node(full_name, node_type) == None:
			return False
		return True
	
			
	def add_node(self, full_name, node_type, hash_hex=None, size=None):
		parent_folder, sep, child_name = full_name.rpartition('/')
		parent = self.get_node(parent_folder, 'folder')
		child = tree_blob.TreeNode()
		child.name = child_name
		child.node_type = node_type
		child.hash_hex = hash_hex
		child.size = size
		logging.debug('[parent, parent.children]: %s'%([parent, parent.children]))
		parent.children.append(child)

	
	def rm_node(self, full_name, node_type):
		parent_folder, sep, child_name = full_name.rpartition('/')
		logging.debug('[full_name, parent_folder, sep, child_name]: %s'%([full_name, parent_folder, sep, child_name]))
		parent = self.get_node(parent_folder, 'folder')
		child = self.get_node(full_name, node_type)
		parent.children.remove(child)
		
	
	def create_tree(self, key, path):
		base_path, unused, root_name = path.rpartition('/')
		self.root_node = tree_blob.TreeNode()
		self.root_node.name = root_name
		self.root_node.node_type = 'folder'
		
		for parent_dir, dir_names, file_names in os.walk(path):
			for dir_name in dir_names:
				if '/.sib' in dir_name:  #ignore .sib folder
					continue
				logging.debug('[parent_dir, dir_name, base_path]: %s'%([parent_dir, dir_name, base_path]))
				folder_path = os.path.relpath(os.path.join(parent_dir, dir_name), base_path)
				self.add_node(folder_path, 'folder')
			for file_name in file_names:
				file_path = os.path.join(parent_dir, file_name) 
				file = open(file_path,'r')
				file_text = file.read()
				self.add_node(os.path.relpath(file_path, base_path), 'file', self.compute_hash(key, file_text), len(file_text))
				
		
	#TODO: move to local_blob_manager?
	def write_folders(self, working_directory):
		for path, node in self.walk():
			if node.node_type !='folder':
				continue
			logging.debug('folder: %s'%(path))
			full_path = os.path.join(working_directory, path)
			if not os.path.exists(full_path):
				os.mkdir(full_path)	

		
	def file_hashes(self, key, storage_directory):
		"""Return a list of unique file hashes identified in this tree.
		"""
		file_hashes=[]
		for path, node in self.walk():
			if node.node_type != 'file':
				continue
			file_hashes.append(node.hash_hex)
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
		#folder_list_A = tree_blob.folder_list(tree_text_A)
		#folder_list_B = tree_blob.folder_list(tree_text_B)
		#folder_list_common_ancestor = tree_blob.folder_list(tree_text_common_ancestor)
		
		temp_tb = tree_blob()
		
		file_listing_A = temp_tb.write_directory_structure(None, '', '', False, tree_text_A)
		file_listing_B = temp_tb.write_directory_structure(None, '', '', False, tree_text_B)
		file_listing_common_ancestor = temp_tb.write_directory_structure(None, '', '', False, tree_text_common_ancestor)
		
			
			
			


















			
			
			
			
			
			
