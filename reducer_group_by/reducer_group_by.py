#!/usr/bin/env python3
import logging
import json
from common.utils import *

class ReducerGroupBy():
    def __init__(self, group_by_queue, group_by_field, grouped_players_queue, sentinel_amount,
    batch_to_send):
        self.group_by_queue = group_by_queue
        self.group_by_field = group_by_field
        self.grouped_players_queue = grouped_players_queue
        self.players_to_group = {}
        self.sentinel_amount = sentinel_amount
        self.batch_to_send = batch_to_send

    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.group_by_queue)
        create_queue(channel, self.grouped_players_queue)

        consume(channel, self.group_by_queue, self.__callback)

    def __callback(self, ch, method, properties, body):
        players = json.loads(body)
        if len(players) == 0:
            logging.info("[REDUCER_GROUP_BY] Received 1 sentinel")
            return self.__handle_end_group_by(ch)
        
        for player in players:
            group_by_element = player[self.group_by_field]
            self.players_to_group[group_by_element] = self.players_to_group.get(group_by_element, [])
            self.players_to_group[group_by_element].append(player)

    def __handle_end_group_by(self, ch):
        self.sentinel_amount -= 1
        if self.sentinel_amount != 0: return        
        logging.info("[REDUCER_GROUP_BY] The client already sent all messages")

        result = {}
        for group_by_element in self.players_to_group:
            result[group_by_element] = self.players_to_group[group_by_element]
            if len(result) == self.batch_to_send:
                send_message(ch, json.dumps(result), queue_name=self.grouped_players_queue)
                result = {}
        
        if len(result) != 0: send_message(ch, json.dumps(result), queue_name=self.grouped_players_queue)
        send_message(ch, json.dumps({}), queue_name=self.grouped_players_queue)