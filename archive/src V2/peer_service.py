
import cloud_server
import peer_manager
import time
import logging

	
class peer_service():
	
	
	def __init__(self, command_port):
		logging.basicConfig(
				filename='peer_service.log',
				format='%(asctime)s | %(process)d | %(processName)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s',
				level=logging.DEBUG)
		self.pm = peer_manager.peer_manager()
		self.cs = cloud_server.cloud_server(command_port)
		self.cs.register_instance(self.pm)
		logging.debug('peer service initiated')




	def serve_forever(self):
		print 'peer service serving forever'
		while True:
			#poll for local working directory changes
			
			#poll for web xmlrpc calls
			self.cs.serve_a_bit(0.5)
			time.sleep(0.1)



		