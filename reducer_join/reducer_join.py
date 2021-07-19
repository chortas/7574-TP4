#!/usr/bin/env python3
import logging
import json
from common.utils import *
from common.state_handler import StateHandler

LEN_JOIN = 2

class ReducerJoin():
    def __init__(self, id, join_exchange, match_consumer_routing_key, 
    player_consumer_routing_key, grouped_result_queue, match_id_field, 
    player_match_field, batch_to_send, heartbeat_sender):
        logging.info("[REDUCER_JOIN] Init")
        self.join_exchange = join_exchange
        self.match_consumer_routing_key = match_consumer_routing_key
        self.player_consumer_routing_key = player_consumer_routing_key
        self.grouped_result_queue = grouped_result_queue
        self.match_id_field = match_id_field
        self.player_match_field = player_match_field
        self.batch_to_send = batch_to_send
        self.heartbeat_sender = heartbeat_sender
        self.__init_state(id)

    def __init_state(self, id):
        logging.info("[REDUCER_JOIN] Init State")
        self.state_handler = StateHandler(id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[REDUCER_JOIN] Found state")
            self.len_join = state["len_join"]
            self.matches_and_players = state["matches_and_players"]
            self.matches = set(state["matches"])
            self.players = set(state["players"])
        else:
            logging.info("[REDUCER_JOIN] No state saved")
            self.matches_and_players = {}
            self.matches = set()
            self.players = set()
            self.len_join = LEN_JOIN # to know when to stop
            self.__save_state()
            

    def __save_state(self):
        self.state_handler.update_state({"len_join": self.len_join, "matches_and_players": self.matches_and_players,
        "matches": list(self.matches), "players": list(self.players)})

    def start(self):
        self.heartbeat_sender.start()
        wait_for_rabbit()
        connection, channel = create_connection_and_channel()
        create_exchange(channel, self.join_exchange, exchange_type="direct")
        queue_name = create_and_bind_queue(channel, self.join_exchange, 
            routing_keys=[self.match_consumer_routing_key, self.player_consumer_routing_key], queue_name=f"input_{self.join_exchange}")
        create_queue(channel, self.grouped_result_queue)
        consume(channel, queue_name, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        elements = json.loads(body) 
        if len(elements) == 0:
            self.__handle_end_join(ch)
            self.__save_state()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        for element in elements:
            self.__store_matches_and_players(element, method)
        self.__save_state()
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    def __handle_end_join(self, ch):
        self.len_join -= 1
        if self.len_join == 0:
            logging.info("[REDUCER_JOIN] The client already sent all messages")
            self.__send_to_grouped_queue(ch)

    def __store_matches_and_players(self, body_parsed, method):
        id_to_join = (body_parsed[self.match_id_field] 
                    if method.routing_key == self.match_consumer_routing_key
                    else body_parsed[self.player_match_field])

        self.matches_and_players[id_to_join] = self.matches_and_players.get(id_to_join, [])

        if method.routing_key == self.match_consumer_routing_key:
            self.matches.add(id_to_join)

        if method.routing_key == self.player_consumer_routing_key:       
            self.players.add(id_to_join)
            self.matches_and_players[id_to_join].append(body_parsed)

    def __send_to_grouped_queue(self, ch):
        result = []
        for token, players in self.matches_and_players.items():
            if token in self.matches and token in self.players:
                for player in players:
                    result.append(player)
                if len(result) == self.batch_to_send:
                    send_message(ch, json.dumps(result), queue_name=self.grouped_result_queue)
                    result = []

        logging.info("To send empty body to group by")
        if len(result) != 0: 
            send_message(ch, json.dumps(result), queue_name=self.grouped_result_queue)
        send_message(ch, json.dumps({}), queue_name=self.grouped_result_queue)
        self.matches_and_players = {}
        self.matches = set()
        self.players = set()
        self.len_join = LEN_JOIN
        