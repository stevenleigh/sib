


from file_blob import file_blob
from commit_blob import commit_blob
from local_blob_manager import local_blob_manager
import time
from multiprocessing import Process
import os
#from peer_manager import peer_manager
import peer_service
import xmlrpclib
import random
import logging
import shutil

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



print '\n\n'
print '************************************************************************'
print '***Testing network connections'
logging.debug('Testing network connections')
print '************************************************************************'
command_port = random.randint(20000,50000)


peer_B = peer_service.peer_service(command_port)
peer_B_process = Process(target = peer_B.serve_forever)
peer_B_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_A = peer_service.peer_service(command_port+1)
peer_B_proxy = peer_A.pm.connect_machine('machine_B','http://localhost:' +str(command_port))
print peer_B_proxy.ping()


time.sleep(0.1)
peer_B_process.terminate()



print '\n\n'
print '************************************************************************'
print '***Testing network blob transfer to peer'
logging.debug('Testing network blob transfer to peer')
print '************************************************************************'
command_port+=2


peer_B = peer_service.peer_service(command_port)
peer_B.pm.storage_directory = peer_B_storage
peer_B.pm.my_machine_ID = 'machine_B'
peer_B.pm.add_share_to_machine('test_share','machine_B')
peer_B_process = Process(target = peer_B.serve_forever)
peer_B_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_A = peer_service.peer_service(command_port+1)
peer_A.pm.storage_directory = peer_A_storage
peer_B_proxy = peer_A.pm.connect_machine('machine_B','http://localhost:' +str(command_port))

print peer_B_proxy.save_file('test_share', fb_hash, xmlrpclib.Binary(f.read()))


time.sleep(0.1)
peer_B_process.terminate()



print '\n\n'
print '************************************************************************'
print '***Testing network blob transfer from peer'
logging.debug('Testing network blob transfer from peer')
print '************************************************************************'
command_port+=2


peer_B = peer_service.peer_service(command_port)
peer_B.pm.storage_directory = peer_B_storage
peer_B.pm.my_machine_ID = 'machine_B'
peer_B.pm.add_share_to_machine('test_share','machine_B')
peer_B_process = Process(target = peer_B.serve_forever)
peer_B_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_A = peer_service.peer_service(command_port+1)
peer_A.pm.storage_directory = peer_A_storage
peer_B_proxy = peer_A.pm.connect_machine('machine_B','http://localhost:' +str(command_port))
(peer_B_proxy.get_file('test_share', fb_hash)).data


time.sleep(0.1)
peer_B_process.terminate()



print '\n\n'
print '************************************************************************'
print '***Testing large network blob transfer to peer'
logging.debug('Testing large network blob transfer to peer')
print '************************************************************************'
command_port +=2
large_file = open('../resource/alice.txt','rb')
fb=file_blob()
fb.compute_delta(key,large_file.read())
large_file_hash = fb.store(key, peer_A_storage)


peer_B = peer_service.peer_service(command_port)
peer_B.pm.storage_directory = peer_B_storage
peer_B.pm.my_machine_ID = 'machine_B'
peer_B.pm.add_share_to_machine('test_share','machine_B')
peer_B_process = Process(target = peer_B.serve_forever)
peer_B_process.start()
time.sleep(0.1)  #wait for peer process and socket creation
print 'server start finished'


peer_A = peer_service.peer_service(command_port+1)
peer_A.pm.storage_directory = peer_A_storage
peer_B_proxy = peer_A.pm.connect_machine('machine_B','http://localhost:' +str(command_port))

print peer_B_proxy.save_file('test_share', large_file_hash, xmlrpclib.Binary(large_file.read()))


time.sleep(0.1)
peer_B_process.terminate()




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
print '***Testing printing all commit info transfered to peer C'
logging.debug('Testing printing all commit info transfered to peer C')
print '************************************************************************'
cb = commit_blob()
for root, dirs, files in os.walk(peer_C_storage):
	for name in files:
		if name[0]=='_':  #commit filenames start with '_'
			cb.load(key, peer_C_storage, name)
			cb.display()




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




print '\n\n'
print '************************************************************************'
print '***Testing automatic sync'
logging.debug('Testing automatic sync')
print '************************************************************************'
command_port+=2


peer_A = peer_service.peer_service(command_port)
peer_A.pm.storage_directory = peer_A_storage
peer_A.pm.my_machine_ID = 'machine_A'
peer_A.pm.add_share_to_machine('test_share','machine_C')
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
peer_C.pm.register_auto_sync(key, '../resource/restore_directory_3', 'test_share','auto_sync_user');

#do some file operations.  A new commit should be created for each one.
time.sleep(0.1)
#copy a file
shutil.copy('../resource/restore_directory_3/root/alice.txt', '../resource/restore_directory_3/root/alice_copy.txt')
time.sleep(0.1)
#edit a file
f_auto = open('../resource/restore_directory_3/root/alice_copy.txt', 'a')
f_auto.write('a bunch of mumbo jumbo.  a bunch of mumbo jumbo.  a bunch of mumbo jumbo')
f_auto.close()
time.sleep(0.1)
#remove a file
os.remove('../resource/restore_directory_3/root/alice_copy.txt')
time.sleep(0.1)

time.sleep(0.1)
peer_A_process.terminate()









print '\n\n'
print '************************************************************************'
print '***Testing finished'
logging.debug('Testing finished')
print '************************************************************************'













