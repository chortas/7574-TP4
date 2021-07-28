#!/usr/bin/env python3
import logging
import json
from common.utils import *

class FilterLadderMapMirror():
    def __init__(self, match_queue, match_token_exchange, top_civ_routing_key, 
    rate_winner_routing_key, ladder_field, map_field, mirror_field, id_field,
    heartbeat_sender, id):
        self.match_queue = match_queue
        self.match_token_exchange = match_token_exchange
        self.top_civ_routing_key = top_civ_routing_key
        self.rate_winner_routing_key = rate_winner_routing_key
        self.ladder_field = ladder_field
        self.map_field = map_field
        self.mirror_field = mirror_field
        self.id_field = id_field
        self.heartbeat_sender = heartbeat_sender
        self.id = id

    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.match_queue)
        create_exchange(channel, self.match_token_exchange, "direct")

        consume(channel, self.match_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        matches = json.loads(body)
        if "sentinel" in matches:
           return self.__handle_end_filter(ch, body, method)

        winner_rate_matches = []
        top_civ_matches = []

        for match in matches:
            # drop extra rows
            new_match = {self.id_field: match[self.id_field], "act_request": match["act_request"]}
            if self.__meets_winner_rate_condition(match):
                winner_rate_matches.append(new_match)
            elif self.__meets_top_civ_condition(match):
                top_civ_matches.append(new_match)

        if len(winner_rate_matches) != 0: send_message(ch, json.dumps(winner_rate_matches), queue_name=self.rate_winner_routing_key, exchange_name=self.match_token_exchange)
        if len(top_civ_matches) != 0: send_message(ch, json.dumps(top_civ_matches), queue_name=self.top_civ_routing_key, exchange_name=self.match_token_exchange)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __handle_end_filter(self, ch, body, method):
        logging.info(f"[FILTER_LADDER_MAP_MIRROR] The client already sent all messages")
        new_sentinel = json.dumps({"sentinel": self.id})
        send_message(ch, new_sentinel, queue_name=self.rate_winner_routing_key, exchange_name=self.match_token_exchange)
        send_message(ch, new_sentinel, queue_name=self.top_civ_routing_key, exchange_name=self.match_token_exchange)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __meets_winner_rate_condition(self, match):
        match_ladder = match[self.ladder_field]
        match_map = match[self.map_field]
        match_mirror = match[self.mirror_field]
        return match_ladder == "RM_1v1" and match_map == "arena" and match_mirror == "False"
    
    def __meets_top_civ_condition(self, match):
        match_ladder = match[self.ladder_field]
        match_map = match[self.map_field]
        return match_ladder == "RM_TEAM" and match_map == "islands"