#!/usr/bin/env python3
import logging
from common.utils import *
from common.custom_socket.server_socket import ServerSocket

INITIAL_STATE = 'READY'

class Interface():
    def __init__(self, api_port, internal_port, sentinels_amount):
        self.sentinels_amount = sentinels_amount
        self.state = INITIAL_STATE
        self.internal_socket = ServerSocket('', internal_port, 1)
        self.sentinels_recieve = 0
    
    def start(self):
        while True:
            component_sock = self.internal_socket.accept()
            if not component_sock:
                continue
            info = self.internal_socket.recv_from(component_sock)

            if len(info) == 0: #sentinel
                logging.info("[INTERFACE] Received 1 sentinel")
                self.sentinels_recieve +=1
                if self.sentinels_recieve == self.sentinels_amount:
                    self.sentinels_recieve = 0
                    self.state = 'READY'
                    logging.info("[INTERFACE] Ready to recieve client requests")

            self.internal_socket.send_to(component_sock, ACK_SCHEME.pack(True), encode=False)
            component_sock.close()
        
        