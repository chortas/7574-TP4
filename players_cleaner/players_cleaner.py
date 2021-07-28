#!/usr/bin/env python3
import logging
import json
from datetime import datetime, timedelta
from common.utils import *
from hashlib import new, sha256

class PlayersCleaner():
    def __init__(self, player_queue, match_field, civ_field, winner_field, 
    join_exchange, join_routing_key, heartbeat_sender, id):
        self.player_queue = player_queue
        self.match_field = match_field
        self.civ_field = civ_field
        self.winner_field = winner_field 
        self.join_exchange = join_exchange
        self.join_routing_key = join_routing_key
        self.heartbeat_sender = heartbeat_sender
        self.id = id

    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.player_queue)
        create_exchange(channel, self.join_exchange, "direct")

        consume(channel, self.player_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        players = json.loads(body)
        if "sentinel" in players:
            self.__handle_end_cleaner(ch)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        new_players = self.__get_new_players(players)
        send_message(ch, json.dumps(new_players), queue_name=self.join_routing_key, exchange_name=self.join_exchange)
        logging.info("[PLAYERS_CLEANER] Sent new players")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __handle_end_cleaner(self, ch):
        logging.info("[PLAYERS_CLEANER] The client already sent all messages")
        new_sentinel = json.dumps({"sentinel": self.id})
        send_message(ch, new_sentinel, queue_name=self.join_routing_key, exchange_name=self.join_exchange)
    
    def __get_new_players(self, players):
        new_players = []
        for player in players:
            new_players.append({self.match_field: player[self.match_field],
                    self.civ_field: player[self.civ_field],
                    self.winner_field: player[self.winner_field],
                    "act_request": player["act_request"]})
        
        return new_players