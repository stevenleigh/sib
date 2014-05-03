


from file_blob import file_blob
#from commit_blob import commit_blob
from local_blob_manager import local_blob_manager
#from socketserver import SocketServer
#from packetprepostprocessor import PacketPrePostprocessor
#from jsonserver import JSONServer
#from packet import Packet
from sib import SIB
import time
#from multiprocessing import Process, Queue, Manager
import os
import operation_commands


#import random
import logging
import shutil
#import socket
import cProfile
#import pstats
#from threading import Thread
#import json


pr = cProfile.Profile()


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


#empty the storage directory
for root, dirs, files in os.walk(peer_A_storage, topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))
        
        
#empty the storage directory
for root, dirs, files in os.walk(peer_B_storage, topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))
        
        
#empty the storage directory
for root, dirs, files in os.walk(peer_C_storage, topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))
        

os.mkdir(os.path.join(peer_A_storage, 'test_share'))
os.mkdir(os.path.join(peer_B_storage, 'test_share'))







print '\n\n'
print '************************************************************************'
print '***Testing initializing a file blob'
logging.debug('Testing initializing a file blob')
print '************************************************************************'
#open a text file and import into file blob
f=open('../resource/sample_text_1.txt','rb')
fb=file_blob()
fb.my_hash='1'
fb.display()
fb.compute_delta(key,f.read())
fb.display()


print '\n\n'
print '************************************************************************'
print '***Testing a simple file delta'
logging.debug('Testing a simple file delta')
print '************************************************************************'
#open a 2nd version of text file and compute delta from first version
f2=open('../resource/sample_text_2.txt','rb')
fb2=file_blob()
fb2.my_hash='2'
fb2.display()
fb2.compute_delta(key, f2.read(), fb, os.path.join(peer_A_storage, 'test_share'))
fb2.display()
fb.display()




print '\n\n'
print '************************************************************************'
print '***Testing simple merging file blobs'
logging.debug('Testing simple merging file blobs')
print '************************************************************************'
f_branch_A=open('../resource/branch_A.txt','rb')
f_branch_B=open('../resource/branch_B.txt','rb')
f_ancest=open('../resource/common_ancestor.txt','rb')
result = file_blob.merge(f_branch_A.read(), f_branch_B.read(), f_ancest.read())
print result



print '\n\n'
print '************************************************************************'
print '***Testing merging conflict file blobs'
logging.debug('Testing merging conflict file blobs')
print '************************************************************************'
f_branch_A=open('../resource/branch_A_conflict.txt','rb')
f_branch_B=open('../resource/branch_B_conflict.txt','rb')
f_ancest=open('../resource/common_ancestor.txt','rb')
result = file_blob.merge(f_branch_A.read(), f_branch_B.read(), f_ancest.read())
print result




print '\n\n'
print '************************************************************************'
print '***Testing storing and loading a simple file blob'
logging.debug('Testing storing and loading a simple file blob')
print '************************************************************************'
#encrypt and store the first file blob, then decrypt and load
fb_hash = fb.store(key, os.path.join(peer_A_storage, 'test_share'))
fb3=file_blob()
fb3.my_hash='3'
fb3.load(key, os.path.join(peer_A_storage, 'test_share'), fb_hash)
fb3.display()


print '\n\n'
print '************************************************************************'
print '***Testing loading a whole directory as an initial commit'
logging.debug('Testing loading a whole directory as an initial commit')
print '************************************************************************'
#load a whole directory as an initial commit
bm=local_blob_manager()
commit_hash_1 = bm.commit_directory(key, '../resource/test_directory_1/root',
				os.path.join(peer_A_storage, 'test_share'), 'joe.keur', 'first commit msg')
bm.restore_directory(key,'../resource/restore_directory_1', os.path.join(peer_A_storage, 'test_share'),
					 commit_hash_1)


print '\n\n'
print '************************************************************************'
print '***Testing adding a second commit'
logging.debug('Testing adding a second commit')
print '************************************************************************'
bm=local_blob_manager()
commit_hash_2 = bm.commit_directory(key, '../resource/test_directory_2/root',
				os.path.join(peer_A_storage, 'test_share'),'joe.keur','second commit msg',commit_hash_1)
bm.restore_directory(key,'../resource/restore_directory_2', os.path.join(peer_A_storage, 'test_share'), commit_hash_2)



print '\n\n'
print '************************************************************************'
print '***Testing adding a third, more challenging, commit'
logging.debug('Testing adding a third, more challenging, commit')
print '************************************************************************'
bm=local_blob_manager()
commit_hash_3 = bm.commit_directory(key, '../resource/test_directory_3/root',
				os.path.join(peer_A_storage, 'test_share'),'joe.keur','third commit msg',commit_hash_2)
bm.restore_directory(key,'../resource/restore_directory_3', os.path.join(peer_A_storage, 'test_share'), commit_hash_3)





"""
print '\n\n'
print '************************************************************************'
print '***Testing SIB ping RPC'
logging.debug('Testing SIB ping RPC')
print '************************************************************************'
sib = SIB()
sib.ss.add_socket(port = 11114)

rpc_msg = '{"jsonrpc": "2.0", "method": "ping", "params": [1.0, null, [null]], "id": 4}'


s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s2.bind(('',11115))
s2.sendto(rpc_msg ,('localhost',11114))
	
sib.process_all()

print s2.recv(1028)




print '\n\n'
print '************************************************************************'
print '***Testing SIB receiving a file block'
logging.debug('Testing SIB receiving a file block')
print '************************************************************************'
sib = SIB()
sib.ss.add_socket(port = 11116)
sib.js.storage_directory = peer_A_storage

rpc_msg = '{"jsonrpc": "2.0", "method": "save_file_block", "params": [1.0, null, ["test_share", "test_file_block.txt", 0]], "id": 5}This is a sample binary payload'


s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s2.bind(('',11117))
s2.sendto(rpc_msg ,('localhost',11116))

sib.process_all()

print s2.recv(1028)




print '\n\n'
print '************************************************************************'
print '***Testing SIB filling a request for a full file'
logging.debug('Testing SIB filling a request for a full file')
print '************************************************************************'
sib = SIB()
sib.ss.add_socket(port = 11116)
sib.js.storage_directory = peer_A_storage

rpc_msg = '{"jsonrpc": "2.0", "method": "get_file", "params": [1.0, null, ["test_share", "' + fb3.my_hash + '"]], "id": 5}'


s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s2.bind(('',11117))
s2.setblocking(0)
s2.sendto(rpc_msg ,('localhost',11116))
time.sleep(0.1)  

sib.process_all()

for i in range(6):
	try:
		print s2.recv(1028)
	except socket.error as msg:
		pass
		

"""


print '\n\n'
print '************************************************************************'
print '***Testing sending a large file between two SIBs'
logging.debug('Testing sending a large file between two SIBs')
print '************************************************************************'
large_file = open('../resource/alice.txt','rb')
fb=file_blob()
fb.compute_delta(key,large_file.read())
large_file_hash = fb.store(key, os.path.join(peer_B_storage, 'test_share'))
time.sleep(1)

sib_b = SIB()
sib_b.new_sockets.put(11120)
sib_b.js.storage_directory = peer_B_storage
sib_b.js.my_machine_ID = 'machine_B'

sib_a = SIB()
sib_a.new_sockets.put(11121)
sib_a.js.storage_directory = peer_A_storage
sib_a.js.my_machine_ID = 'machine_A'

#TODO: this transfer is slow?

sib_b.run_forever()
sib_a.run_forever()
time.sleep(0.5)

operation_commands.socket_command(method_name='update_machine_address', params=['machine_B','localhost',11120], to=('localhost',11121))
operation_commands.socket_command(method_name='update_machine_address', params=['machine_A','localhost',11121], to=('localhost',11120))
time.sleep(0.5)

operation_commands.socket_command(method_name='get_file', params=['machine_A', 'test_share', large_file_hash], to=('localhost',11120), frm=11121)

time.sleep(5)
sib_b.terminate()
sib_a.terminate()









print '\n\n'
print '************************************************************************'
print '***Testing adding shares and machine details'
logging.debug('Testing adding shares and machine details')
print '************************************************************************'
sib_a = SIB()
sib_a.new_sockets.put(11123)
sib_a.js.storage_directory = peer_A_storage
sib_a.js.my_machine_ID = 'machine_A'


sib_a.run_forever()
time.sleep(0.5)
operation_commands.socket_command(method_name='update_machine_address', params=['machine_A','localhost',10101], to=('localhost',11123))
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_B'], to=('localhost',11123))
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_A'], to=('localhost',11123))
time.sleep(2)
sib_a.terminate()







print '\n\n'
print '************************************************************************'
print '***Testing sending a directory update'
logging.debug('Testing sending a directory update')
print '************************************************************************'
sib_a = SIB()
sib_a.new_sockets.put(11125)
sib_a.js.storage_directory = peer_A_storage
sib_a.js.my_machine_ID = 'machine_A'

sib_c = SIB()
sib_c.new_sockets.put(11126)
sib_c.js.storage_directory = peer_C_storage
sib_c.js.my_machine_ID = 'machine_C'

sib_a.run_forever()
sib_c.run_forever()
time.sleep(0.5)
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_A'], to=('localhost',11125))
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_C'], to=('localhost',11125))
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_C'], to=('localhost',11126))
operation_commands.socket_command(method_name='update_machine_address', params=['machine_C','localhost',11126], to=('localhost',11125))
operation_commands.socket_command(method_name='update_machine_address', params=['machine_A','localhost',11125], to=('localhost',11126))
time.sleep(0.5)
operation_commands.socket_command(method_name='push_update_to_peer', params=['test_share','machine_C', None], to=('localhost',11125))
time.sleep(5)
sib_a.terminate()
sib_c.terminate()






print '\n\n'
print '************************************************************************'
print '***Testing automatic sync'
logging.debug('Testing automatic sync')
print '************************************************************************'
sib_c = SIB()
sib_c.new_sockets.put(11130)
sib_c.js.storage_directory = peer_C_storage
sib_c.js.my_machine_ID = 'machine_C'
sib_c.js.command_port = 11130
sib_c.run_forever()

sib_a = SIB()
sib_a.new_sockets.put(11131)
sib_a.js.storage_directory = peer_A_storage
sib_a.js.my_machine_ID = 'machine_A'
sib_a.js.command_port = 11131
sib_a.run_forever()


time.sleep(0.5)
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_A'], to=('localhost',11130))
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_A'], to=('localhost',11131))
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_C'], to=('localhost',11130))
operation_commands.socket_command(method_name='add_share_to_machine', params=['test_share','machine_C'], to=('localhost',11131))
operation_commands.socket_command(method_name='update_machine_address', params=['machine_C','localhost',11130], to=('localhost',11131))
operation_commands.socket_command(method_name='update_machine_address', params=['machine_A','localhost',11131], to=('localhost',11130))
time.sleep(0.5)
operation_commands.socket_command(method_name='register_auto_sync', params=[key, '../resource/restore_directory_3', 'test_share','auto_sync_user', 10], to=('localhost',11130))
operation_commands.socket_command(method_name='register_auto_sync', params=[key, '../resource/restore_directory_1', 'test_share','auto_sync_user', 10], to=('localhost',11131))

#do some file operations.  A new commit should be created for each one.
time.sleep(8)
#copy a file
shutil.copy('../resource/restore_directory_3/root/alice.txt', '../resource/restore_directory_3/root/alice_copy.txt')
time.sleep(16)
#edit a file
f_auto = open('../resource/restore_directory_3/root/alice_copy.txt', 'a')
f_auto.write('a bunch of mumbo jumbo.  a bunch of mumbo jumbo.  a bunch of mumbo jumbo')
f_auto.close()
time.sleep(8)
#remove a file
os.remove('../resource/restore_directory_3/root/alice_copy.txt')
time.sleep(8)

sib_c.terminate()
sib_a.terminate()





print '\n\n'
print '************************************************************************'
print '***Testing printing all commits on peer C'
logging.debug('Testing printing all commits on peer C')
print '************************************************************************'
operation_commands.print_all_commits(key, peer_C_storage)









'''



print '\n\n'
print '************************************************************************'
print '***Testing receiving all commits form peer'
logging.debug('Testing receiving all commits form peer')
print '************************************************************************'
command_port+=2


peer_A = peer_service.peer_service(command_port)
peer_A.pm.storage_directory = peer_A_storage
peer_A.pm.my_machine_ID = 'machine_A'
peer_A.pm.add_share_to_machine('test_share','machine_A')
peer_A_process = Process(target = peer_A.serve_forever)
peer_A_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_C = peer_service.peer_service(command_port+1)
peer_C.pm.storage_directory = peer_C_storage
peer_C.pm.my_machine_ID = 'machine_C'
peer_C.pm.add_share_to_machine('test_share','machine_C')
peer_A_proxy = peer_C.pm.connect_machine('machine_A','http://localhost:' +str(command_port))

peer_C_process = Process(target = peer_C.serve_forever)  #start peer C as a new process so it can receive all commits
peer_C_process.start()
time.sleep(0.1)  #wait for peer process and socket creation

print peer_A_proxy.get_all_commits('test_share', 'http://localhost:' +str(command_port+1))  #Returns after peer A transfers all commits to peer C.


time.sleep(0.1)
peer_A_process.terminate()
peer_C_process.terminate()






print '\n\n'
print '************************************************************************'
print '***Testing collecting all blobs for a given commit'
logging.debug('Testing collecting all blobs for a given commit')
print '************************************************************************'
command_port+=2


peer_A = peer_service.peer_service(command_port)
peer_A.pm.storage_directory = peer_A_storage
peer_A.pm.my_machine_ID = 'machine_A'
peer_A.pm.add_share_to_machine('test_share','machine_A')
peer_A_process = Process(target = peer_A.serve_forever)
peer_A_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_C = peer_service.peer_service(command_port+1)
peer_C.pm.storage_directory = peer_C_storage
peer_C.pm.my_machine_ID = 'machine_C'
peer_C.pm.add_share_to_machine('test_share','machine_A')
peer_C.pm.add_share_to_machine('test_share','machine_C')
peer_C.pm.connect_machine('machine_A','http://localhost:' +str(command_port))
peer_C.pm.collect_commit_dependencies(key, '_'+commit_hash_3, 'test_share')


time.sleep(0.1)
peer_A_process.terminate()





print '\n\n'
print '************************************************************************'
print '***Testing sending a full directory'
print '************************************************************************'



print '\n\n'
print '************************************************************************'
print '***Testing recieving a full directory'
print '************************************************************************'



print '\n\n'
print '************************************************************************'
print '***Testing sending a directory update'
logging.debug('Testing sending a directory update')
print '************************************************************************'
command_port+=2


peer_C = peer_service.peer_service(command_port)
peer_C.pm.storage_directory = peer_C_storage
peer_C.pm.my_machine_ID = 'machine_C'
peer_C.pm.add_share_to_machine('test_share','machine_C')
peer_C_process = Process(target = peer_C.serve_forever)
peer_C_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_A = peer_service.peer_service(command_port+1)
peer_A.pm.storage_directory = peer_A_storage
peer_A.pm.my_machine_ID = 'machine_A'
peer_A.pm.add_share_to_machine('test_share','machine_C')
peer_A.pm.connect_machine('machine_C','http://localhost:' +str(command_port))
peer_A.pm.push_update_to_peer('test_share', 'machine_C')


time.sleep(0.1)
peer_C_process.terminate()





print '\n\n'
print '************************************************************************'
print '***Testing receiving a directory update'
logging.debug('Testing receiving a directory update')
print '************************************************************************'




print '\n\n'
print '************************************************************************'
print '***Test saving and loading peer connection info'
logging.debug('Test saving and loading peer connection info')
print '************************************************************************'
command_port+=2
peer_C = peer_service.peer_service(command_port)
peer_C.pm.storage_directory = peer_C_storage
peer_C.pm.my_machine_ID = 'machine_C'
peer_C.pm.add_share_to_machine('test_share','machine_C')
peer_C.pm.add_share_to_machine('test_share','machine_A')
peer_C_process = Process(target = peer_C.serve_forever)
peer_C_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_A = peer_service.peer_service(command_port+1)
peer_A.pm.storage_directory = peer_A_storage
peer_A.pm.my_machine_ID = 'machine_A'
peer_A.pm.add_share_to_machine('test_share','machine_C')
peer_A.pm.add_share_to_machine('test_share','machine_A')
peer_A.pm.connect_machine('machine_C','http://localhost:' +str(command_port))


time.sleep(0.1)
peer_C_process.terminate()

print peer_A.pm.save_peer_info()
peer_A.pm.load_peer_info()


'''








print '\n\n'
print '************************************************************************'
print '***Testing finished'
logging.debug('Testing finished')
print '************************************************************************'













