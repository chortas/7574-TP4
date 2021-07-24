import os
import logging
import json

from common.custom_socket.client_socket import ClientSocket
from common.custom_socket.server_socket import ServerSocket
from common.shared_value import SharedValue
from common.utils import ACK_SCHEME
from threading import Thread
from time import sleep
from common.state_handler_safe import StateHandlerSafe

class HeartbeatSenderSingleMonitor(Thread):
    def __init__(self, node_id, monitor_host, monitor_port, start_election_callback):
        Thread.__init__(self)
        self.monitor_host = monitor_host
        self.monitor_port = monitor_port        
        self.id = node_id
        self.start_election=start_election_callback

    def __init_port(self):
        logging.info(f"[HEARTBEAT_SENDER] Trying to connect with node ({self.monitor_host}, {self.monitor_port})")
        while True:
            
            try:
                self.sock = ClientSocket(address = (self.monitor_host, self.monitor_port))
                self.sock.send_with_size(json.dumps({"id": self.id}))

                response = self.sock.recv_with_size()
                logging.info(f"[HEARTBEAT_SENDER] Recv port: {response}")
                self.port = int(response["port"])

                self.sock.close()

                logging.info(f"[HEARTBEAT_SENDER] Port received: {self.port}")
                break
            
            except Exception as err:
                self.start_election(self.monitor_host)
                continue


    def __send_heartbeats(self):
        while True:
            try:
                heartbeat_listener_socket = ClientSocket(address = (self.monitor_host, self.port))

                while True:
                    heartbeat_listener_socket.send_with_size(json.dumps({"id": self.id}))

            except Exception as err:
                logging.info(f"[HEARTBEAT_SENDER] Failed sending heartbeat: {err}")
                self.__init_port()
                self.__send_heartbeats() # retry

    def run(self):
        logging.info(f"[HEARTBEAT_SENDER] Init for host {self.monitor_host}")
        self.__init_port()
        self.__send_heartbeats()
