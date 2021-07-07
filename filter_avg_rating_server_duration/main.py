#!/usr/bin/env python3
import logging
import os

from filter_avg_rating_server_duration import FilterAvgRatingServerDuration

def parse_config_params():
    config_params = {}
    try:
        config_params["match_queue"] = os.environ["MATCH_QUEUE"]
        config_params["output_queue"] = os.environ["OUTPUT_QUEUE"]
        config_params["avg_rating_field"] = os.environ["AVG_RATING_FIELD"]
        config_params["server_field"] = os.environ["SERVER_FIELD"]
        config_params["duration_field"] = os.environ["DURATION_FIELD"]
        config_params["id_field"] = os.environ["ID_FIELD"]

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

def main():
    initialize_log()

    config_params = parse_config_params()

    filter_arsd = FilterAvgRatingServerDuration(config_params["match_queue"], 
    config_params["output_queue"], config_params["avg_rating_field"], 
    config_params["server_field"], config_params["duration_field"], config_params["id_field"])
    filter_arsd.start()

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