


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from multiprocessing import Process, Manager
import time
import logging
import random
import sib



class AutoSync(FileSystemEventHandler):
	
	
	def __init__(self, key, monitoring_directory, storage_directory, share_ID, user_name, machine_ID, command_port, json_response_dict, min_update_interval=10):
		self.key = key
		self.monitoring_directory = monitoring_directory
		self.storage_directory = storage_directory
		self.share_ID = share_ID
		self.user_name = user_name
		self.machine_ID = machine_ID
		self.command_port = command_port
		self.json_response_dict = json_response_dict
		self.min_update_interval = min_update_interval
		

	def on_any_event(self, event):
		logging.debug('auto sync directory event triggered')
		time.sleep(0.1)  #ignore any transient changes
		
		my_rpc_id = random.randint(1,1000000) #TODO: rpc_id collisions could occur
		sib.cmd(method_name='commit', params=[self.key, self.monitoring_directory, self.share_ID, self.user_name, 'auto', None, None], to=('localhost', self.command_port), rpc_id = my_rpc_id)
		while my_rpc_id not in self.json_response_dict:
			time.sleep(0.1)
		commit_packet = self.json_response_dict[my_rpc_id]
		commit_hash = commit_packet.json_RPC_object['result']
		
		sib.cmd(method_name='push_update_to_peer', params=[self.share_ID, None, commit_hash], to=('localhost', self.command_port))
		time.sleep(4)  #@TODO:  wait until pushing updates is complete, then run next command
		#operation_commands.socket_command(method_name='sync_new_commit', params=[self.key, commit_hash, self.share_ID], to=('localhost', self.command_port))
		
	
	



class ObserverWrapper():

	def __init__(self, key, monitoring_directory, storage_directory, share_ID, user_name, machine_ID, command_port, json_response_dict, min_update_interval, command_dict):
		self.key = key
		self.monitoring_directory = monitoring_directory
		self.storage_directory = storage_directory
		self.share_ID = share_ID
		self.user_name = user_name
		self.machine_ID = machine_ID
		self.command_port = command_port
		self.json_response_dict = json_response_dict
		self.min_update_interval = min_update_interval
		self.command_dict = command_dict
		
		
		
	def run(self):
		self.a_s = AutoSync(self.key, self.monitoring_directory, self.storage_directory, self.share_ID, self.user_name, self.machine_ID, self.command_port, self.json_response_dict, self.min_update_interval)	
		self.observer = Observer()  #The observer objects can't cross process boundaries because they are unpicklable
		self.observer.schedule(self.a_s, self.monitoring_directory, recursive=True)
		self.observer.start()
		while True:
			if self.monitoring_directory not in self.command_dict:
				time.sleep(0.1)
				continue
			command = self.command_dict[self.monitoring_directory]
			if command == 'stop' and self.observer.isAlive():
				logging.debug('stopping observer')
				self.observer.stop()
			elif command == 'start' and not self.observer.isAlive():
				logging.debug('starting observer')
				self.observer.start()
			elif command == 'terminate':
				logging.debug('terminating observer')
				if self.observer.isAlive():
					self.observer.stop()
				self.observer.unschedule_all()
				return

	
	def start(self):
		proc = Process(target=self.run)
		proc.start()
		logging.info('observer started')




class AutoSyncManager():
	"""Manages the watchdog event handlers.  
	The event handlers each run in a different process.
	"""
	def __init__(self, json_response_dict):
		self.manager = Manager()
		self.command_dict = self.manager.dict()
		self.o_w_list = []
	
	def create(self, key, monitoring_directory, storage_directory, share_ID, user_name, machine_ID, command_port, json_response_dict, min_update_interval=10):
			
		o_w = ObserverWrapper(key, monitoring_directory, storage_directory, share_ID, user_name, machine_ID, command_port, json_response_dict, min_update_interval, self.command_dict)
		o_w.start()
		#o_w.observer.start()
		#o_w.run()
		self.o_w_list.append(o_w)
		
		
	def start(self, working_directory):
		self.command_dict.update({working_directory:'start'})  #TODO: any sort of feedback from this?
		
	def stop(self, working_directory):
		self.command_dict.update({working_directory:'stop'})
		
	def terminate(self, working_directory):
		self.command_dict.update({working_directory:'terminate'})
































