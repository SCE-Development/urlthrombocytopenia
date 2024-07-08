import logging
import os
import uuid
import pyqrcode
import json

logger = logging.getLogger(__name__)

class QRCode:
    def __init__(self, base_url, qr_cache_path, max_cache_size, cache_state_file) -> None:
        self.mapping = {}
        self.base_url = base_url
        self.qr_cache_path = qr_cache_path
        self.max_cache_size = max_cache_size
        self.cache_state_file = cache_state_file

        # read from JSON file to initialize cache at server startup
        self.read_cache_state()

    def add(self, alias: str):
        try:
            # remove files to remain under cache size
            if len(self.mapping) >= self.max_cache_size:  
                removed_qr_path = self.mapping.popitem()
                os.remove(removed_qr_path)

            # sets the name of the qr code file to a uuid string
            qr_url = os.path.join(self.base_url, alias)
            qr_path = os.path.join(self.qr_cache_path, str(uuid.uuid4()) + ".png")

            qrcode = pyqrcode.create(qr_url)
            qrcode.png(qr_path, scale=10)
            
            self.mapping[alias] = qr_path

            return qr_path
        except FileNotFoundError:
            logger.exception(f"Could not find folder {self.qr_cache_path}:")
        except OSError:
            logger.exception(f"Error occurred when handling files:")
        except Exception:
            logger.exception(f"An unexpected error occurred")

    def find(self, alias: str):
        return self.mapping.get(alias)

    def delete(self, alias: str):
        path = self.mapping.get(alias)
        if alias in self.mapping:
            self.mapping.pop(alias)
        if os.path.exists(path):
            os.remove(path)
            logger.debug(f"removed qr code at {path} for alias {alias}")

    def clear(self):
        try:
            for alias in self.mapping.keys():
                self.delete(alias)
            self.mapping.clear()
            logger.debug("Cleared qr code folder")
        except Exception:
            logger.exception("An unexpected error occurred clearing the cache")

    #  when server starts, load the cache state from file
    def read_cache_state(self):
        try:
            with open(self.cache_state_file, 'r') as json_file:
                self.mapping = json.load(json_file)
        except FileNotFoundError:
                logger.exception(f"Could not find file {self.cache_state_file}:")
        except json.JSONDecodeError:
                logger.exception(f"Error when reading JSON from cache state file: {self.cache_state_file}")
        except Exception:
                logger.exception(f"An unexpected error occurred while reading cache state file: {self.cache_state_file}")

    # when server shuts down, save the cache state to file
    def write_cache_state(self):
        try:
            with open(self.cache_state_file, 'w') as json_file:
                json.dump(self.mapping, json_file)
        except FileNotFoundError:
            logger.exception(f"Could not find file: {self.cache_state_file}")
        except Exception:
            logger.exception(f"An unexpected error occurred while saving cache state file")