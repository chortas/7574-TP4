#!/usr/bin/env python3
import logging
import csv
import json
from threading import Thread
from common.utils import *
from common.custom_socket.client_socket import ClientSocket

class Client:
    def __init__(self, match_queue, match_file, player_queue, player_file, 
    batch_to_send, n_lines, api_address, exchange_names):
        self.match_queue = match_queue
        self.match_file = match_file
        self.player_queue = player_queue
        self.player_file = player_file
        self.batch_to_send = batch_to_send
        self.match_sender = Thread(target=self.__send_matches)
        self.player_sender = Thread(target=self.__send_players)
        self.n_lines = n_lines
        self.api_address = api_address
        self.exchange_names = exchange_names

    def start(self):
        self.act_request = self.__send_request() 
        if self.act_request != -1:
            logging.info("[CLIENT] Request accepted")            
            self.match_sender.start()
            self.player_sender.start()
        else:
            logging.info("[CLIENT] Request declined")

    def __send_request(self):
        self.interface_sock = ClientSocket(address = self.api_address)
        try:
            self.interface_sock.send_with_size(json.dumps({"n_lines": self.n_lines})) # send request
            act_request = self.interface_sock.recv_with_size()["act_request"]
            logging.info(f"[CLIENT] Receiving act_request: {act_request}")
        except Exception as e:
            logging.info("[CLIENT] Request errored")
            act_request = -1
        return act_request

    def __send_sentinel(self):
        try:
            logging.info("[CLIENT] Sending sentinel")
            self.interface_sock.send_with_size(json.dumps({})) # send sentinel
        except Exception as e:
            logging.info(f"[CLIENT] Sentinel request errored: {e}")

    def __send_players(self):
        self.__read_and_send(self.player_file, self.player_queue, self.act_request)

    def __send_matches(self):
        self.__read_and_send(self.match_file, self.match_queue, self.act_request)

    def __read_and_send(self, file_name, queue, act_request):
        connection, channel = create_connection_and_channel()

        create_queue(channel, queue)
        self.__create_queues(channel)

        with open(file_name, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)    
            counter_batch = 0
            counter_lines = 0
            lines = []
            for element in csv_reader:
                element["act_request"] = act_request
                counter_lines += 1
                lines.append(element)
                counter_batch += 1
                if counter_lines == self.n_lines:
                    break
                if counter_batch == self.batch_to_send:
                    logging.info(f"[{file_name}] Read {self.batch_to_send} lines and global counter is {counter_lines}")
                    send_message(channel, json.dumps(lines), queue_name=queue)
                    lines = []
                    counter_batch = 0
                
        if len(lines) != 0: send_message(channel, json.dumps(lines), queue_name=queue)                    
        
        # send the sentinel to the broadcasters
        send_message(channel, json.dumps({}), queue_name=queue)     

        # send the sentinel to the interface
        self.__send_sentinel()

        connection.close()

    def __create_queues(self, channel):
        routing_key = f"request_{self.act_request}"

        for i, exchange_name in enumerate(self.exchange_names):
            create_exchange(channel, exchange_name, "direct")
            create_and_bind_queue(channel, exchange_name, 
            routing_keys=[routing_key], queue_name=f"result_query_{i+1}_client_{self.act_request}")
