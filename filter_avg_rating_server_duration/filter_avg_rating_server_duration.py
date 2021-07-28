#!/usr/bin/env python3
import logging
import json
import re
from datetime import timedelta
from common.utils import *
from common.state_handler import StateHandler

class FilterAvgRatingServerDuration():
    def __init__(self, match_queue, output_exchange, avg_rating_field, server_field, 
    duration_field, id_field, interface_communicator, heartbeat_sender, id, sentinel_amount):
        self.match_queue = match_queue
        self.output_exchange = output_exchange
        self.avg_rating_field = avg_rating_field
        self.server_field = server_field
        self.duration_field = duration_field
        self.id_field = id_field
        self.interface_communicator = interface_communicator
        self.heartbeat_sender = heartbeat_sender
        self.sentinel_amount = sentinel_amount
        self.__init_state(id)

    def __init_state(self, id):
        self.state_handler = StateHandler(id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[FILTER_AVG_RATING_SERVER_DURATION] Found state {}".format(state))
            self.matches_with_condition = state["matches"]
            self.sentinels = state["sentinels"]
            self.act_sentinel = state["act_sentinel"]
            self.finished = state["finished"]
        else:
            self.matches_with_condition = []
            self.sentinels = []
            self.act_sentinel = self.sentinel_amount
            self.finished = 0
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"act_sentinel": self.act_sentinel,
        "matches": self.matches_with_condition, "sentinels": self.sentinels, "finished": self.finished})

    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.match_queue)
        create_exchange(channel, self.output_exchange, "direct")

        consume(channel, self.match_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        matches = json.loads(body)
        if "sentinel" in matches:
            sentinel = matches["sentinel"]
            if sentinel not in self.sentinels and not self.finished:
                self.sentinels.append(sentinel)
                self.act_sentinel -= 1
                if self.act_sentinel == 0:
                    logging.info("[FILTER_AVG_RATING_SERVER_DURATION] The client already sent all messages")
                    self.interface_communicator.send_finish_message()
                    self.matches_with_condition = []
                    self.act_sentinel = self.sentinel_amount
                    self.sentinels = []
                    self.finished = 1
            self.__save_state()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        self.finished = 0
        for match in matches:
            if self.__meets_the_condition(match) and match not in self.matches_with_condition:
                send_message(ch, self.__parse_match(match), queue_name=f"request_{match['act_request']}", exchange_name=self.output_exchange)
                self.matches_with_condition.append(match)
        self.__save_state()
        ch.basic_ack(delivery_tag=method.delivery_tag)
           
    def __meets_the_condition(self, match):
        if "sentinel" in match:
            logging.info("[FILTER_AVG_RATING_SERVER_DURATION] The client already sent all messages")
            self.interface_communicator.send_finish_message()
            return False
        average_rating = int(match[self.avg_rating_field]) if match[self.avg_rating_field] else 0
        server = match[self.server_field]
        duration = self.__parse_timedelta(match[self.duration_field])
        return average_rating > 2000 and server in ("koreacentral", "southeastasia", "eastus") and duration > timedelta(hours=2)

    def __parse_match(self, match):
        return json.dumps({"act_request": match["act_request"], self.id_field: match[self.id_field]})

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
