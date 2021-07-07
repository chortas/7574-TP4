#!/usr/bin/env python3
import logging
import json
from common.utils import *

class ReducerJoin():
    def __init__(self, join_exchange, match_consumer_routing_key, player_consumer_routing_key,
    grouped_result_queue, match_id_field, player_match_field, batch_to_send):
        self.join_exchange = join_exchange
        self.match_consumer_routing_key = match_consumer_routing_key
        self.player_consumer_routing_key = player_consumer_routing_key
        self.grouped_result_queue = grouped_result_queue
        self.match_id_field = match_id_field
        self.player_match_field = player_match_field
        self.batch_to_send = batch_to_send
        self.matches_and_players = {}
        self.matches = set()
        self.players = set()
        self.len_join = 2 # to know when to stop

    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_exchange(channel, self.join_exchange, exchange_type="direct")
        queue_name = create_and_bind_anonymous_queue(channel, self.join_exchange, 
        routing_keys=[self.match_consumer_routing_key, self.player_consumer_routing_key])

        create_queue(channel, self.grouped_result_queue)

        consume(channel, queue_name, self.__callback)

    def __callback(self, ch, method, properties, body):
        elements = json.loads(body) 
        if len(elements) == 0:
            return self.__handle_end_join(ch)
        for element in elements:
            self.__store_matches_and_players(element, method)
    
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
