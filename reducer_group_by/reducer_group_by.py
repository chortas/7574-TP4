#!/usr/bin/env python3
import logging
import json
from common.utils import *
from common.state_handler import StateHandler

class ReducerGroupBy():
    def __init__(self, id, group_by_queue, group_by_field, grouped_players_queue, 
    sentinel_amount, batch_to_send, heartbeat_sender):
        logging.info("[REDUCER_GROUP_BY] Init")
        self.group_by_queue = group_by_queue
        self.group_by_field = group_by_field
        self.grouped_players_queue = grouped_players_queue
        self.sentinel_amount = sentinel_amount
        self.batch_to_send = batch_to_send
        self.heartbeat_sender = heartbeat_sender
        self.id = id
        self.__init_state()

    def __init_state(self):
        self.state_handler = StateHandler(self.id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[REDUCER_GROUP_BY] Found state")
            self.act_sentinel = state["act_sentinel"]
            self.players_to_group = state["players_to_group"]
            self.act_request = state["act_request"]
            self.sentinels = state["sentinels"]
            self.finished = state["finished"]
        else:
            logging.info("[REDUCER_GROUP_BY] State not found")
            self.players_to_group = {}
            self.act_sentinel = self.sentinel_amount
            self.act_request = 0
            self.sentinels = []
            self.finished = 0
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"act_sentinel": self.act_sentinel, 
        "players_to_group": self.players_to_group, "act_request": self.act_request,
        "sentinels": self.sentinels, "finished": self.finished})

    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.group_by_queue)
        create_queue(channel, self.grouped_players_queue)

        consume(channel, self.group_by_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        players = json.loads(body)
        if "sentinel" in players:
            self.__handle_end_group_by(ch, players["sentinel"])
            self.__save_state()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        self.finished = 0
        self.__check_request(players[0])
        for player in players:
            group_by_element = player[self.group_by_field]
            self.players_to_group[group_by_element] = self.players_to_group.get(group_by_element, [])
            self.players_to_group[group_by_element].append(player)
        self.__save_state()
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def __check_request(self, player):
        if player["act_request"] != self.act_request and len(self.players_to_group) != 0:
            logging.info("[REDUCER_GROUP_BY] Client failed previously")
            self.players_to_group = {}
            self.act_sentinel = self.sentinel_amount
        self.act_request = player["act_request"]

    def __handle_end_group_by(self, ch, sentinel):
        logging.info(f"[REDUCER GROUP BY] I've seen a sentinel: {sentinel}")
        if sentinel in self.sentinels or self.finished: return
        self.sentinels.append(sentinel)
        self.act_sentinel -= 1
        if self.act_sentinel != 0: return        
        logging.info("[REDUCER_GROUP_BY] The client already sent all messages")

        result = {}
        for group_by_element in self.players_to_group:
            result[group_by_element] = self.players_to_group[group_by_element]
            if len(result) == self.batch_to_send:
                send_message(ch, json.dumps(result), queue_name=self.grouped_players_queue)
                result = {}
        
        if len(result) != 0: send_message(ch, json.dumps(result), queue_name=self.grouped_players_queue)
        send_message(ch, json.dumps({"sentinel": self.id}), queue_name=self.grouped_players_queue)
        self.players_to_group = {}
        self.act_sentinel = self.sentinel_amount
        self.sentinels = []
        self.finished = 1