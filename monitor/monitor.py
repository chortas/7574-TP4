#!/usr/bin/env python3
import logging
import json
from multiprocessing import Process
from common.custom_socket.server_socket import ServerSocket
from heartbeat_listener import HeartbeatListener
from common.state_handler import StateHandler
from heartbeat_manager import HeartbeatManager
from common.shared_value import SharedValue

class Monitor():
    def __init__(self, id, internal_port, timeout, is_leader):
        self.timeout = timeout
        self.internal_socket = ServerSocket('', internal_port, 1)
        self.heartbeat_listeners = {}
        self.init_port = 5000
        self.is_leader = SharedValue(is_leader) #default
        self.heartbeat_manager = HeartbeatManager(id, self.change_is_leader)
        self.__init_state(id, is_leader)

    def __init_state(self, id, is_leader):
        self.state_handler = StateHandler(id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[MONITOR] Found state {}".format(state))
            self.nodes = state["nodes"]
            self.last_port = state["last_port"]
            self.is_leader.update(state["is_leader"])
            for id, port in self.nodes.items():
                heartbeat_listener = HeartbeatListener(port, id, self.timeout, self.is_leader)
                heartbeat_listener.start()
                if "monitor" in id and not self.is_leader.read(): continue
                self.heartbeat_listeners[id] = heartbeat_listener
        else:
            self.nodes = {}
            self.last_port = self.init_port
            self.is_leader.update(is_leader)
            self.__save_state()
        logging.info(f"[MONITOR]Im leader? {self.is_leader.read()}")

    def __save_state(self):
        self.state_handler.update_state({"nodes": self.nodes,
        "last_port": self.last_port, "is_leader": self.is_leader.read()})

    def change_is_leader(self, is_it):
        logging.info(f"[MONITOR] Im changing is_leader to: {is_it}")
        self.is_leader.update(is_it)
    
    def start(self):
        self.heartbeat_manager.start()
        while True:
            logging.info("[MONITOR] Hearing nodes")
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
                heartbeat_listener = HeartbeatListener(self.nodes[node_id], node_id, self.timeout, self.is_leader)
                self.internal_socket.send_to(component_sock, json.dumps({"port": self.nodes[node_id]}))
                heartbeat_listener.start()
                self.heartbeat_listeners[node_id] = heartbeat_listener
                
            else:
                logging.info("[MONITOR] Id already registered")
                self.internal_socket.send_to(component_sock, json.dumps({"port": self.nodes[node_id]}))

            component_sock.close()
