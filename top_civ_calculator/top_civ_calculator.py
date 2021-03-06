#!/usr/bin/env python3
import logging
import json
from common.utils import *
from common.state_handler import StateHandler
from collections import Counter

class TopCivCalculator():
    def __init__(self, id, grouped_players_queue, output_exchange, id_field, sentinel_amount, 
    interface_communicator, heartbeat_sender):
        logging.info("[TOP_CIV_CALCULATOR] Init")
        self.grouped_players_queue = grouped_players_queue
        self.output_exchange = output_exchange
        self.id_field = id_field
        self.sentinel_amount = sentinel_amount
        self.act_sentinel = sentinel_amount
        self.interface_communicator = interface_communicator
        self.heartbeat_sender = heartbeat_sender
        self.id = id
        self.__init_state()
    
    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.grouped_players_queue)
        create_exchange(channel, self.output_exchange, "direct")
        
        consume(channel, self.grouped_players_queue, self.__callback, auto_ack=False)

    def __init_state(self):
        self.state_handler = StateHandler(self.id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[TOP_CIV_CALCULATOR] Found state {}".format(state))
            self.act_sentinel = state["act_sentinel"]
            self.civilizations = state["civilizations"]
            self.act_request = state["act_request"]
            self.sentinels = state["sentinels"]
            self.finished = state["finished"]
        else:
            self.civilizations = {}
            self.act_sentinel = self.sentinel_amount
            self.act_request = 0
            self.sentinels = []
            self.finished = 0
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"act_sentinel": self.act_sentinel, 
        "civilizations": self.civilizations, "act_request": self.act_request,
        "sentinels": self.sentinels, "finished": self.finished})

    def __callback(self, ch, method, properties, body):
        players_by_civ = json.loads(body)

        if "sentinel" in players_by_civ:
            if self.__send_top_5(ch, players_by_civ["sentinel"]):
                logging.info("[TOP_CIV_CALCULATOR] End of file")
                self.interface_communicator.send_finish_message()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        self.finished = 0
        for civ in players_by_civ:
            if civ in self.civilizations:
                continue
            token_by_civ = set()
            players = players_by_civ[civ]
            
            self.__check_request(players[0])

            for player in players:
                token = player[self.id_field]
                if token not in token_by_civ:
                    token_by_civ.add(token)
            self.civilizations[civ] = len(token_by_civ)
        self.__save_state()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __check_request(self, player):
        if player["act_request"] != self.act_request and len(self.civilizations) != 0:
            self.civilizations = {}
            self.act_sentinel = self.sentinel_amount
        self.act_request = player["act_request"]        

    def __send_top_5(self, channel, sentinel):
        if sentinel in self.sentinels or self.finished: return False
        self.sentinels.append(sentinel)
        self.act_sentinel -= 1
        if self.act_sentinel != 0:
            self.__save_state()
            return False
        logging.info(f"To send top 5 -> civilizations: {self.civilizations}")

        top_5_civilizations = dict(Counter(self.civilizations).most_common(5))
        top_5_civilizations["act_request"] = self.act_request

        send_message(channel, json.dumps(top_5_civilizations), queue_name=f"request_{self.act_request}", exchange_name=self.output_exchange)            
        
        self.civilizations = {}
        self.act_sentinel = self.sentinel_amount
        self.sentinels = []
        self.finished = 1
        self.__save_state()
        return True
