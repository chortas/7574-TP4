import socket
import logging
import json
from .utils import *

class Socket:
    def __init__(self):
        # Initialize server socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       

    def send_with_size(self, data, encode=True):
        self._send(self.socket, number_to_8_bytes(len(data)))
        data_to_send = data
        if encode:
            data_to_send = str.encode(data, 'utf-8')
        self._send(self.socket, data_to_send)

    def recv_with_size(self, decode = True):
        size = bytes_8_to_number(self._recv(self.socket, NUMBER_SIZE))
        data = self._recv(self.socket, size)
        if decode:
            return json.loads(data.decode('utf-8'))
        return data

    def _send(self, sock, data):
        try:
            sock.sendall(data)
        except:
            raise RuntimeError("Socket connection failed unexpectedly while sending")

    def _recv(self, sock, size):
        data_received = bytearray()
        bytes_received = 0
        while bytes_received < size:
            chunk = sock.recv(size - bytes_received)
            if not chunk:
                raise RuntimeError("Socket connection failed unexpectedly while receiving")
            bytes_received += len(chunk)
            data_received.extend(chunk)
        return data_received

    def close(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            pass
        self.socket.close()