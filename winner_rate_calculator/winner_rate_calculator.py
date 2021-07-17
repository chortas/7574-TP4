#!/usr/bin/env python3
import logging
import json
from common.utils import *

class WinnerRateCalculator():
    def __init__(self, grouped_players_queue, output_queue, winner_field, 
    sentinel_amount, interface_communicator, heartbeat_sender):
        self.grouped_players_queue = grouped_players_queue
        self.output_queue = output_queue
        self.winner_field = winner_field
        self.interface_communicator = interface_communicator
        self.sentinel_amount = sentinel_amount
        self.act_sentinel = sentinel_amount
        self.heartbeat_sender = heartbeat_sender
    
    def start(self):
        wait_for_rabbit()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.grouped_players_queue)
        create_queue(channel, self.output_queue)

        self.heartbeat_sender.start()
        consume(channel, self.grouped_players_queue, self.__callback)

    def __callback(self, ch, method, properties, body):
        logging.info("To send winner rate result")
        players_by_civ = json.loads(body)

        if len(players_by_civ) == 0:
            self.act_sentinel -= 1
            if self.act_sentinel == 0:
                self.act_sentinel = self.sentinel_amount
                logging.info("[WINNER_RATE_CALCULATOR] End of file")
                self.interface_communicator.send_finish_message()
                return

        for civ in players_by_civ:
            victories = 0
            players = players_by_civ[civ]
            for player in players:
                if player[self.winner_field] == "True":
                    victories += 1
            winner_rate = (victories / len(players)) * 100
            result = {civ: winner_rate}
            send_message(ch, json.dumps(result), queue_name=self.output_queue)