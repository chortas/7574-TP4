import os
import logging
import json

class StateHandler:
    def __init__(self, node_id, filename = "state.json"):
        self.id = node_id
        self.directory = "states/{}/".format(node_id)
        self.filename = filename
        self.path = "./" + self.directory + self.filename
        self.tmp_path = self.path + "_tmp"
        os.makedirs(self.directory, exist_ok=True)

    def update_state(self, state):
        with open(self.tmp_path, "w") as file:
            json.dump(state, file)
        os.rename(self.tmp_path, self.path)

    def get_state(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, "r") as file:
                    state = json.load(file)
                return state
            return {}
        except:
            logging.info("[STATE HANDLER] Error while getting state")
            return {}