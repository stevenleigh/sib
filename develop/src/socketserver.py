


from packet import Packet

import select
import errno
import logging
import socket
from multiprocessing import Process
import time

class SocketServer():
	
	
	
	def __init__(self):
		self.listen_sockets = []
		self.new_sockets = None
		self.raw_in_queue = None
		self.my_sockets = []
	
	
	def serve_forever_process(self):
		proc = Process(target = self.serve_forever)
		proc.start()
		return proc
	
	
	def serve_forever(self):
		"""
		"""
		logging.info("Serving forever")
		while True:
			if not self.serve_once():
				time.sleep(0.1)
			if not self.new_sockets.empty():
				self.add_socket(port = self.new_sockets.get())

	
	
	
	def serve_once(self, poll_interval = 0):
		processed = False
		#logging.debug('listening on socket fileno: %s' %(self.listen_sockets))
		try:
			r, w, e = select.select(self.listen_sockets, [], [], poll_interval)
			#logging.debug('readable socket fileno: %s' %(r))
		except IOError as e:
			print "I/O error({0}): {1}".format(e.errno, e.strerror)
			logging.debug("I/O error({0}): {1}".format(e.errno, e.strerror))
			raise
		except (OSError, select.error) as e:
			if e.args[0] != errno.EINTR:
				raise
		
		for sock in r:
			#read socket into Packet
			#pop Packet onto Queue
			logging.debug('reading in socket')
			processed = True
			p = Packet()
			p.read_from_socket(sock)
			p.recv_time = time.time()
			self.raw_in_queue.put(p)
		return processed
			
			

	def add_socket(self, port = None, sock = None):
		"""Tell the server to listen on a particular port or socket
		"""
		if port != None:
			s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			s.bind(('', port))
		elif sock != None:
			s = sock
		else:
			return
		self.my_sockets.append(s)
		self.listen_sockets.extend([s.fileno()])
		logging.info('Added listening socket.  port: %d, FID: %d' %(port, s.fileno()))















