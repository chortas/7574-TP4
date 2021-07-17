import os
import logging
import json

class StateHandler:
    def __init__(self, node_id):
        self.id = node_id
        self.directory = "states/{}/".format(node_id)
        self.filename = "state.json"
        self.path = "./" + self.directory + self.filename
        os.makedirs(self.directory, exist_ok=True)

    def update_state(self, state):
        logging.info("[STATE HANDLER] Saving state")
        with open(self.path, "w") as file:
            json.dump(state, file)

    def get_state(self):
        logging.info("[STATE HANDLER] Geting state")
        if os.path.exists(self.path):
            with open(self.path, "r") as file:
                state = json.load(file)
            return state
        return {}