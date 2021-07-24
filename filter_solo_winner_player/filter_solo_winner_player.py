#!/usr/bin/env python3
import logging
import json
from common.utils import *
from common.state_handler import StateHandler

class FilterSoloWinnerPlayer():
    def __init__(self, grouped_players_queue, output_queue, rating_field, winner_field, 
    interface_communicator, heartbeat_sender, id, sentinel_amount):
        self.grouped_players_queue = grouped_players_queue
        self.output_queue = output_queue
        self.rating_field = rating_field
        self.winner_field = winner_field
        self.interface_communicator = interface_communicator
        self.heartbeat_sender = heartbeat_sender
        self.sentinel_amount = sentinel_amount
        self.__init_state(id)
    
    def __init_state(self, id):
        self.state_handler = StateHandler(id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[FILTER_SOLO_WINNER_PLAYER] Found state {}".format(state))
            self.act_sentinel = state["act_sentinel"]
            self.matches_with_condition = state["matches"]
        else:
            self.act_sentinel = self.sentinel_amount
            self.matches_with_condition = []
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"act_sentinel": self.act_sentinel, "matches": self.matches_with_condition})

    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.grouped_players_queue)
        create_queue(channel, self.output_queue)

        consume(channel, self.grouped_players_queue, self.__callback, auto_ack=False)

    def __callback(self, ch, method, properties, body):
        matches = json.loads(body)

        if len(matches) == 0:
            self.act_sentinel -= 1
            if self.act_sentinel == 0:
                self.act_sentinel = self.sentinel_amount
                self.matches_with_condition = []
                logging.info(f"[FILTER_SOLO_WINNER_PLAYER] End of file")
                self.interface_communicator.send_finish_message()
            self.__save_state()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        for match, players in matches.items():              
            if self.__meets_the_condition(players) and match not in self.matches_with_condition:
                send_message(ch, match, queue_name=self.output_queue)
                self.matches_with_condition.append(match)
        self.__save_state()
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    def __meets_the_condition(self, players):
        if len(players) != 2: return False
        rating_winner, rating_loser = (0,0)
        for player in players:
            if not player[self.rating_field]: return False
            is_winner = player[self.winner_field].lower() == "true"
            if is_winner:
                rating_winner = int(player[self.rating_field])
            else:
                rating_loser = int(player[self.rating_field])
        
        return rating_loser != 0 and rating_winner > 1000 and ((rating_loser - rating_winner) / rating_winner) * 100 > 30
