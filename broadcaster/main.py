#!/usr/bin/env python3
import logging
import os

from broadcaster import Broadcaster
from common.heartbeat_sender import HeartbeatSender

def parse_config_params():
    config_params = {}
    try:
        config_params["row_queue"] = os.environ["ROW_QUEUE"]
        config_params["queues_to_send"] = os.environ["QUEUES_TO_SEND"].split(',')
        config_params["id"] = os.environ["ID"]

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    heartbeat_sender = HeartbeatSender()

    broadcaster = Broadcaster(config_params["row_queue"], config_params["queues_to_send"],
    heartbeat_sender, config_params["id"])
    
    broadcaster.start()

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