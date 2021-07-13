#!/usr/bin/env python3
import logging
import json
from datetime import datetime, timedelta
from common.utils import *

class FilterSoloWinnerPlayer():
    def __init__(self, grouped_players_queue, output_queue, rating_field, winner_field, interface_communicator):
        self.grouped_players_queue = grouped_players_queue
        self.output_queue = output_queue
        self.rating_field = rating_field
        self.winner_field = winner_field
        self.interface_communicator = interface_communicator

    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.grouped_players_queue)
        create_queue(channel, self.output_queue)

        consume(channel, self.grouped_players_queue, self.__callback)

    def __callback(self, ch, method, properties, body):
        matches = json.loads(body)
        if len(matches) == 0:
            logging.info(f"[FILTER_SOLO_WINNER_PLAYER] End of file")
            self.interface_communicator.send_finish_message()
            return
        
        for match, players in matches.items():
            if self.__meets_the_condition(match, players):
                logging.info(f"[FILTER_SOLO_WINNER_PLAYER] Player matches condition!")
                send_message(ch, match, queue_name=self.output_queue)
        
    def __meets_the_condition(self, match, players):
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
