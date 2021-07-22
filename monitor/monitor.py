#!/usr/bin/env python3
import logging
import json
from multiprocessing import Process
from common.custom_socket.server_socket import ServerSocket
from heartbeat_listener import HeartbeatListener
from common.state_handler import StateHandler

class Monitor():
    def __init__(self, id, internal_port, timeout):
        self.timeout = timeout
        self.internal_socket = ServerSocket('', internal_port, 1)
        self.heartbeat_listeners = []
        self.init_port = 5000
        self.__init_state(id)

    def __init_state(self, id):
        self.state_handler = StateHandler(id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[MONITOR] Found state {}".format(state))
            self.nodes = state["nodes"]
            self.last_port = state["last_port"]
            for id, port in self.nodes.items():
                heartbeat_listener = HeartbeatListener(port, id, self.timeout)
                heartbeat_listener.start()
                self.heartbeat_listeners.append(heartbeat_listener)
        else:
            self.nodes = {}
            self.last_port = self.init_port
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"nodes": self.nodes,
        "last_port": self.last_port})
    
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
                self.nodes[node_id] = self.last_port
                self.last_port += 1
                self.__save_state() 
                heartbeat_listener = HeartbeatListener(self.nodes[node_id], node_id, self.timeout)
                self.internal_socket.send_to(component_sock, json.dumps({"port": self.nodes[node_id]}))
                heartbeat_listener.start()
                self.heartbeat_listeners.append(heartbeat_listener)
                
            else:
                logging.info("[MONITOR] Id already registered")
                self.internal_socket.send_to(component_sock, json.dumps({"port": self.nodes[node_id]}))

            component_sock.close()
