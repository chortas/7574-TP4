import logging
import socket
from .base_socket import Socket

class ClientSocket(Socket):
    def __init__(self, address = None, connection = None):
        Socket.__init__(self)
        if address:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect(address)
        elif connection:
            self.socket = connection
    
    def connect(self, address):
        # Connect the socket to the port where the server is listening
        self.socket.connect(address)

    def set_timeout(self, timeout):
        self.socket.settimeout(timeout)