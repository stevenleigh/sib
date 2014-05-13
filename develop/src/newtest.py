

from file_blob import file_blob
from local_blob_manager import local_blob_manager
from sib import SIB
import time
import os


import logging
import shutil
import cProfile
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

shutil.rmtree(peer_A_storage)
shutil.rmtree(peer_B_storage)
shutil.rmtree(peer_C_storage)
os.mkdir(peer_A_storage)
os.mkdir(peer_B_storage)
os.mkdir(peer_C_storage)
os.mkdir(os.path.join(peer_A_storage, 'test_share'))
os.mkdir(os.path.join(peer_B_storage, 'test_share'))






class TestLocalBlobManager(unittest.TestCase):

    def setUp(self):
        pass

    def test_initialize_simple(self):
        # make sure the shuffled sequence does not lose any elements
        logging.debug('Testing initializing a simple file blob')
        f=open('../resource/sample_text_1.txt','rb')
        fb=file_blob()
        fb.my_hash='1'        
        expected_string = '\n=========Printing details of file blob object=========\nmy_hash: 1\nparent_hash: \nblob_type: file\n------------------------------------------------------'
        self.assertEqual(expected_string, str(fb))
    
    
    def test_delta_simple(self):
        # make sure the shuffled sequence does not lose any elements
        logging.debug('Testing a delta on a file blob')
        f=open('../resource/sample_text_1.txt','rb')
        fb=file_blob()
        fb.my_hash='1'
        fb.compute_delta(key,f.read())
        
        expected_string = '\n=========Printing details of file blob object=========\nmy_hash: a1f7f4060ff3f7c0b7c28b4a37990a851a225e475d47da7a0d82dec5\nparent_hash: \nblob_type: file\naggregate a[0:0] b[0:0] first line\nabcdefghijklmnopqrstuvwxyz\nthird line\nfourth\nlast line------------------------------------------------------'
        self.assertEqual(expected_string, str(fb))
        



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLocalBlobManager)
    unittest.TextTestRunner(verbosity=10+1).run(suite)





