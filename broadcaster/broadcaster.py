#!/usr/bin/env python3
import logging
import json
from common.utils import *

class Broadcaster():
    def __init__(self, row_queue, queues_to_send, heartbeat_sender, id):
        self.row_queue = row_queue
        self.queues_to_send = queues_to_send
        self.heartbeat_sender = heartbeat_sender
        self.id = id

    def start(self):
        self.heartbeat_sender.start()
        
        connection, channel = create_connection_and_channel()

        create_queue(channel, self.row_queue)
        for queue in self.queues_to_send:
            create_queue(channel, queue)

        consume(channel, self.row_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        logging.info(f"Received {len(json.loads(body))} from client")

        for queue in self.queues_to_send:
            if len(json.loads(body)) == 0:
                send_message(ch, json.dumps({"sentinel": self.id}), queue_name=queue)
            else:
                send_message(ch, body, queue_name=queue)
        ch.basic_ack(delivery_tag=method.delivery_tag)
