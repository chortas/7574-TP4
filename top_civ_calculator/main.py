#!/usr/bin/env python3
import logging
import os

from top_civ_calculator import TopCivCalculator
from common.interface_communicator import InterfaceCommunicator
from common.heartbeat_sender import HeartbeatSender

def parse_config_params():
    config_params = {}
    try:
        config_params["grouped_players_queue"] = os.environ["GROUPED_PLAYERS_QUEUE"]
        config_params["output_exchange"] = os.environ["OUTPUT_EXCHANGE"]
        config_params["id_field"] = os.environ["ID_FIELD"]
        config_params["sentinel_amount"] = os.environ["SENTINEL_AMOUNT"]
        config_params["id"] = os.environ["ID"]
        
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()
    
    interface_communicator = InterfaceCommunicator()
    heartbeat_sender = HeartbeatSender(config_params["id"])

    top_civ_calculator = TopCivCalculator(config_params["id"], config_params["grouped_players_queue"], 
    config_params["output_exchange"], config_params["id_field"], 
    int(config_params["sentinel_amount"]), interface_communicator, heartbeat_sender)

    top_civ_calculator.start()

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