import logging
from .utils import *
from .client_socket import ClientSocket
from .base_socket import Socket

class ServerSocket(Socket):
    def __init__(self, host, port, listen_backlog):
        Socket.__init__(self)
        self.socket.settimeout(0.2) # timeout for listening
        self.bind_listen(host, port, listen_backlog)   
        
    def bind_listen(self, host, port, listen_backlog):
        self.socket.bind((host, port))
        self.socket.listen(listen_backlog)


    def accept(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        try:
            # Connection arrived
            c, addr = self.socket.accept()
            logging.info('Got connection from {}'.format(addr))
            return ClientSocket(connection = c)
        except socket.timeout:
            return None

    def send_to(self, client_sock, data, encode=True):
        client_sock.send_with_size(data, encode)

    def recv_from(self, client_sock, decode = True):
        return client_sock.recv_with_size(decode)