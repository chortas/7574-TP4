import os
import logging
import json

from .custom_socket.client_socket import ClientSocket
from .utils import ACK_SCHEME

class InterfaceCommunicator:
    def __init__(self):
        self.host = os.environ["INTERFACE_IP"]
        self.port = int(os.environ["INTERFACE_PORT"])

    def send_finish_message(self):
        try:
            logging.info("[INTERFACE COMMUNICATOR] Trying to connect with interface")
            self.sock = ClientSocket(address = (self.host, self.port))
            self.sock.send_with_size(json.dumps({}))

            response = ACK_SCHEME.unpack(self.sock.recv_with_size(decode=False))[0]
            logging.info("[INTERFACE COMMUNICATOR] Received ack")
        except Exception as e:
            logging.info(f"[INTERFACE COMMUNICATOR] Failed sending finish message: {e}")
        