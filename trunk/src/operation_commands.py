


from commit_blob import commit_blob

import os
import socket
import random
import logging
import json

def print_all_commits(key, my_storage):
	cb = commit_blob()
	for root, dirs, files in os.walk(my_storage):
		for name in files:
			if name[0]=='_':  #commit filenames start with '_'
				cb.load(key, root, name)
				cb.display()

def socket_command(method_name, params, to, blocking = False, congest=None, ver=1.0, frm=None, rpc_id=None, TTL=None):
	logging.debug('[method_name, params, to, blocking, congest, ver, frm, rpc_id, TTL]: %s' %([method_name, params, to, blocking, congest, ver, frm, rpc_id, TTL]))
	if rpc_id==None:
		rpc_id=random.randint(1,10000)
	msg_dict = dict()
	msg_dict.update({'jsonrpc':2.0})
	msg_dict.update({'method':method_name})
	msg_dict.update({'params':[ver, congest, params]})
	msg_dict.update({'id':rpc_id})
	logging.debug('msg_dict: %s' %(msg_dict))
	rpc_msg = json.dumps(msg_dict)
	s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	if frm!= None:
		s2.bind(('',frm))
	s2.setblocking(0)
	s2.sendto(rpc_msg, to)
	logging.debug('Sent msg: %s, to: %s, from: %s, rpcID: %d' %(rpc_msg, to, frm, rpc_id))
	
	ret_msg = None
	if blocking:
		ret_msg = s2.recv(65507)  #65507 is max UDP packet size for IPv4
	s2.close()
	return ret_msg
	
	
	
	'''
def common_commands():
	
	
	
	
####For Desktop
key=b'Sixteen byte key'

#home = expanduser("~")
my_storage = '../storage'
my_working = '../working'
share_ID ='live_test'
laptop_url = '192.168.2.35'
my_machine_ID = 'desktop'
command_port = 43434


my_sib = sib.SIB()
my_sib.ss.add_socket(port = command_port)
my_sib.js.storage_directory = my_storage
my_sib.js.my_machine_ID = my_machine_ID
my_sib.js.command_port = command_port
my_sib.run_forever()

"""
operation_commands.socket_command(method_name='ping', params = None, to=('localhost',command_port))
operation_commands.socket_command(method_name='update_machine_address', params=['laptop', laptop_url, 43435], to=('localhost',command_port))
operation_commands.socket_command(method_name='add_share_to_machine', params=[share_ID, my_machine_ID], to=('localhost', command_port))
operation_commands.socket_command(method_name='add_share_to_machine', params=[share_ID, 'laptop'], to=('localhost', command_port))
operation_commands.socket_command(method_name='register_auto_sync', params=[key, my_working, share_ID,'auto_sync_desktop', 10], to=('localhost',command_port))
"""








###For Laptop
key=b'Sixteen byte key'

#home = expanduser("~")
my_storage = '../storage'
my_working = '../working'
share_ID ='live_test'
desktop_url = '192.168.2.34'
my_machine_ID = 'laptop'
command_port = 43435


my_sib = sib.SIB()
my_sib.ss.add_socket(port = command_port)
my_sib.js.storage_directory = my_storage
my_sib.js.my_machine_ID = my_machine_ID
my_sib.js.command_port = command_port
my_sib.run_forever()

"""
operation_commands.socket_command(method_name='ping', params = None, to=('localhost',command_port))
operation_commands.socket_command(method_name='update_machine_address', params=['desktop', desktop_url, 43434], to=('localhost',command_port))
operation_commands.socket_command(method_name='add_share_to_machine', params=[share_ID, my_machine_ID], to=('localhost', command_port))
operation_commands.socket_command(method_name='add_share_to_machine', params=[share_ID, 'dekstop'], to=('localhost', command_port))
operation_commands.socket_command(method_name='register_auto_sync', params=[key, my_working, share_ID,'auto_sync_desktop', 10], to=('localhost',command_port))
"""



#commands for managing local commits
bm=local_blob_manager()	
bm.commit_directory(key, my_working, os.path.join(my_storage, share_ID), 'user_name','commit msg')
bm.restore_directory(key, my_working, os.path.join(my_storage, share_ID), 'commit_hash')

'''







