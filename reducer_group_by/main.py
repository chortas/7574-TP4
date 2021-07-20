#!/usr/bin/env python3
import logging
import os

from reducer_group_by import ReducerGroupBy
from common.heartbeat_sender import HeartbeatSender

def parse_config_params():
    config_params = {}
    try:
        config_params["group_by_queue"] = os.environ["GROUP_BY_QUEUE"]
        config_params["group_by_field"] = os.environ["GROUP_BY_FIELD"]
        config_params["grouped_players_queue"] = os.environ["GROUPED_PLAYERS_QUEUE"]
        config_params["sentinel_amount"] =  (os.environ["SENTINEL_AMOUNT"]
                                            if "SENTINEL_AMOUNT" in os.environ
                                            else 1) 
        config_params["batch_to_send"] = os.environ["BATCH_TO_SEND"]
        config_params["id"] = os.environ["ID"]

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    heartbeat_sender = HeartbeatSender(config_params["id"])

    reducer_group_by = ReducerGroupBy(config_params["id"], config_params["group_by_queue"],
    config_params["group_by_field"], config_params["grouped_players_queue"], 
    int(config_params["sentinel_amount"]), int(config_params["batch_to_send"]), heartbeat_sender)

    reducer_group_by.start()

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