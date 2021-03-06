#!/usr/bin/env python3
import logging
import os

from monitor import Monitor

def parse_config_params():
    config_params = {}
    try:
        config_params["internal_port"] = os.environ["INTERNAL_PORT"]
        config_params["timeout"] = os.environ["TIMEOUT"]
        config_params["id"] = os.environ["ID"]
        config_params["is_leader"] = os.environ["IS_LEADER"] == "True"
        config_params["sleep_frequency"] = os.environ["SLEEP_FREQUENCY"]
    
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    monitor = Monitor(config_params["id"], int(config_params["internal_port"]), 
    int(config_params["timeout"]), config_params["is_leader"], 
    int(config_params["sleep_frequency"]))
    
    monitor.start()

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