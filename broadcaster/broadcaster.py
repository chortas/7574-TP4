#!/usr/bin/env python3
import logging
import json
from common.utils import *

class Broadcaster():
    def __init__(self, row_queue, queues_to_send):
        self.row_queue = row_queue
        self.queues_to_send = queues_to_send

    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.row_queue)
        for queue in self.queues_to_send:
            create_queue(channel, queue)

        consume(channel, self.row_queue, self.__callback)

    def __callback(self, ch, method, properties, body):
        logging.info(f"Received {len(json.loads(body))} from client")

        for queue in self.queues_to_send:
            send_message(ch, body, queue_name=queue)
