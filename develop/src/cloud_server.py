

from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler

import select
import errno
import time


def _eintr_retry(func, *args):
	"""restart a system call interrupted by EINTR"""
	while True:
		try:
			return func(*args)
		except (OSError, select.error) as e:
			if e.args[0] != errno.EINTR:
				raise

# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
	rpc_paths = ('/RPC2',)

class cloud_server(SimpleXMLRPCServer):
	
	
	def __init__(self, command_port):
		SimpleXMLRPCServer.__init__(self, ("0.0.0.0", command_port), requestHandler=RequestHandler, allow_none=True)
		#self.requestHandler=RequestHandler
		#self.register_introspection_functions()
		
		
	def serve_a_bit(self, poll_interval):
		"""Handle one request at a time until shutdown.

        Polls for shutdown every poll_interval seconds. Ignores
        self.timeout. If you need to do periodic tasks, do them in
        another thread.
        """
		start_time = time.time()

		while (time.time() < start_time + poll_interval):
			# XXX: Consider using another file descriptor or
			# connecting to the socket to wake this up instead of
			# polling. Polling reduces our responsiveness to a
			# shutdown request and wastes cpu at all other times.
			r, w, e = _eintr_retry(select.select, [self], [], [],
								   poll_interval)
			if self in r:
				self._handle_request_noblock()




