import logging
import subprocess

from multiprocessing import Process
from common.custom_socket.server_socket import ServerSocket
from socket import timeout

class HeartbeatListener(Process):
    def __init__(self, port_to_recv, id, timeout):
        Process.__init__(self)
        logging.info("Constructor heartbeat listener")
        self.socket = ServerSocket('', port_to_recv, 1)
        self.id = id
        self.timeout = timeout

    def run(self):
        component_sock = self.socket.accept()

        #logging.info("[HEARTBEAT_LISTENER] Antes del while")
        while True:
            if not component_sock:
                component_sock = self.socket.accept()
                continue
            
            logging.info(f"[HEARTBEAT_LISTENER] I'm {self.id} and I accepted a node connection")
            try:
                info = self.socket.recv_from(component_sock, recv_timeout = self.timeout)
                if info["id"] == id:
                    continue
                else:
                    # TODO: redirect request to monitor
                    pass

            except:
                logging.info(f"[HEARTBEAT_LISTENER] The id {self.id} has died :'(")
                result = subprocess.run(['docker', 'start', self.id], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging.info('Command executed. Result={}. Output={}. Error={}'.format(result.returncode, result.stdout, result.stderr))
                component_sock = self.socket.accept(timeout=self.timeout) #TODO: IMPROVE
                while not component_sock:
                    logging.info(f"[HEARTBEAT_LISTENER] The id {self.id} has not started. Retrying")
                    result = subprocess.run(['docker', 'start', self.id], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    logging.info('Command executed. Result={}. Output={}. Error={}'.format(result.returncode, result.stdout, result.stderr))
                    component_sock = self.socket.accept(timeout=self.timeout)

            
        component_sock.close()
