#!/usr/bin/env python3
import logging
import threading
from common.utils import *
from common.custom_socket.server_socket import ServerSocket
from common.state_handler_safe import StateHandlerSafe

INITIAL_STATUS = 'READY'

from common.shared_value import SharedValue

class Interface():
    def __init__(self, id, api_port, internal_port, sentinels_amount, heartbeat_sender):
        self.sentinels_amount = sentinels_amount
        self.internal_socket = ServerSocket('', internal_port, 1)
        self.api_socket = ServerSocket('', api_port, 1)
        self.node_listener = threading.Thread(target=self._start_listening_nodes)
        self.client_listener = threading.Thread(target=self._start_listening_clients)
        self.heartbeat_sender = heartbeat_sender
        self.__init_state(id)

    def __init_state(self, id):
        self.state_handler = StateHandlerSafe(id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[INTERFACE] Found state {}".format(state))
            self.status = SharedValue(state["status"])
            self.sentinels_recieve = state["sentinels_recieve"]
        else:
            self.status = SharedValue(INITIAL_STATUS)
            self.sentinels_recieve = self.sentinels_amount
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"sentinels_recieve": self.sentinels_recieve,
        "status": self.status.read()})
    
    def _start_listening_nodes(self):
        while True:
            component_sock = self.internal_socket.accept()
            if not component_sock:
                continue
            logging.info("[INTERFACE] Component connection accepted")
            info = self.internal_socket.recv_from(component_sock)

            if len(info) == 0: #sentinel
                logging.info("[INTERFACE] Received 1 sentinel. Total Received: {}. Total Expected {}".format(self.sentinels_recieve+1, self.sentinels_amount))
                self.sentinels_recieve +=1
                if self.sentinels_recieve == self.sentinels_amount:
                    self.sentinels_recieve = 0
                    self.status.update('READY')
                    logging.info("[INTERFACE] Ready to recieve client requests. Change state to READY")
            self.__save_state()
            self.internal_socket.send_to(component_sock, ACK_SCHEME.pack(True), encode=False)
            component_sock.close()

    def _start_listening_clients(self):
        while True:
            client_sock = self.api_socket.accept()
            if not client_sock:
                continue
            logging.info("[INTERFACE] Client connection accepted")
            info = self.api_socket.recv_from(client_sock)

            if len(info) == 0: #sentinel
                logging.info("[INTERFACE] Received client request")
                if self.status.read() == 'READY':
                    self.sentinels_recieve = 0
                    self.status.update('RUNNING')
                    logging.info("[INTERFACE] Accepting request of client. Change state to RUNNING")
                    self.__save_state()
                    self.internal_socket.send_to(client_sock, ACK_SCHEME.pack(True), encode=False)
                    client_sock.close()
                    continue
            self.internal_socket.send_to(client_sock, ACK_SCHEME.pack(False), encode=False)
            client_sock.close()
        
    def start(self):
        self.heartbeat_sender.start()
        self.node_listener.start()
        self.client_listener.start()
        