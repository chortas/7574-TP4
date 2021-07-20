import os
import logging
import json

from .custom_socket.client_socket import ClientSocket
from .utils import ACK_SCHEME
from multiprocessing import Process
from time import sleep

class HeartbeatSender(Process):
    def __init__(self, node_id = None):
        Process.__init__(self)
        self.hosts = os.environ["MONITOR_IPS"].split(',')
        logging.info(f"Hosts: {self.hosts}")
        self.monitor_port = int(os.environ["MONITOR_PORT"])        
        self.id = node_id if node_id else os.environ["ID"]
        self.frequency = int(os.environ["FREQUENCY"])
        self.act_idx = 0

    def __init_port(self):
        act_host = self.hosts[self.act_idx]

        logging.info("[HEARTBEAT_SENDER] Trying to connect with node")
        logging.info(f"[HEARTBEAT_SENDER] Host: {act_host}, port: {self.monitor_port}")

        self.sock = ClientSocket(address = (act_host, self.monitor_port))

        self.sock.send_with_size(json.dumps({"id": self.id}))

        response = self.sock.recv_with_size()
        logging.info("[HEARTBEAT_SENDER] Recv port")
        self.port = int(response["port"])

        self.sock.close()

        logging.info(f"[HEARTBEAT_SENDER] Port received: {self.port}")

    def __send_heartbeats(self):
        act_host = self.hosts[self.act_idx]
        logging.info(f"[HEARTBEAT_SENDER] Act host: {act_host}")
        heartbeat_listener_socket = ClientSocket(address = (act_host, self.port))

        while True:
            #logging.info(f"[HEARTBEAT_SENDER] About to send heartbeat to {self.id}")
            heartbeat_listener_socket.send_with_size(json.dumps({"id": self.id}))
            sleep(self.frequency)

    def run(self):
        self.__init_port()
        while True:
            try:
                self.__send_heartbeats()
            except Exception as err:
                logging.info(f"[HEARTBEAT_SENDER] Failed sending heartbeat: {err}")
                sleep(self.frequency)
                self.act_idx = (self.act_idx + 1) % len(self.hosts)
                self.__init_port()
                continue # retry
        
