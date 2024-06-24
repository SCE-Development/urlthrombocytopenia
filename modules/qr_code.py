import qrcode
import uuid
import os
import logging

logger = logging.getLogger(__name__)

class QRCode:
    def __init__(self, base_url, qr_cache_path, max_size) -> None:
        self.mapping = {}
        self.base_url = base_url
        self.qr_cache_path = qr_cache_path
        self.max_size = max_size

    def add(self, alias: str):
        try:    
            if len(self.mapping) >= self.max_size: #removes files if exceeds size
                remove_alias,remove_path = self.mapping.popitem()
                os.remove(remove_path)
                logger.debug(f"Removed qrcode with alias: {remove_alias} to free space.")
                
            url = os.path.join(self.base_url, alias) 
            path = os.path.join(self.qr_cache_path, str(uuid.uuid4()) + ".jpg")

            img = qrcode.make(url)
            img.save(path)
            self.mapping[alias] = path

            return path
        except FileNotFoundError:
            logger.exception(f"Could not find folder {self.qr_cache_path}:")
        except OSError:
            logger.exception(f"Error occured when handling files:")
        except Exception:
            logger.exception(f"An unexpected error occured")

    def find(self, alias: str):
        return self.mapping.get(alias)

    def clear(self):
        try: 
            for alias, path in self.mapping.items():
                if os.path.exists(path):
                    os.remove(path)
            self.mapping.clear()
            logger.debug("Cleared qr code folder")
        except Exception:
            logger.exception("An unexpected error occurred clearing the cache")
