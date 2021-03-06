


from file_blob import file_blob
from tree_blob import tree_blob
from commit_blob import commit_blob
import difflib
import logging
import os



class local_blob_manager:
	
	
	def commit_directory(self, key, working_directory, storage_directory, user_name, commit_msg,
						parent_commit_hash=None, other_parent_commit_hash=None):
		"""Traverse working directory and store all file blobs"""
		logging.info('working_directory: %s, storage_directory: %s, user_name: %s, commit_msg: %s, parent_commit_hash: %s, other_parent_commit_hash: %s', 
					working_directory, storage_directory, user_name, commit_msg, parent_commit_hash, other_parent_commit_hash)
		
		file_list, mod_times, last_commit_hash = local_blob_manager.read_commit_meta(working_directory)
		if parent_commit_hash==None and last_commit_hash!=None:
			parent_commit_hash = last_commit_hash
		
		#create and store tree blob
		tb = tree_blob()  #TODO: fix this up so it diffs with parent tree blobs
		tb.create_tree(key, working_directory)
		#tb_tree_text = tb.create_tree_text(key, working_directory)
		#tb.build_tree(key, storage_directory)
		tb_tree_text_bytes = bytearray(tb.serialize_tree(),'utf-8')
		tb.compute_delta(key, tb_tree_text_bytes, None)
		tb.storage_directory = storage_directory
		print str(tb)
		tb.store(key, storage_directory)
		tb_hash = tb.my_hash
		
		#create and store commit blob
		cb = commit_blob()
		cb.create(key, user_name, commit_msg, tb_hash, parent_commit_hash, other_parent_commit_hash)
		cb.display()
		cb.store(key, storage_directory)
		commit_hash = cb.my_hash

		self.store_file_blobs(key, commit_hash, parent_commit_hash, storage_directory, working_directory)
		local_blob_manager.write_commit_meta(working_directory, commit_hash)
				
		return commit_hash
	

	def store_file_blobs(self, key, commit_hash, parent_commit_hash, storage_directory, working_directory):
		logging.info('commit_hash: %s, parent_commit_hash: %s, storage_directory: %s, working_directory: %s', 
					commit_hash, parent_commit_hash, storage_directory, working_directory)
		
		#chop the root folder off working_directory
		working_directory, tail = os.path.split(working_directory)
		
		#load current commit, tree, and file info
		cb = commit_blob()
		cb.load(key, storage_directory, commit_hash)
		tb = tree_blob()  #it is okay to modify this tree blob.  The one stored for the commit is already saved.
		tb.load(key, storage_directory, cb.tree_hash)	
		tb.build_tree(key, storage_directory)
		logging.debug('tree to store: %s'%(tb))
		
		#removed files with duplicate hashes in working directory or storage directory
		hash_set = set()
		for root, dirs, files in os.walk(storage_directory):
			for f in files:
				hash_set.add(f)
		logging.debug('storage directory hashes: %s'%(hash_set))
		for path, node in tb.walk():
			logging.debug('checking: %s'%(path))
			if node.node_type != 'file':
				continue
			if node.hash_hex in hash_set:
				logging.debug('found hash match: %s'%(node.hash_hex))
				tb.rm_node(path, 'file')
			else:
				hash_set.add(node.hash_hex)
		
		
		if parent_commit_hash==None:  #this is an initial commit
			for path, node in tb.walk():
				if node.node_type !='file':
					continue
				full_path = os.path.join(working_directory, path)
				new_file = open(full_path,'r')
				fb = file_blob()
				fb.compute_delta(key, new_file.read())
				fb.store(key, storage_directory)
			return
		
		
		#load parent commit, tree, and file info
		pcb = commit_blob()
		pcb.load(key, storage_directory, parent_commit_hash)
		ptb = tree_blob()
		ptb.load(key, storage_directory, pcb.tree_hash)	
		ptb.build_tree(key, storage_directory)
		
		logging.debug('performing differential commit using following trees')
		logging.debug('parent tree: %s' %(str(ptb)))
		logging.debug('child tree: %s' %(str(tb)))
		

		#find files with the same name in the same path, compute deltas, and store as file blob diffs
		for path, node in tb.walk():
			if node.node_type != 'file':
				continue
			if not ptb.has_node(path, 'file'):
				continue
			p_node = ptb.get_node(path, 'file')
			logging.debug('Found files with matching paths and names.  working: %s, parent: %s', node.hash_hex, p_node.hash_hex)
			full_file_path = os.path.join(working_directory, path)
			new_file = open(full_file_path,'rb')
			pfb = file_blob()
			pfb.load(key, storage_directory, p_node.hash_hex)
			fb = file_blob()
			fb.compute_delta(key, new_file.read(), pfb, storage_directory)
			fb.store(key, storage_directory)
			tb.rm_node(path, 'file')
		
		
		#TODO: re-implement code commented below
		"""
		#Look for similar files between working and parent and compute diffs on those
		index=-1
		while (index+1<len(file_hashes)):  #cycle through all file records in working directory
			index+=1
			parent_index=-1
			while (parent_index+1<len(parent_file_hashes)):  #cycle through all files records in parent commit
				parent_index+=1
				#if file_names[index]!= parent_file_names[parent_index]:
				#	break
				
				#must have similar file sizes
				percent_size_change = abs(file_sizes[index]-parent_file_sizes[index]) / file_sizes[index] 
				if  percent_size_change > 0.10:
					continue
				
				#must have similar byte sequences
				full_file_path = working_directory + file_folders[index] + '/' + file_names[index]
				new_file = open(full_file_path,'rb')
				new_file_text = new_file.read()
				pfb = file_blob()
				pfb.load(key, storage_directory, parent_file_hashes[parent_index])
				pfb_text = pfb.apply_delta(key, storage_directory)
				s=difflib.SequenceMatcher(None,new_file_text,pfb_text)
				if s.real_quick_ratio() < 0.75:
					continue
				if s.quick_ratio() < 0.75:
					continue
				
				#If this line is reached the files are similar enough.  Compute the diff and store.
				logging.debug('Found files with similar content. working: %s, parent: %s', file_hashes[index], parent_file_hashes[parent_index])
				fb = file_blob()
				fb.compute_delta(key, new_file_text, pfb, storage_directory)
				fb.store(key, storage_directory)
				
				file_hashes.pop(index)
				file_names.pop(index)
				file_folders.pop(index)
				file_sizes.pop(index)
				index-=1
				break
		"""
		
		#store all remaining files as initial versions
		for path, node in tb.walk():
			if node.node_type !='file':
				continue
			full_file_path = os.path.join(working_directory, path)
			new_file = open(full_file_path,'rb')
			fb = file_blob()
			fb.compute_delta(key, new_file.read())
			fb.store(key, storage_directory)		


	def restore_directory(self, key, working_directory, storage_directory, commit_hash):
		'''
		load a whole directory as an initial commit
		'''
		logging.info('working_directory: %s, storage_directory: %s, commit_hash: %s', working_directory, storage_directory, commit_hash)
		#@TODO:  Write to a temp directory first and then cut to the working directory?  Would ensure user has very little possibility to see on partial files.
		
		cb=commit_blob()
		cb.load(key, storage_directory, commit_hash)
		
		#restore tree folder structure
		tb = tree_blob()
		tb.load(key, storage_directory, cb.tree_hash)
		tb.build_tree(key, storage_directory)
		logging.debug('tree to restore:\n%s'%(str(tb)))
		tb.write_folders(working_directory)
		
		for path, node in tb.walk():
			if node.node_type != 'file':
				continue
			fb = file_blob()
			fb.load(key, storage_directory, node.hash_hex)
			full_file_path = os.path.join(working_directory, path)
			#full_file_path = working_directory + path + '/' + file_name
			f=open(full_file_path,'wb');
			f.write(fb.apply_delta(key, storage_directory))	


	def update_directory(self, key, working_directory, storage_directory, update_ch, wd_ch):
		"""
		Load a whole directory as a second commit.
		update_ch: update commit hash
		wd_ch: working directory commit hash
		"""
		#@TODO: this
		
		#update_ch is always a child of wd_ch.  If not, we need to commit the wd, perform a merge, then run update_directory
		
		#load trees from update and wd.
		
		#overwrite tree for update and delete any folders that don't exist in update
		
		#sort file lists from update and wd in alpha numeric based on hash
		
		
		pass


	
	
	def blobs_to_restore_blob(self, key, storage_directory, file_name, parent_tree = True):
		"""
		Returns a list file names of any blobs needed to restore a blob.  
		If an empty list is returned then it should be possible to restore the given blob from local files.
		Will likely need to be called repeatedly on a commit because needed blobs 
		also have dependent blobs which wont be known until the needed blobs are obtained. 
		"""
		if (not os.path.exists(os.path.join(storage_directory,file_name))):
			return [file_name]
		
		#Check if this is a commit blob
		if file_name[0]=='_':
			#Get the tree.  Parent commits are not needed to restore a commit, or its files.
			cb = commit_blob()
			cb.load(key, storage_directory, file_name[1:])
			return self.blobs_to_restore_blob(key, storage_directory, cb.tree_hash)
		
		fb = file_blob()
		fb.load(key, storage_directory, file_name)
		
		#check if this is a tree blob
		if fb.blob_type=='tree':
			tb=tree_blob()
			tb.load(key, storage_directory, file_name)  #TODO: can this be casted?
			if not tb.parent_hash=='':
				#check for all parents of tree
				needed_tree_parent_hash = self.blobs_to_restore_blob(key, storage_directory, tb.parent_hash, False)
				if not (needed_tree_parent_hash == None):
					return needed_tree_parent_hash
			
			if not parent_tree:  #only traverse tree structure of parent tree
				return None
			#check for all files in tree structure
			file_hashes = tb.file_hashes(key, storage_directory)
			#(unused_path, unused_file_name, hash_hex, unused_file_size) = tb.write_directory_structure(key, storage_directory, None, False)
			needed_files = []
			for h in file_hashes:
				temp_hash = self.blobs_to_restore_blob(key, storage_directory, h)
				if not temp_hash==None:
					needed_files.extend(temp_hash)
			if needed_files==[]:
				return None
			return needed_files
		
		#fb is a file blob
		if fb.parent_hash=='':
			return None
		else:
			return self.blobs_to_restore_blob(key, storage_directory, fb.parent_hash)
	
		
	@staticmethod		
	def get_file_change_times(wd):
		"""Traverse through working directory wd and read the date modified time for each file.
		Return a list of full file paths from the wd and a corresponding list of times.
		"""
		file_list = []
		mod_times = []
		for root, dirs, files in os.walk(wd):
			for name in files:
				file_list.append(os.path.join(root, name))
				mod_times.append(os.path.getmtime(os.path.join(root, name)))
		return file_list, mod_times
	
	
	@staticmethod
	def write_commit_meta(wd, commit_hash):
		"""Write the meta data for a commit.  The path is wd/.sib/.
		Various files are written.
		last_mod_time.txt : mod_times file_list
		last_commit_hash.txt
		"""
		if not os.path.exists(os.path.join(wd,'.sib')):
			os.mkdir(os.path.join(wd,'.sib'))
		
		f_time = open(os.path.join(wd,'.sib','last_mod_time.txt'),'w')  #TODO: use with statement
		file_list, mod_times = local_blob_manager.get_file_change_times(wd)
		while(not file_list):  #test for empty list
			f_time.write("" + mod_times.pop() + " " + file_list.pop())
		f_time.close()
		
		f_commit = open(os.path.join(wd,'.sib','last_commit_hash.txt'),'w')
		f_commit.write(commit_hash)
		f_commit.close()
		
		
	@staticmethod
	def read_commit_meta(wd):
		"""Read the meta data for a commit.  The path is wd/.sib/.
		Various files are read.
		last_mod_time.txt : mod_times file_list
		last_commit_hash.txt
		Returns file_list, mod_times, last_commit_hash
		"""
		file_list = []
		mod_times = []
		last_commit_hash = None
		
		if not os.path.exists(os.path.join(wd,'.sib')):
			return file_list, mod_times, last_commit_hash
		
		f_time = open(os.path.join(wd,'.sib','last_mod_time.txt'),'r')  #TODO: use with statement
		for line in f_time:
			space_idx = line.index(' ')
			mod_times.append(line[0:space_idx])
			file_list.append(line[space_idx:])
		f_time.close()
		
		f_commit = open(os.path.join(wd,'.sib','last_commit_hash.txt'),'r')
		last_commit_hash = f_commit.readline()
		f_commit.close()
		
		return file_list, mod_times, last_commit_hash
			








