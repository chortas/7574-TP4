import os
import logging
import json

from common.custom_socket.client_socket import ClientSocket
from common.custom_socket.server_socket import ServerSocket
from common.shared_value import SharedValue
from common.utils import ACK_SCHEME
from threading import Thread
from time import sleep
from common.state_handler_safe import StateHandlerSafe

class HeartbeatSender(Thread):
    def __init__(self, node_id = None, change_is_leader_callback=None):
        Thread.__init__(self)
        self.hosts = os.environ["MONITOR_IPS"].split(',')
        logging.info(f"Hosts: {self.hosts}")
        self.monitor_port = int(os.environ["MONITOR_PORT"])        
        self.id = node_id if node_id else os.environ["ID"]
        self.pos = self.hosts.index(node_id)
        logging.info(f"Pos is {self.pos}")
        self.election_port = int(os.environ["ELECTION_PORT"]) 
        self.leader_info_port = int(os.environ["LEADER_INFO_PORT"])
        self.election_started = SharedValue(False)
        self.__init_state(self.id, change_is_leader_callback)
        

        self.election_listening = Thread(target=self.__start_listening_elections)
        self.leader_listening = Thread(target=self.__start_listening_leaders)

    
    def __start_listening_elections(self):
        logging.info(f"[HEARTBEAT_SENDER] Listening to election msg in {self.election_port}")
        election_socket = ServerSocket('', self.election_port, 1)
        while True:
            component_sock = election_socket.accept()
            if not component_sock:
                continue
            logging.info("[HEART_BEAT] Component connection accepted")
            info = election_socket.recv_from(component_sock)

            if "id" in info: #election
                logging.info(f"[HEARTBEAT_SENDER] Received election msg from {info['id']}.")
                if self.pos > info["id"]:
                    logging.info(f"[HEARTBEAT_SENDER] Is smaller than me I send ACK.")
                    election_socket.send_to(component_sock, ACK_SCHEME.pack(True), encode=False)
                    component_sock.close()
                else:
                    component_sock.close()
                logging.info(f"[HEARTBEAT_SENDER] Recv election msg -> Starting election.")
                self.__start_election()
            self.__save_state()

    def __start_listening_leaders(self):
        logging.info(f"[HEARTBEAT_SENDER] Listening to leaders in {self.leader_info_port}")
        logging.info("[HEARTBEAT_SENDER] Hearing leader info")
        leader_socket = ServerSocket('', self.leader_info_port, 1)
        monitor_component_sock = leader_socket.accept()
        while True:
            if not monitor_component_sock:
                monitor_component_sock = leader_socket.accept()
                continue
            logging.info(f"[LISTENING_LEADER] Accept leader connection!!!")
            try:
                info = leader_socket.recv_from(monitor_component_sock)
                logging.info(f"[LISTENING_LEADER] Recieve {info} and election is {self.election_started.read()}")
                if info["leader"] and self.leader.read() != info["leader"]:
                    logging.info(f"[HEARTBEAT_SENDER] New leader is monitor_{info['leader']+1}")
                    self.leader.update(info["leader"])
                    self.__save_state()
                    self.election_started.update(False)
                    monitor_component_sock.close()
                    continue
                else:
                    continue
            except Exception as err:
                logging.info(f"[LISTENING_LEADER] Error recieving {err}!!!")
                continue
            finally:
                monitor_component_sock=None
            
    def __start_election(self):
        logging.info(f"[HEARTBEAT_SENDER] Election? {self.election_started.read()}")
        if not self.election_started.read():
            logging.info("[HEARTBEAT_SENDER] Election started")
            self.election_started.update(True)
            responses = 0
            for i in range(self.pos+1, len(self.hosts)):
                if not self.election_started.read():
                    logging.info("[HEARTBEAT_SENDER] Leader elected!")
                    return
                host = self.hosts[i]
                try:
                    logging.info(f"[HEARTBEAT_SENDER] Sending election msg to {host}")
                    self.sock = ClientSocket(address = (host, self.election_port))
                    self.sock.send_with_size(json.dumps({"id": self.pos}))

                    response = ACK_SCHEME.unpack(self.sock.recv_with_size(decode=False))[0]
                    logging.info("[HEARTBEAT_SENDER] RECV ELECTION ACK")
                    
                    if response:
                        responses +=1
                        logging.info(f"[HEARTBEAT_SENDER] Im not leader")
                        break
                
                except Exception as err:
                    logging.info(f"[HEARTBEAT_SENDER] Error sending election msg. {err}")
                    continue

            if responses == 0:
                logging.info(f"[HEARTBEAT_SENDER] Im leader")
                for i in range(len(self.hosts)):
                    if i == self.pos: continue
                    host = self.hosts[i]
                    try:
                        logging.info(f"[HEARTBEAT_SENDER] Trying to send leader msg to {host}")
                        self.sock = ClientSocket(address = (host, self.leader_info_port))
                        self.sock.send_with_size(json.dumps({"leader": self.pos}))
                        logging.info(f"[HEARTBEAT_SENDER] Sended leader msg to {host}")
                    except Exception as err:
                        logging.info(f"[HEARTBEAT_SENDER] Error sending that im leader to {host}: {err}")
                        continue
                    finally:
                        if self.sock: self.sock.close()
                logging.info(f"[HEARTBEAT_SENDER] Finish sending leader msg")
                self.leader.update(self.pos)
                self.is_leader = True
                self.__save_state()
                self.election_started.update(False)

    def __init_state(self, id, change_is_leader_callback):
        self.state_handler = StateHandlerSafe(id, filename = "heartbeat_info.json")
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info(f"[HEARTBEAT_SENDER] Found state: {state}")
            self.leader = SharedValue(state["leader"])
        else:
            logging.info("[HEARTBEAT_SENDER] State not found")
            self.leader = SharedValue(int(os.environ["LEADER"]))
        self.is_leader = f"monitor_{self.leader.read()+1}" == self.id
        self.change_is_leader_callback=change_is_leader_callback
        self.__save_state()

    def __save_state(self):
        self.election_started.update(False)
        self.is_leader = f"monitor_{self.leader.read()+1}" == self.id
        self.change_is_leader_callback(self.is_leader)
        self.state_handler.update_state({"leader": self.leader.read()})

    def __init_port(self):
        while True:
            leader = self.leader.read()
            if leader == self.pos: continue
            act_host = self.hosts[leader]

            logging.info(f"[HEARTBEAT_SENDER] Trying to connect with node ({act_host}, {self.monitor_port})")

            try:
                self.sock = ClientSocket(address = (act_host, self.monitor_port))
                self.sock.send_with_size(json.dumps({"id": self.id}))

                response = self.sock.recv_with_size()
                logging.info(f"[HEARTBEAT_SENDER] Recv port: {response}")
                self.port = int(response["port"])

                self.sock.close()

                logging.info(f"[HEARTBEAT_SENDER] Port received: {self.port}")
                break
            
            except Exception as err:
                logging.info(f"[HEARTBEAT_SENDER] Problem initiating port: {err}. Start election")
                self.__start_election()
                continue


    def __send_heartbeats(self):
        self.election_started.update(False)
        while True:
            act_host = self.hosts[self.leader.read()]

            try:
                if self.is_leader: continue
                logging.info(f"[HEARTBEAT_SENDER] Act host: {act_host}")
                heartbeat_listener_socket = ClientSocket(address = (act_host, self.port))

                while not self.is_leader:
                    #logging.info(f"[HEARTBEAT_SENDER] Sending heartbeat from {self.id} to ({act_host},{self.port})")
                    heartbeat_listener_socket.send_with_size(json.dumps({"id": self.id}))
                    #logging.info(f"[HEARTBEAT_SENDER] About to sleep: {self.id}")
                    #sleep(self.frequency)

            except Exception as err:
                logging.info(f"[HEARTBEAT_SENDER] Failed sending heartbeat: {err}. Start election")
                self.__init_port()
                self.__send_heartbeats() # retry

    def run(self):
        self.election_listening.start()
        self.leader_listening.start()
        logging.info(f"[HEARTBEAT_SENDER] Init. Start election")
        sleep(5)# wating other monitors
        self.__start_election()
        logging.info(f"[HEARTBEAT_SENDER] Finish election {self.leader.read()}")
        self.__init_port()
        self.__send_heartbeats()
