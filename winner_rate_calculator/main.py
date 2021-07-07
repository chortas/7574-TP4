#!/usr/bin/env python3
import logging
import os

from winner_rate_calculator import WinnerRateCalculator

def parse_config_params():
    config_params = {}
    try:
        config_params["grouped_players_queue"] = os.environ["GROUPED_PLAYERS_QUEUE"]
        config_params["output_queue"] = os.environ["OUTPUT_QUEUE"]
        config_params["winner_field"] = os.environ["WINNER_FIELD"]
        
    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    winner_rate_calculator = WinnerRateCalculator(config_params["grouped_players_queue"], 
    config_params["output_queue"], config_params["winner_field"])
    winner_rate_calculator.start()

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