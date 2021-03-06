#!/usr/bin/env python3
import logging
import json
from common.utils import *
from common.state_handler import StateHandler

class WinnerRateCalculator():
    def __init__(self, id, grouped_players_queue, output_exchange, winner_field, 
    sentinel_amount, interface_communicator, heartbeat_sender):
        self.grouped_players_queue = grouped_players_queue
        self.output_exchange = output_exchange
        self.winner_field = winner_field
        self.interface_communicator = interface_communicator
        self.sentinel_amount = sentinel_amount
        self.heartbeat_sender = heartbeat_sender
        self.id = id
        self.__init_state()
    
    def start(self):
        self.heartbeat_sender.start()

        connection, channel = create_connection_and_channel()

        create_queue(channel, self.grouped_players_queue)
        create_exchange(channel, self.output_exchange, "direct")

        consume(channel, self.grouped_players_queue, self.__callback, auto_ack=False)

    def __init_state(self):
        self.state_handler = StateHandler(self.id)
        state = self.state_handler.get_state()
        if len(state) != 0:
            logging.info("[WINNER RATE CALCULATOR] Found state {}".format(state))
            self.act_sentinel = state["act_sentinel"]
            self.civs = state["civs"]
            self.sentinels = state["sentinels"]
            self.finished = state["finished"]
        else:
            self.act_sentinel = self.sentinel_amount
            self.civs = []
            self.sentinels = []
            self.finished = 0
            self.__save_state()

    def __save_state(self):
        self.state_handler.update_state({"act_sentinel": self.act_sentinel, "civs": self.civs,
        "sentinels": self.sentinels, "finished": self.finished})

    def __callback(self, ch, method, properties, body):
        logging.info("To send winner rate result")
        players_by_civ = json.loads(body)

        if "sentinel" in players_by_civ:
            sentinel = players_by_civ["sentinel"]
            if sentinel not in self.sentinels and not self.finished:
                self.sentinels.append(sentinel)
                self.act_sentinel -= 1
                if self.act_sentinel == 0:
                    self.act_sentinel = self.sentinel_amount
                    self.civs = []
                    self.sentinels = []
                    self.finished = 1
                    logging.info("[WINNER_RATE_CALCULATOR] End of file")
                    self.interface_communicator.send_finish_message()
                self.__save_state()
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        self.finished = 0
        for civ in players_by_civ:
            if civ in self.civs:
                continue
            self.civs.append(civ)
            victories = 0
            players = players_by_civ[civ]
            for player in players:
                if player[self.winner_field] == "True":
                    victories += 1
            
            act_request = players[0]["act_request"]
            
            winner_rate = (victories / len(players)) * 100
            result = {civ: winner_rate, "act_request": act_request}

            send_message(ch, json.dumps(result), queue_name=f"request_{act_request}", exchange_name=self.output_exchange)            
        self.__save_state()
        ch.basic_ack(delivery_tag=method.delivery_tag)
    