#!/usr/bin/env python3
import logging
import json
from common.utils import *

class WinnerRateCalculator():
    def __init__(self, grouped_players_queue, output_queue, winner_field):
        self.grouped_players_queue = grouped_players_queue
        self.output_queue = output_queue
        self.winner_field = winner_field
    
    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.grouped_players_queue)
        create_queue(channel, self.output_queue)

        consume(channel, self.grouped_players_queue, self.__callback)

    def __callback(self, ch, method, properties, body):
        logging.info("To send winner rate result")
        players_by_civ = json.loads(body)

        for civ in players_by_civ:
            victories = 0
            players = players_by_civ[civ]
            for player in players:
                if player[self.winner_field] == "True":
                    victories += 1
            winner_rate = (victories / len(players)) * 100
            result = {civ: winner_rate}
            send_message(ch, json.dumps(result), queue_name=self.output_queue)