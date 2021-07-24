import logging

from threading import Thread
from common.custom_socket.server_socket import ServerSocket
from socket import timeout

class HeartbeatListener(Thread):
    def __init__(self, port_to_recv, node_id, timeout, is_leader, restart_node_callback):
        Thread.__init__(self)
        self.socket = ServerSocket('', port_to_recv, 1)
        self.id = node_id
        self.timeout = timeout
        self.is_leader = is_leader
        logging.info(f"Constructor heartbeat listener {self.id} {port_to_recv}")
        self.__restart_node = restart_node_callback

    def run(self):
        component_sock = self.socket.accept()

        while True:
            if not component_sock:
                component_sock = self.socket.accept()
                continue
            
            #logging.info(f"[HEARTBEAT_LISTENER] I'm {self.id} and I accepted a node connection")
            try:
                info = self.socket.recv_from(component_sock, recv_timeout = self.timeout)
                if info["id"] == id:
                    continue
                else:
                    # TODO: redirect request to monitor
                    pass

            except:
                if "monitor" in self.id and not self.is_leader.read(): continue
                logging.info(f"[HEARTBEAT_LISTENER] The id {self.id} has died :'(")
                self.__restart_node(self.id)
                component_sock = self.socket.accept(timeout=self.timeout) #TODO: IMPROVE
                while not component_sock:
                    logging.info(f"[HEARTBEAT_LISTENER] The id {self.id} has not started. Retrying")
                    self.__restart_node(self.id)
                    component_sock = self.socket.accept(timeout=self.timeout)

        component_sock.close()
