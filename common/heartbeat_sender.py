import os
import logging
import json

from .custom_socket.client_socket import ClientSocket
from .utils import ACK_SCHEME
from multiprocessing import Process
from time import sleep
from common.state_handler import StateHandler

class HeartbeatSender(Process):
    def __init__(self, node_id = None):
        Process.__init__(self)
        self.hosts = os.environ["MONITOR_IPS"].split(',')
        logging.info(f"Hosts: {self.hosts}")
        self.monitor_port = int(os.environ["MONITOR_PORT"])        
        self.id = node_id if node_id else os.environ["ID"]
        self.frequency = int(os.environ["FREQUENCY"])
        self.__init_state(self.id)

    def __init_state(self, id):
        self.state_handler = StateHandler(id, filename = "heartbeat_info.json")
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info(f"[HEARTBEAT_SENDER] Found state: {state}")
            self.act_idx = state["act_idx"]
        else:
            logging.info("[HEARTBEAT_SENDER] State not found")
            self.act_idx = 0
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"act_idx": self.act_idx})

    def __init_port(self):
        act_host = self.hosts[self.act_idx]

        logging.info(f"[HEARTBEAT_SENDER] Trying to connect with node ({act_host}, {self.monitor_port})")

        self.sock = ClientSocket(address = (act_host, self.monitor_port))

        self.sock.send_with_size(json.dumps({"id": self.id}))

        response = self.sock.recv_with_size()
        logging.info("[HEARTBEAT_SENDER] Recv port")
        self.port = int(response["port"])

        self.sock.close()

        logging.info(f"[HEARTBEAT_SENDER] Port received: {self.port}")

    def __send_heartbeats(self):
        act_host = self.hosts[self.act_idx]

        try:
            logging.info(f"[HEARTBEAT_SENDER] Act host: {act_host}")
            heartbeat_listener_socket = ClientSocket(address = (act_host, self.port))

            while True:
                #logging.info(f"[HEARTBEAT_SENDER] Sending heartbeat from {self.id} to ({act_host},{self.port})")
                heartbeat_listener_socket.send_with_size(json.dumps({"id": self.id}))
                #logging.info(f"[HEARTBEAT_SENDER] About to sleep: {self.id}")
                #sleep(self.frequency)

        except Exception as err:
            logging.info(f"[HEARTBEAT_SENDER] Failed sending heartbeat: {err}")
            self.act_idx = (self.act_idx + 1) % len(self.hosts)
            self.__save_state()
            self.__init_port()
            self.__send_heartbeats() # retry

    def run(self):
        self.__init_port()
        self.__send_heartbeats()
