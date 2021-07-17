import logging
from .utils import *
from .client_socket import ClientSocket
from .base_socket import Socket

class ServerSocket(Socket):
    def __init__(self, host, port, listen_backlog):
        Socket.__init__(self)
        self.bind_listen(host, port, listen_backlog)   
        
    def bind_listen(self, host, port, listen_backlog):
        self.socket.bind((host, port))
        self.socket.listen(listen_backlog)
        
    def accept(self, timeout=None):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        try:
            if timeout:
                self.socket.settimeout(timeout)
            # Connection arrived
            c, addr = self.socket.accept()
            logging.info('Got connection from {}'.format(addr))
            return ClientSocket(connection = c)
        except socket.timeout:
            return None

    def send_to(self, client_sock, data, encode=True):
        client_sock.send_with_size(data, encode)

    def recv_from(self, client_sock, decode = True, recv_timeout = 0):
        if recv_timeout:
            client_sock.set_timeout(recv_timeout)
        return client_sock.recv_with_size(decode)