import logging
import os
import uuid
import pyqrcode

logger = logging.getLogger(__name__)

class QRCode:
    def __init__(self, base_url, qr_folder_path, max_cache_size) -> None:

        self.qr_folder_path = qr_folder_path
        if not os.path.exists(self.qr_folder_path):
            os.mkdir(self.qr_folder_path)
        self.mapping = {}
        self.base_url = base_url
        self.max_cache_size = max_cache_size

    def add(self, alias: str):
        try:
            # remove files to remain under cache size
            if len(self.mapping) >= self.max_cache_size:  
                removed_qr_path = self.mapping.popitem()
                os.remove(removed_qr_path)

            # sets the name of the qr code file to a uuid string
            qr_url = os.path.join(self.base_url, alias)
            qr_path = os.path.join(self.qr_folder_path, str(uuid.uuid4()) + ".png")

            qrcode = pyqrcode.create(qr_url)
            qrcode.png(qr_path, scale=10)
            
            self.mapping[alias] = qr_path

            return qr_path
        except FileNotFoundError:
            logger.exception(f"Could not find folder {self.qr_folder_path}:")
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
