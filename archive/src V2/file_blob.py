

from blob import blob
import difflib
import json
import base64
import os
import logging


class file_blob(blob):
	blob_type='file'
	
	opcodes=[]
	opcode_bytes=[]
	
	
	
	def display(self):
		print'=========Printing details of file blob object========='
		print 'my_hash: %s' %self.my_hash
		print 'parent_hash: %s' %self.parent_hash
		print 'blob_type: %s' %self.blob_type
		index=0;
		for code in self.opcodes:
			#code(tag,i1,i2,j1,j2)
			print ("%7s a[%d:%d] b[%d:%d] %s" \
					%(code[0], code[1],code[2],code[3],code[4], \
					self.opcode_bytes[index]))
			index=index+1
		print'------------------------------------------------------'
			
			
			
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

			
		
	def gen_opcodes(self, new_text, parent_text=None):
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
		
		
		
	def apply_opcodes(self,old_text,opcodes,opcode_strings):
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















