#!/usr/bin/env python3
import logging
import json
from common.utils import *

class FilterRating():
    def __init__(self, player_queue, rating_field, match_field, civ_field, id_field,
    join_exchange, join_routing_key, heartbeat_sender):
        self.player_queue = player_queue
        self.rating_field = rating_field
        self.match_field = match_field
        self.civ_field = civ_field
        self.id_field = id_field
        self.join_exchange = join_exchange
        self.join_routing_key = join_routing_key
        self.heartbeat_sender = heartbeat_sender

    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.player_queue)
        create_exchange(channel, self.join_exchange, "direct")

        consume(channel, self.player_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        players = json.loads(body)
        if len(players) == 0:
            logging.info("[FILTER_RATING] The client already sent all messages")
            send_message(ch, body, queue_name=self.join_routing_key, exchange_name=self.join_exchange)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        message = self.__get_message(players)
        send_message(ch, json.dumps(message), queue_name=self.join_routing_key, exchange_name=self.join_exchange)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __get_message(self, players):
        message = []
        for player in players:
            rating = int(player[self.rating_field]) if player[self.rating_field] else 0
            if rating > 2000:
                new_player = {self.match_field: player[self.match_field],
                        self.civ_field: player[self.civ_field],
                        self.id_field: player[self.id_field]}
                message.append(new_player)
        return message