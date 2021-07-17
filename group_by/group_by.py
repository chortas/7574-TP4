#!/usr/bin/env python3
import logging
import json
from datetime import datetime, timedelta
from common.utils import *
from hashlib import sha256

class GroupBy():
    def __init__(self, n_reducers, group_by_queue, group_by_field, queue_name,
    heartbeat_sender):
        self.reducer_queues = [f"{group_by_queue}_{i}" for i in range(1, n_reducers+1)]
        self.n_reducers = n_reducers
        self.group_by_field = group_by_field
        self.queue_name = queue_name
        self.heartbeat_sender = heartbeat_sender
    
    def start(self):
        self.heartbeat_sender.start()
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.queue_name)

        for reducer_queue in self.reducer_queues:
            create_queue(channel, reducer_queue)

        consume(channel, self.queue_name, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        players = json.loads(body)

        if len(players) == 0:
            for reducer_queue in self.reducer_queues:
                send_message(ch, body, queue_name=reducer_queue)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # { group_id_field: {players that have that id} }
        message = self.__get_message(players)

        for reducer_id, elements in message.items():
            send_message(ch, json.dumps(elements), queue_name=self.reducer_queues[reducer_id])
        ch.basic_ack(delivery_tag=method.delivery_tag)
        

    def __get_message(self, players):
        message = {}
        for player in players:
            group_by_element = player[self.group_by_field]
            hashed_element = int(sha256(group_by_element.encode()).hexdigest(), 16)
            reducer_id = hashed_element % self.n_reducers
            message[reducer_id] = message.get(reducer_id, [])
            message[reducer_id].append(player)
        return message
        