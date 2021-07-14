import os
import logging
import json

from .custom_socket.client_socket import ClientSocket
from .utils import ACK_SCHEME
from multiprocessing import Process
from time import sleep

class HeartbeatSender(Process):
    def __init__(self):
        Process.__init__(self)
        self.host = os.environ["MONITOR_IP"]
        self.monitor_port = int(os.environ["MONITOR_PORT"])
        self.id = os.environ["ID"]
        self.frequency = int(os.environ["FREQUENCY"])

    def run(self):
        try:
            logging.info("[HEARTBEAT_SENDER] Trying to connect with NODE")
            self.sock = ClientSocket(address = (self.host, self.monitor_port))
            self.sock.send_with_size(json.dumps({"id": self.id}))

            response = self.sock.recv_with_size()
            logging.info("[HEARTBEAT_SENDER] Recv port")
            self.port = int(response["port"])

            self.sock.close()

            logging.info(f"[HEARTBEAT_SENDER] Port received: {self.port}")
            heartbeat_listener_socket = ClientSocket(address = (self.host, self.port))

            while True:
                logging.info(f"[HEARTBEAT_SENDER] About to send heartbeat to {self.id}")
                heartbeat_listener_socket.send_with_size(json.dumps({"id": self.id}))
                sleep(self.frequency)

        except Exception as err:
            logging.info(f"[HEARTBEAT_SENDER] Failed sending heartbeat: {err}")
