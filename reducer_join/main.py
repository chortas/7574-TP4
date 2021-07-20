#!/usr/bin/env python3
import logging
import os

from reducer_join import ReducerJoin
from common.heartbeat_sender import HeartbeatSender

def parse_config_params():
    config_params = {}
    try:
        config_params["join_exchange"] = os.environ["JOIN_EXCHANGE"]
        config_params["match_consumer_routing_key"] = os.environ["MATCH_CONSUMER_ROUTING_KEY"]
        config_params["player_consumer_routing_key"] = os.environ["PLAYER_CONSUMER_ROUTING_KEY"]
        config_params["grouped_result_queue"] = os.environ["GROUPED_RESULT_QUEUE"]
        config_params["match_id_field"] = os.environ["MATCH_ID_FIELD"]
        config_params["player_match_field"] = os.environ["PLAYER_MATCH_FIELD"]
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

    reducer_join = ReducerJoin(config_params["id"], config_params["join_exchange"], 
    config_params["match_consumer_routing_key"],config_params["player_consumer_routing_key"],
    config_params["grouped_result_queue"], config_params["match_id_field"],
    config_params["player_match_field"], int(config_params["batch_to_send"]), heartbeat_sender)

    reducer_join.start()

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