



from local_blob_manager import local_blob_manager


from watchdog.events import FileSystemEventHandler
import time
import logging
import os

class auto_sync (FileSystemEventHandler):
	
	
	def __init__(self, key, monitoring_directory, storage_directory, share_ID, user_name, machine_ID, min_update_interval=10):
		self.key = key
		self.monitoring_directory = monitoring_directory
		self.storage_directory = storage_directory
		self.share_ID = share_ID
		self.user_name = user_name
		self.machine_ID = machine_ID
		self.min_update_interval = min_update_interval



	def on_any_event(self, event):
		logging.debug('auto sync directory event triggered')
		time.sleep(0.1)  #ignore any transient changes
		bm = local_blob_manager()
		bm.commit_directory(self.key, self.monitoring_directory, os.path.join(self.storage_directory, self.share_ID), 
						self.user_name, 'auto', None, None)  #TODO: real value for parent commit
		