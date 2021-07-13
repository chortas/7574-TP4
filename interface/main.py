#!/usr/bin/env python3
import logging
import os

from interface import Interface
from common.utils import *

def parse_config_params():
    config_params = {}
    try:
        config_params["api_port"] = int(os.environ["API_PORT"])
        config_params["internal_port"] = int(os.environ["INTERNAL_PORT"])
        config_params["sentinel_amount"] =  (int(os.environ["SENTINEL_AMOUNT"])
                                            if "SENTINEL_AMOUNT" in os.environ
                                            else 1) 
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    interface = Interface(config_params['api_port'], config_params['internal_port'], config_params["sentinel_amount"])
    interface.start()

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