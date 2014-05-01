

from blob import blob
import difflib
import json
import base64
import os
import logging


class file_blob(blob):
	
	
	def __init__(self):
		super(file_blob, self ).__init__()
		self.blob_type='file'
		self.opcodes=[]
		self.opcode_bytes=[]
	
	
	def __str__(self):
		out_text = '\n'
		out_text+='=========Printing details of file blob object=========\n'
		out_text+= 'my_hash: %s\n' %self.my_hash
		out_text+= 'parent_hash: %s\n' %self.parent_hash
		out_text+= 'blob_type: %s\n' %self.blob_type
		index=0;
		for code in self.opcodes:
			out_text+= ("%7s a[%d:%d] b[%d:%d] %s" \
					%(code[0], code[1],code[2],code[3],code[4], \
					self.opcode_bytes[index]))
			index=index+1
		out_text+= '------------------------------------------------------'
		return out_text
	
	
	def display(self):
		print str(self)
			
			
			
	def compute_delta(self, key, new_text, parent_file_blob=None, storage_directory=None):
		""""Computes delta between two files.  Stores opcodes in terms of turning the new file into the old one."""
		
		if type(new_text)!=bytearray:
			new_text = bytearray(new_text)
		
		self.my_hash = self.compute_hash(key,new_text)
			
		if (parent_file_blob==None):  # if no parent file blob this means this is an initial commit
			(self.opcodes,self.opcode_bytes) = self.gen_opcodes(new_text)
		else:
			self.parent_hash=parent_file_blob.my_hash  #Current blob is a child to the parent blob.
			parent_text=parent_file_blob.apply_delta(key, storage_directory)  #get parent file text stream
			(self.opcodes,self.opcode_bytes) = self.gen_opcodes(new_text, parent_text)
			
		return


	
	def apply_delta(self, key, storage_directory):
		"""Apply delta between this file blob and the parent file blob
		 to get complete file at this blob's version """
		old_text=''	
		
		#Call apply_delta recursively working up parent tree until we get an aggregate
		if(self.parent_hash!=''):
			#file_blob_path = os.path.join(self.storage_directory, '1_'+self.parent_hash)
			parent_file_blob = file_blob()
			parent_file_blob.load (key, storage_directory, self.parent_hash)
			#parent_file_blob.storage_directory = self.storage_directory
			old_text=parent_file_blob.apply_delta(key, storage_directory)
		
		return self.apply_opcodes(old_text, self.opcodes, self.opcode_bytes)
		
	
	
	
	def store(self, key, path, max_percent_size_increase=0):
		"""store this file blob"""
		#convert bytearrays to strings with base64 encoding so JSON works
		opcode_strings=[]
		for line in self.opcode_bytes:
			opcode_strings.append(base64.b64encode(line))
			
		bytes_to_write = json.dumps([self.blob_type, [self.my_hash, self.parent_hash, 
									self.opcodes, opcode_strings]])
		
		logging.debug('File string for encrypting: %s' %(bytes_to_write.decode("utf-8")))
		#if path==None:
		#	return self.write(key, bytes_to_write, self.storage_directory, max_percent_size_increase)
		#else:
		return self.write(key, bytes_to_write, path, max_percent_size_increase)
			

		
		
	def load(self, key, storage_directory, file_hash):
		"""load this file blob"""
		file_hash = self.find_full_hash(storage_directory, file_hash)
		full_file_name = os.path.join(storage_directory,file_hash)
		decrypted_bytes=self.read(key, full_file_name)
		
		[self.blob_type, [self.my_hash, self.parent_hash, 
		self.opcodes, opcode_strings]] = json.loads(decrypted_bytes)
		
		#convert strings back to bytearrays using base64 decoding
		self.opcode_bytes=[]
		for line in opcode_strings:
			self.opcode_bytes.append(base64.b64decode(line))

			
	@staticmethod	
	def gen_opcodes(new_text, parent_text=None):
		opcodes=[]
		opcode_strings=[]
		
		if (parent_text==None):  # if no parent text this means this is an initial commit
			opcodes=[('aggregate',0,0,0,0)]
			opcode_strings=[new_text]
			return (opcodes, opcode_strings)
		
		
		s = difflib.SequenceMatcher(None, parent_text, new_text)
		for tag, i1, i2, j1, j2 in s.get_opcodes():
			opcodes = opcodes + [(tag,i1,i2,j1,j2)]
			new_opcode_string = [None]
			if tag == 'insert' or tag == 'replace':  #only insert and replace need to store additional data
				new_opcode_string = [new_text[j1:j2]]
			opcode_strings = opcode_strings + new_opcode_string
		
		return (opcodes, opcode_strings)
		
		
	@staticmethod	
	def apply_opcodes(old_text, opcodes, opcode_strings):
		"""Apply delta between this file blob and the parent file blob
		 to get complete file at this blob's version """

		return_string=bytearray()
		return_string+=old_text
		#apply the opcodes of current blob to parent text
		index=0;
		for code in opcodes:
			tag,i1,i2,j1,j2=code
			if(tag=='equal'):
				return_string[j1:j2]=return_string[i1:i2]
			elif(tag=='insert'):
				return_string[j1:j2]=opcode_strings[index]
			elif(tag=='delete'):
				pass
			elif(tag=='replace'):
				return_string[j1:j2]=opcode_strings[index]
			elif(tag=='aggregate'):
				#for line_index in range (0,len(opcode_strings[0])):
				#	return_string+=opcode_strings[0][line_index]
				return_string = opcode_strings[0]
				
			else:
				print 'error: undefined delta opcode'
			index=index+1
			
		return return_string


	class OpcodeIter():
		"""Object to manage iterating through opcodes.
		A helper class to the merger method.
		"""
		
		def __init__(self, opcodes, opcode_strings, ancestor_text):
			self.opcodes = opcodes
			self.opcode_strings = opcode_strings
			self.current_opcode_idx = 0
			self.current_fp = 0  #"file pointer" to current location in "file"
			self.new_opcode = True
			self.ancestor_text = ancestor_text
			self.equal_iter = 0

		def next(self):
			"""Iterates through the opcodes and returns the current output 
			character and current opcode tag for that character.
			"""
			tag=None
			char=None
			
			if self.current_opcode_idx >= len(self.opcodes):
				return ['EOF', None]
			code = self.opcodes[self.current_opcode_idx]
			tag,i1,i2,j1,j2 = code

			if tag in ['insert', 'replace']:  #only insert and replace store opcode strings
				oc_string = self.opcode_strings[self.current_opcode_idx]
				char = oc_string[self.current_fp-j1]
			
			if tag == 'equal':
				char = self.ancestor_text[i1+self.equal_iter]
				self.equal_iter+=1
			else:
				self.equal_iter=0

			self.current_fp+=1
			if self.current_fp >= j2:
				self.current_opcode_idx+=1
				self.new_opcode = True
			return [tag, char]
	
	
			
	@staticmethod
	def append_conflict(conflict_block_A, conflict_block_B, result_text):
		"""Helper for merge function.
		"""
		#We just reached then end of a conflicting block so append it.
		result_text.extend('\n************************')
		result_text.extend('\nblockA')
		result_text.extend('\n************************\n')
		result_text.extend(conflict_block_A)
		result_text.extend('\n************************')
		result_text.extend('\nblockB')
		result_text.extend('\n************************\n')
		result_text.extend(conflict_block_B)
		result_text.extend('\n************************')
		
		


	@staticmethod
	def merge(branch_A_text, branch_B_text, common_ancestor_text):
		"""Merges a file from branch A with a file from branch B.  
		Uses a common ancestor for some reason.
		
		Basic algorithm:
			-compute opcodes of ancestor->A and ancestor->B
			-apply both sets of opcodes at the same time
			-append characters in agreement
			-if the opcodes conflict insert both version A and version B in the file
		"""
		#@TODO:  If these are binary files such a unified diff doesn't really make sense.
		#@TODO:  Notify user somehow if there is a conflict.
		#@TODO:  This rewrites the whole file even if only a single character was changed.  Is there a quicker way?
		#@TODO:  Moving the most likely conditionals closer to the top of the loop could speed things up by short-circuiting more.  (watch out for complex logic though...)
		
		[branch_A_opcodes, branch_A_opcode_strings] = file_blob.gen_opcodes(branch_A_text, common_ancestor_text)
		[branch_B_opcodes, branch_B_opcode_strings] = file_blob.gen_opcodes(branch_B_text, common_ancestor_text)
		
		A_iter = file_blob.OpcodeIter(branch_A_opcodes, branch_A_opcode_strings, common_ancestor_text)
		B_iter = file_blob.OpcodeIter(branch_B_opcodes, branch_B_opcode_strings, common_ancestor_text)
		
		result_text = bytearray()
		conflict_block_A = bytearray()
		conflict_block_B = bytearray()
		conflicting = False
		conflict_tag_A = ''  #For use in conflicts.  If a conflict is detected, assume the conflict continues until one of the opcodes change.
		conflict_tag_B = ''
		[tag_A, char_A] = A_iter.next()
		[tag_B, char_B] = B_iter.next()
			
		while True:
			#Only conditional that checks for conflicts
			if (tag_A=='insert' and tag_B=='insert' and char_A!=char_B) \
				or (tag_A=='replace' and tag_B=='replace' and char_A!=char_B) \
				or (tag_A=='delete' and tag_B=='replace') \
				or (tag_A=='replace' and tag_B=='delete') \
				or (tag_A==conflict_tag_A and tag_B==conflict_tag_B):  
				conflicting = True
				conflict_tag_A = tag_A
				conflict_tag_B = tag_B
				conflict_block_A.append(char_A)
				conflict_block_B.append(char_B)
				[tag_A, char_A] = A_iter.next()
				[tag_B, char_B] = B_iter.next()
				continue
			
			if conflicting:  #triggers at the end of a conflicting block
				file_blob.append_conflict(conflict_block_A, conflict_block_B, result_text)
				conflict_block_A = bytearray()
				conflict_block_B = bytearray()
				conflicting = False
				conflict_tag_A = ''
				conflict_tag_B = ''
			
			if (tag_A=='equal' and tag_B=='equal') \
				or (tag_A=='insert' and tag_B=='insert' and char_A==char_B) \
				or (tag_A=='replace' and tag_B=='replace' and char_A==char_B):
				result_text.append(char_A)
				[tag_A, char_A] = A_iter.next()
				[tag_B, char_B] = B_iter.next()
				continue;
			if (tag_A=='equal' and tag_B=='delete') \
				or (tag_A=='delete' and tag_B=='equal') \
				or (tag_A=='delete' and tag_B=='delete'):
				[tag_A, char_A] = A_iter.next()
				[tag_B, char_B] = B_iter.next()
				continue;
			if tag_A=='equal' and tag_B=='replace':
				result_text.append(char_B)
				[tag_A, char_A] = A_iter.next()
				[tag_B, char_B] = B_iter.next()
				continue;
			if tag_A=='replace' and tag_B=='equal':
				result_text.append(char_A)
				[tag_A, char_A] = A_iter.next()
				[tag_B, char_B] = B_iter.next()
				continue;
			if tag_A=='EOF' and tag_B=='EOF':
				break
			if (tag_A=='insert') \
				or (tag_B=='EOF'):  #insert-delete, insert-equal, insert-replace, insert-EOF, equal-EOF, delete-EOF, replace-EOF.  Should some of these be conflicts?
				result_text.append(char_A)  #@TODO: bug?  delete-EOF shouldn't append
				[tag_A, char_A] = A_iter.next()
				continue;
			if (tag_B=='insert') \
				or (tag_A=='EOF'):
				result_text.append(char_B)  #@TODO: bug?  delete-EOF shouldn't append
				[tag_B, char_B] = B_iter.next()
				continue;
			
		return result_text






























