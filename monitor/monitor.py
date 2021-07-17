#!/usr/bin/env python3
import logging
import json
from multiprocessing import Process
from common.custom_socket.server_socket import ServerSocket
from heartbeat_listener import HeartbeatListener

class Monitor():
    def __init__(self, internal_port, timeout):
        self.timeout = timeout
        self.internal_socket = ServerSocket('', internal_port, 1)
        self.nodes = {}
        self.port = 5000
        self.heartbeat_listeners = []
    
    def start(self):
        while True:
            component_sock = self.internal_socket.accept()
            if not component_sock:
                continue
            logging.info("[MONITOR] Node connection accepted")
            info = self.internal_socket.recv_from(component_sock)
            node_id = info["id"]
            logging.info(f"[MONITOR] Id: {node_id}")

            if node_id not in self.nodes:
                logging.info("[MONITOR] Id not registered")
                self.nodes[node_id] = self.port
                heartbeat_listener = HeartbeatListener(self.port, node_id, self.timeout)
                self.internal_socket.send_to(component_sock, json.dumps({"port": self.port}))
                heartbeat_listener.start()
                self.heartbeat_listeners.append(heartbeat_listener)               
                self.port += 1 
                
            else:
                logging.info("[MONITOR] Id already registered")
                self.internal_socket.send_to(component_sock, json.dumps({"port": self.nodes[node_id]}))

            component_sock.close()
