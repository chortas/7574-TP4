import logging
import json

from common.custom_socket.client_socket import ClientSocket
from threading import Thread

class HeartbeatSenderSingleMonitor(Thread):
    def __init__(self, node_id, monitor_host, monitor_port, start_election_callback, frequency):
        Thread.__init__(self)
        self.monitor_host = monitor_host
        self.monitor_port = monitor_port        
        self.id = node_id
        self.start_election = start_election_callback
        self.frequency = frequency

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
