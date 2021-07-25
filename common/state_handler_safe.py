import os
import logging
import json

from .state_handler import StateHandler
from .filelock import FileLock

class StateHandlerSafe(StateHandler):
    def __init__(self, node_id, filename="state.json"):
        StateHandler.__init__(self, node_id, filename)
        self.filelock = FileLock()

    def update_state(self, state):
        f = self.filelock.acquire_writeonly(self.path)
        logging.info("[STATE HANDLER] Saving state")
        json.dump(state, f)
        self.filelock.release(f)
        logging.info("[STATE HANDLER] State saved")
        

    def get_state(self):
        logging.info("[STATE HANDLER] Getting state")
        try:
            if not os.path.exists(self.path): 
                return {}
            f = self.filelock.acquire_readonly(self.path)
            state = json.load(f)
            self.filelock.release(f)
            return state
        except:
            logging.info("[STATE HANDLER] Error while getting state")
            return {}