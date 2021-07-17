#!/usr/bin/env python3
import logging
import json
from datetime import datetime, timedelta
from common.utils import *
from hashlib import sha256

class PlayersCleaner():
    def __init__(self, player_queue, match_field, civ_field, winner_field, 
    join_exchange, join_routing_key, heartbeat_sender):
        self.player_queue = player_queue
        self.match_field = match_field
        self.civ_field = civ_field
        self.winner_field = winner_field 
        self.join_exchange = join_exchange
        self.join_routing_key = join_routing_key
        self.heartbeat_sender = heartbeat_sender

    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.player_queue)
        create_exchange(channel, self.join_exchange, "direct")

        self.heartbeat_sender.start()
        consume(channel, self.player_queue, self.__callback)

    def __callback(self, ch, method, properties, body):
        players = json.loads(body)
        if len(players) == 0:
            self.__handle_end_cleaner(ch, body)

        new_players = self.__get_new_players(players)
        send_message(ch, json.dumps(new_players), queue_name=self.join_routing_key, exchange_name=self.join_exchange)

    def __handle_end_cleaner(self, ch, body):
        logging.info("[PLAYERS_CLEANER] The client already sent all messages")
        send_message(ch, body, queue_name=self.join_routing_key, exchange_name=self.join_exchange)
        return
    
    def __get_new_players(self, players):
        new_players = []
        for player in players:
            new_players.append({self.match_field: player[self.match_field],
                    self.civ_field: player[self.civ_field],
                    self.winner_field: player[self.winner_field]})
        
        return new_players