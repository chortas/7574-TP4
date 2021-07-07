#!/usr/bin/env python3
import logging
import csv
import json
from threading import Thread
from common.utils import *

class Client:
    def __init__(self, match_queue, match_file, player_queue, player_file, batch_to_send):
        self.match_queue = match_queue
        self.match_file = match_file
        self.player_queue = player_queue
        self.player_file = player_file
        self.batch_to_send = batch_to_send
        self.match_sender = Thread(target=self.__send_matches)
        self.player_sender = Thread(target=self.__send_players)

    def start(self):
        wait_for_rabbit()
        
        self.match_sender.start()
        self.player_sender.start()
    
    def __send_players(self):
        self.__read_and_send(self.player_file, self.player_queue, "match_players_reducido.csv",
        ["token","match","rating","color","civ","team","winner"])

    def __send_matches(self):
        self.__read_and_send(self.match_file, self.match_queue, "matches_reducido.csv", 
        ["token","winning_team","mirror","ladder","patch","average_rating","map","map_size","num_players","server","duration"])

    def __read_and_send(self, file_name, queue, other_file_name, fieldnames):
        connection, channel = create_connection_and_channel()

        create_queue(channel, queue)

        with open(other_file_name, mode='w') as csv_file_writer:
            writer = csv.DictWriter(csv_file_writer, fieldnames=fieldnames)
            writer.writeheader()

            with open(file_name, mode='r') as csv_file:
                csv_reader = csv.DictReader(csv_file)    
                counter_lines = 0
                global_counter = 0
                lines = []
                for element in csv_reader:
                    global_counter += 1
                    lines.append(element)
                    counter_lines += 1
                    if counter_lines == self.batch_to_send:
                        logging.info(f"[{file_name}] Read {self.batch_to_send} lines and global counter is {global_counter}")
                        send_message(channel, json.dumps(lines), queue_name=queue)
                        lines = []
                        counter_lines = 0
                
        if len(lines) != 0: send_message(channel, json.dumps(lines), queue_name=queue)                    
        
        #send the sentinel
        send_message(channel, json.dumps({}), queue_name=queue)     

        connection.close()