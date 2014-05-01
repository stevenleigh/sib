
from packet import Packet


from multiprocessing import Queue, Manager
from Queue import PriorityQueue
import time
import logging
from multiprocessing import Process


class CongestionManager():
	
	
	def __init__(self):
		self.shared_sent_queue = None
		self.shared_recv_queue = None
		self.connect_details = None
		self.man = Manager()
		self.connect_summary = self.man.dict()
		self.sent_queue = PriorityQueue()
		self.recv_queue = PriorityQueue()
		self.proc = None
	
		
	def serve_forever_process(self):
		self.proc = Process(target = self.serve_forever)
		self.proc.start()
		return self.proc
	
	
		
	def serve_forever(self):
		"""
		"""
		logging.info("servering forever")
		while True:
			self.run_once()
			time.sleep(0.01)
	
	
		
	def run_once(self):
		self.process_shared_queues()
		self.compute_congest_stats()
		
		
	def process_shared_queues(self):
		while(not self.shared_sent_queue.empty()):
			p = self.shared_sent_queue.get()
			self.sent_queue.put((-p.send_time, p))  #Lowest value priority is popped.  Use -ve time to pop oldest packets
			
		while(not self.shared_recv_queue.empty()):
			p = self.shared_recv_queue.get()
			self.recv_queue.put(-p.recv_time, p)
			
	
	def compute_congest_stats(self):
		
		#Implement a really crappy congestion control algorithm for now.
		#pop old packets from send window
		if self.sent_queue.empty():
			return
		temp = self.sent_queue.get()
		(t, sent_p) = temp
		
		while ((sent_p.send_time < time.time() - 0.02) and (not self.sent_queue.empty())):
			temp = self.sent_queue.get()
			(t, sent_p) = temp

		self.sent_queue.put((-sent_p.send_time, sent_p))
		
		window = self.sent_queue.qsize()
		address = sent_p.to_address
		
		if not address in self.connect_summary:
			self.connect_summary.update({address:'unknown'})
		
		
		if window < 30:
			self.connect_summary[address] = 'CTS'  #Clear To Send
		else:
			self.connect_summary[address] = 'choke'  #restrict send
		#logging.debug('address: %s, window: %d, state: %s', address, window, self.connect_summary[address])
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		