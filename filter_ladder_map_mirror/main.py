#!/usr/bin/env python3
import logging
import os

from filter_ladder_map_mirror import FilterLadderMapMirror

def parse_config_params():
    config_params = {}
    try:
        config_params["match_queue"] = os.environ["MATCH_QUEUE"]
        config_params["match_token_exchange"] = os.environ["MATCH_TOKEN_EXCHANGE"]
        config_params["top_civ_routing_key"] = os.environ["TOP_CIV_ROUTING_KEY"]
        config_params["rate_winner_routing_key"] = os.environ["RATE_WINNER_ROUTING_KEY"]
        config_params["ladder_field"] = os.environ["LADDER_FIELD"]
        config_params["map_field"] = os.environ["MAP_FIELD"]
        config_params["mirror_field"] = os.environ["MIRROR_FIELD"]
        config_params["id_field"] = os.environ["ID_FIELD"]

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    filter_lmm = FilterLadderMapMirror(config_params["match_queue"], 
    config_params["match_token_exchange"], config_params["top_civ_routing_key"], 
    config_params["rate_winner_routing_key"], config_params["ladder_field"], 
    config_params["map_field"], config_params["mirror_field"], config_params["id_field"]) 
    filter_lmm.start()

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