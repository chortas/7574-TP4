#!/usr/bin/env python3
import logging
import json
import re
from datetime import datetime, timedelta
from common.utils import *

class FilterAvgRatingServerDuration():
    def __init__(self, match_queue, output_queue, avg_rating_field, server_field, 
    duration_field, id_field, interface_communicator, heartbeat_sender):
        self.match_queue = match_queue
        self.output_queue = output_queue
        self.avg_rating_field = avg_rating_field
        self.server_field = server_field
        self.duration_field = duration_field
        self.id_field = id_field
        self.interface_communicator = interface_communicator
        self.heartbeat_sender = heartbeat_sender

    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.match_queue)
        create_queue(channel, self.output_queue)

        self.heartbeat_sender.start()
        consume(channel, self.match_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        matches = json.loads(body)
        if len(matches) == 0:
            logging.info("[FILTER_AVG_RATING_SERVER_DURATION] The client already sent all messages")
            self.interface_communicator.send_finish_message()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        for match in matches:
            if self.__meets_the_condition(match):
                send_message(ch, match[self.id_field], queue_name=self.output_queue)
        ch.basic_ack(delivery_tag=method.delivery_tag)
           
    def __meets_the_condition(self, match):
        if len(match) == 0:
            logging.info("[FILTER_AVG_RATING_SERVER_DURATION] The client already sent all messages")
            self.interface_communicator.send_finish_message()
            return False
        average_rating = int(match[self.avg_rating_field]) if match[self.avg_rating_field] else 0
        server = match[self.server_field]
        duration = self.__parse_timedelta(match[self.duration_field])
        return average_rating > 2000 and server in ("koreacentral", "southeastasia", "eastus") and duration > timedelta(hours=2)

    def __parse_timedelta(self, stamp):
        m = None
        if 'day' in stamp:
            m = re.match(r'(?P<d>[-\d]+) day[s]*, (?P<h>\d+):'
                         r'(?P<m>\d+):(?P<s>\d[\.\d+]*)', stamp)
        else:
            m = re.match(r'(?P<h>\d+):(?P<m>\d+):'
                         r'(?P<s>\d[\.\d+]*)', stamp)
        time_dict = {key: float(val) for key, val in m.groupdict().items()}
        if 'd' in time_dict:
            return timedelta(days=time_dict['d'], hours=time_dict['h'],
                             minutes=time_dict['m'], seconds=time_dict['s'])
        return timedelta(hours=time_dict['h'], minutes=time_dict['m'], seconds=time_dict['s'])
