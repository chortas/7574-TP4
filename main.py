#!/usr/bin/env python3
import logging
import os

from client import Client

def parse_config_params():
    config_params = {}
    try:
        config_params["match_queue"] = os.environ["MATCH_QUEUE"]
        config_params["match_file"] = os.environ["MATCH_FILE"]
        config_params["player_queue"] = os.environ["PLAYER_QUEUE"]
        config_params["player_file"] = os.environ["PLAYER_FILE"]
        config_params["batch_to_send"] = os.environ["BATCH_TO_SEND"]
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    client = Client(config_params["match_queue"], config_params["match_file"], 
    config_params["player_queue"], config_params["player_file"], 
    int(config_params["batch_to_send"]))
    client.start()

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