#!/usr/bin/env python3
import logging
import os

from players_cleaner import PlayersCleaner

def parse_config_params():
    config_params = {}
    try:
        config_params["player_queue"] = os.environ["PLAYER_QUEUE"]
        config_params["match_field"] = os.environ["MATCH_FIELD"]
        config_params["civ_field"] = os.environ["CIV_FIELD"]
        config_params["winner_field"] = os.environ["WINNER_FIELD"]
        config_params["join_exchange"] = os.environ["JOIN_EXCHANGE"]
        config_params["join_routing_key"] = os.environ["JOIN_ROUTING_KEY"]

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    players_cleaner = PlayersCleaner(config_params["player_queue"],
    config_params["match_field"], config_params["civ_field"], config_params["winner_field"],
    config_params["join_exchange"], config_params["join_routing_key"])
    players_cleaner.start()

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