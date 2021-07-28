#!/usr/bin/env python3
import logging
import os

from group_by import GroupBy
from common.utils import *
from common.heartbeat_sender import HeartbeatSender

def parse_config_params():
    config_params = {}
    try:
        config_params["queue_name"] = os.environ["QUEUE_NAME"]
        config_params["n_reducers"] = os.environ["N_REDUCERS"]
        config_params["group_by_queue"] = os.environ["GROUP_BY_QUEUE"]
        config_params["group_by_field"] = os.environ["GROUP_BY_FIELD"]
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

    group_by = GroupBy(int(config_params["n_reducers"]), config_params["group_by_queue"], 
    config_params["group_by_field"], config_params["queue_name"], heartbeat_sender, config_params["id"])
    
    group_by.start()

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