#!/usr/bin/env python3
import logging
import os

from filter_solo_winner_player import FilterSoloWinnerPlayer
from common.interface_communicator import InterfaceCommunicator
from common.heartbeat_sender import HeartbeatSender

def parse_config_params():
    config_params = {}
    try:
        config_params["grouped_players_queue"] = os.environ["GROUPED_PLAYERS_QUEUE"]
        config_params["output_queue"] = os.environ["OUTPUT_QUEUE"]
        config_params["rating_field"] = os.environ["RATING_FIELD"]
        config_params["winner_field"] = os.environ["WINNER_FIELD"]

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    interface_communicator = InterfaceCommunicator()
    heartbeat_sender = HeartbeatSender()

    filter_swp = FilterSoloWinnerPlayer(config_params["grouped_players_queue"], 
    config_params["output_queue"], config_params["rating_field"], 
    config_params["winner_field"], interface_communicator, heartbeat_sender)
    
    filter_swp.start()

def initialize_log():
    """
    Python custom logging initialization
    Current timestamp is added to be able to identify in docker
    compose logs the date when the log has arrived
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S',
    )

if __name__== "__main__":
    main()