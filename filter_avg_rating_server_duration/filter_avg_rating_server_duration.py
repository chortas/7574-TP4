#!/usr/bin/env python3
import logging
import json
import re
from datetime import datetime, timedelta
from common.utils import *

class FilterAvgRatingServerDuration():
    def __init__(self, match_queue, output_queue, avg_rating_field, server_field, 
    duration_field, id_field):
        self.match_queue = match_queue
        self.output_queue = output_queue
        self.avg_rating_field = avg_rating_field
        self.server_field = server_field
        self.duration_field = duration_field
        self.id_field = id_field

    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.match_queue)
        create_queue(channel, self.output_queue)

        consume(channel, self.match_queue, self.__callback)

    def __callback(self, ch, method, properties, body):
        matches = json.loads(body)
        for match in matches:
            if self.__meets_the_condition(match):
                send_message(ch, match[self.id_field], queue_name=self.output_queue)
           
    def __meets_the_condition(self, match):
        if len(match) == 0:
            logging.info("[FILTER_AVG_RATING_SERVER_DURATION] The client already sent all messages")
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
