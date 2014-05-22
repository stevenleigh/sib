

from file_blob import file_blob
from local_blob_manager import local_blob_manager
from sib import SIB
import os


import logging
import shutil
import unittest


logging.basicConfig(
				filename='test.log',
				filemode='w',
				format='%(asctime)s | %(process)d | %(processName)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s',
				level=logging.DEBUG)
logging.debug('testing started')

key=b'Sixteen byte key'
peer_A_storage = '../resource/peer_A_storage'  #simulated local
peer_B_storage = '../resource/peer_B_storage'  #simulated remote peer
peer_C_storage = '../resource/peer_C_storage'  #simulated remote peer



def reset_storage():
	shutil.rmtree(peer_A_storage)
	shutil.rmtree(peer_B_storage)
	shutil.rmtree(peer_C_storage)
	os.mkdir(peer_A_storage)
	os.mkdir(peer_B_storage)
	os.mkdir(peer_C_storage)
	os.mkdir(os.path.join(peer_A_storage, 'test_share'))
	os.mkdir(os.path.join(peer_B_storage, 'test_share'))
	os.mkdir(os.path.join(peer_C_storage, 'test_share'))
	shutil.rmtree('../resource/restore_directory_1')
	shutil.rmtree('../resource/restore_directory_2')
	shutil.rmtree('../resource/restore_directory_3')
	os.mkdir('../resource/restore_directory_1')
	os.mkdir('../resource/restore_directory_2')
	os.mkdir('../resource/restore_directory_3')


def setup_test_dirs():
	if os.path.exists('../resource/test_dir_1'):
		shutil.rmtree('../resource/test_dir_1')
	if os.path.exists('../resource/test_dir_2'):
		shutil.rmtree('../resource/test_dir_2')
	if os.path.exists('../resource/test_dir_3'):
		shutil.rmtree('../resource/test_dir_3')
	shutil.copytree('../resource/share merge test set/test_dir_1', '../resource/test_dir_1')
	shutil.copytree('../resource/share merge test set/test_dir_2', '../resource/test_dir_2')
	shutil.copytree('../resource/share merge test set/test_dir_3', '../resource/test_dir_3')
	


class TestLocalBlobManager(unittest.TestCase):

	def setUp(self):
		pass

	def test_initialize_simple(self):
		logging.debug('Testing initializing a simple file blob')
		reset_storage()
		fb=file_blob()
		fb.my_hash='1'		
		expected_string = '\n=========Printing details of file blob object=========\nmy_hash: 1\nparent_hash: \nblob_type: file\n------------------------------------------------------'
		self.assertEqual(expected_string, str(fb))
	
	
	def test_delta_simple(self):
		logging.debug('Testing a delta on a file blob')
		reset_storage()
		f=open('../resource/sample_text_1.txt','rb')
		fb=file_blob()
		fb.my_hash='1'
		fb.compute_delta(key,f.read())
		
		expected_string = '\n=========Printing details of file blob object=========\nmy_hash: a1f7f4060ff3f7c0b7c28b4a37990a851a225e475d47da7a0d82dec5\nparent_hash: \nblob_type: file\naggregate a[0:0] b[0:0] first line\nabcdefghijklmnopqrstuvwxyz\nthird line\nfourth\nlast line------------------------------------------------------'
		self.assertEqual(expected_string, str(fb))


	def test_merge_conflict(self):
		logging.debug('Testing a file blob merge conflict')
		reset_storage()
		f_branch_A=open('../resource/branch_A_conflict.txt','rb')
		f_branch_B=open('../resource/branch_B_conflict.txt','rb')
		f_ancest=open('../resource/common_ancestor.txt','rb')
		result = file_blob.merge(f_branch_A.read(), f_branch_B.read(), f_ancest.read())
		print result
		#TODO: assert something
		
	
	def test_initial_commit(self):
		logging.debug('Testing recoring a tree')
		reset_storage()
		setup_test_dirs()
		bm = local_blob_manager()
		commit_hash_1 = bm.commit_directory(key, '../resource/test_dir_1/root',
				os.path.join(peer_A_storage, 'test_share'), 'joe.keur', 'first commit msg')
		bm.restore_directory(key,'../resource/restore_directory_1', os.path.join(peer_A_storage, 'test_share'),
					 commit_hash_1)
		#TODO: assert something
		
		
	def test_delta_commit(self):
		logging.debug('Testing commiting with a known parent')
		reset_storage()
		setup_test_dirs()
		bm = local_blob_manager()
		commit_hash_1 = bm.commit_directory(key, '../resource/test_dir_3/root',
				os.path.join(peer_A_storage, 'test_share'), 'joe.keur', 'first commit msg')
		commit_hash_2 = bm.commit_directory(key, '../resource/test_dir_1/root',
				os.path.join(peer_A_storage, 'test_share'), 'joe.keur', 'first commit msg', commit_hash_1)
		#TODO: assert something
		
	def test_tree_merge(self):
		logging.debug('Testing tree merge')
		reset_storage()
		setup_test_dirs()
		


if __name__ == '__main__':
	suite = unittest.TestLoader().loadTestsFromTestCase(TestLocalBlobManager)
	unittest.TextTestRunner(verbosity=10+1).run(suite)




