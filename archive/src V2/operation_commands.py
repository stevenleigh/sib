

from file_blob import file_blob
from commit_blob import commit_blob
from local_blob_manager import local_blob_manager
from peer_manager import peer_manager
import peer_service

import xmlrpclib
import random
import time
from multiprocessing import Process
import os
from os.path import expanduser


def print_all_commits():
	cb = commit_blob()
	for root, dirs, files in os.walk(my_storage):
		for name in files:
			if name[0]=='_':  #commit filenames start with '_'
				cb.load(key, root, name)
				cb.display()


key=b'Sixteen byte key'

home = expanduser("~")
my_storage = '../storage'
my_working = '../working'
share_ID='live_test'
my_url = '70.55.44.120'
my_url = ''  #'101.109.92.68:43434'
your_url = ''  #'129.123.144.11:43434'
my_machine_ID = 'laptop'
command_port = 43434

#my_storage = '/home/steven/temp/my_storage'
#my_working = '/home/steven/temp/my_working'
#my_storage = 'Home/temp/you_storage'
#my_working = 'Home/temp/you_working'









bm=local_blob_manager()


#initialize and start local peer service
peer_me = peer_service.peer_service(command_port)
peer_me.pm.storage_directory = my_storage
peer_me.pm.add_share_to_machine(share_ID, my_machine_ID)
peer_you_proxy = peer_me.pm.connect_machine('desktop', your_url)
peer_me_process = Process(target = peer_me.serve_forever)
peer_me_process.start()
time.sleep(0.1)  #wait for peer process and socket creation


#commands for managing local commits
bm.commit_directory(key, my_working, os.path.join(my_storage, share_ID), 'user_name','commit msg')
bm.restore_directory(key, my_working, os.path.join(my_storage, share_ID), 'commit_hash')


#commands for getting commits from peer
peer_you_proxy.get_all_commits(share_ID, my_machine_ID)
print_all_commits()
peer_me.pm.collect_commit_dependencies(key, '_'+'commit_hash', 'peer_you', share_ID)

#send all local files to peer
peer_me.pm.push_update_to_peer(share_ID, 'desktop')



peer_me_process.terminate()








