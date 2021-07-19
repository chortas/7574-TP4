#!/usr/bin/env python3
import logging
import os

from join import Join
from common.heartbeat_sender import HeartbeatSender

def parse_config_params():
    config_params = {}
    try:
        config_params["match_token_exchange"] = os.environ["MATCH_TOKEN_EXCHANGE"]
        config_params["n_reducers"] = os.environ["N_REDUCERS"]
        config_params["match_consumer_routing_key"] = os.environ["MATCH_CONSUMER_ROUTING_KEY"]
        config_params["join_exchange"] = os.environ["JOIN_EXCHANGE"]
        config_params["match_id_field"] = os.environ["MATCH_ID_FIELD"]
        config_params["player_consumer_routing_key"] = os.environ["PLAYER_CONSUMER_ROUTING_KEY"]
        config_params["player_match_field"] = os.environ["PLAYER_MATCH_FIELD"]
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
    
    join = Join(config_params["id"], config_params["match_token_exchange"], int(config_params["n_reducers"]),
    config_params["match_consumer_routing_key"], config_params["join_exchange"], 
    config_params["match_id_field"], config_params["player_consumer_routing_key"],
    config_params["player_match_field"], heartbeat_sender)

    join.start()

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