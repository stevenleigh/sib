


import operation_commands

from watchdog.events import FileSystemEventHandler
import time
import logging
import random


class AutoSync (FileSystemEventHandler):
	
	
	def __init__(self, key, monitoring_directory, storage_directory, share_ID, user_name, machine_ID, command_port, json_response_dict, min_update_interval=10):
		self.key = key
		self.monitoring_directory = monitoring_directory
		self.storage_directory = storage_directory
		self.share_ID = share_ID
		self.user_name = user_name
		self.machine_ID = machine_ID
		self.command_port = command_port
		self.min_update_interval = min_update_interval
		self.json_response_dict = json_response_dict
		


	def on_any_event(self, event):
		logging.debug('auto sync directory event triggered')
		time.sleep(0.1)  #ignore any transient changes
		
		my_rpc_id = random.randint(1,1000000) #TODO: rpc_id collisions could occur
		operation_commands.socket_command(method_name='commit', params=[self.key, self.monitoring_directory, self.share_ID, self.user_name, 'auto', None, None], to=('localhost', self.command_port), rpc_id = my_rpc_id)
		while my_rpc_id not in self.json_response_dict:
			time.sleep(0.1)
		commit_packet = self.json_response_dict[my_rpc_id]
		commit_hash = commit_packet.json_RPC_object['result']
		
		operation_commands.socket_command(method_name='push_update_to_peer', params=[self.share_ID, None, commit_hash], to=('localhost', self.command_port))
		time.sleep(4)  #@TODO:  wait until pushing updates is complete, then run next command
		#operation_commands.socket_command(method_name='sync_new_commit', params=[self.key, commit_hash, self.share_ID], to=('localhost', self.command_port))
		









