import logging
import os
import uuid
import json

from PIL import Image
import pyqrcode

from modules.metrics import MetricsHandler

logger = logging.getLogger(__name__)


class QRCode:
    def __init__(
        self,
        base_url,
        qr_cache_path,
        max_size,
        cache_state_file=None,
        qr_image_path=None,
    ) -> None:
        self.mapping = {}
        self.base_url = base_url
        self.qr_cache_path = qr_cache_path
        self.max_size = max_size
        self.cache_state_file = cache_state_file
        self.qr_image_path = qr_image_path

        # read from JSON file to initialize cache at server startup
        if self.cache_state_file is not None:
            self.read_cache_state()

    def add(self, alias: str):
        try:
            if len(self.mapping) >= self.max_size:  # removes files if exceeds size
                remove_alias, remove_path = self.mapping.popitem()
                # Decrease the qr_code_cache_size_in_bytes custom prometheus metric by the file size of the QR Code that was removed
                MetricsHandler.qr_code_cache_size_in_bytes.dec(
                    os.path.getsize(remove_path)
                )
                os.remove(remove_path)
                # Decrease the qr_code_cache_size custom prometheus metric by 1 after a QR Code is removed
                MetricsHandler.qr_code_cache_size.dec(1)
                logger.debug(
                    f"Removed qrcode with alias: {remove_alias} to free space."
                )

            url = os.path.join(self.base_url, alias)
            path = os.path.join(self.qr_cache_path, str(uuid.uuid4()) + ".png")

            # Create a QR Code with high error tolerance (30%) to accommodate for the logo placed in the center
            qrcode = pyqrcode.create(url, error="H")
            # Save the generated QR Code
            qrcode.png(path, scale=10)

            # Open the saved QR Code to add the logo in the center
            qrcode_image = Image.open(path)
            qrcode_image = qrcode_image.convert("RGBA")

            if self.qr_image_path is not None:
                sce_logo = Image.open(self.qr_image_path)

                qrcode_width, qrcode_height = qrcode_image.size
                # Resize sce_logo to be 20% of the qr code's width and height
                sce_logo_width = int(qrcode_width * 0.2)
                sce_logo_height = int(qrcode_height * 0.2)
                sce_logo = sce_logo.resize((sce_logo_width, sce_logo_height))

                # Calculate the coordinates for the logo to be centered on the QR Code
                top_left_x = int((qrcode_width / 2) - (sce_logo_width / 2))
                top_left_y = int((qrcode_height / 2) - (sce_logo_height / 2))
                bottom_right_x = int((qrcode_width / 2) + (sce_logo_width / 2))
                bottom_right_y = int((qrcode_height / 2) + (sce_logo_height / 2))

            box = [top_left_x, top_left_y, bottom_right_x, bottom_right_y]
            # Place the logo in the center of the QR Code
            qrcode_image.paste(sce_logo, box)
            # Save the QR Code again after the logo has been added
            qrcode_image.save(path, scale=10)
            # Increase the qr_code_cache_size_in_bytes custom prometheus metric by the size of the newly created QR Code
            MetricsHandler.qr_code_cache_size_in_bytes.inc(os.path.getsize(path))
            # Increase the qr_code_cache_size custom prometheus metric by 1 after a new QR Code is added
            MetricsHandler.qr_code_cache_size.inc()

            self.mapping[alias] = path

            return path
        except FileNotFoundError:
            logger.exception(f"Could not find folder {self.qr_cache_path}:")
        except OSError:
            logger.exception("Error occured when handling files:")
        except Exception:
            logger.exception("An unexpected error occured")

    def find(self, alias: str):
        return self.mapping.get(alias)

    def delete(self, alias: str):
        path = self.mapping.get(alias)
        if alias in self.mapping:
            self.mapping.pop(alias)
        if os.path.exists(path):
            # Decrease the qr_code_cache_size_in_bytes custom prometheus metric by the file size of the QR Code that was removed
            MetricsHandler.qr_code_cache_size_in_bytes.dec(os.path.getsize(path))
            os.remove(path)
            # Set the qr_code_cache_size custom prometheus metric to the length of self.mapping after a QR Code is removed
            MetricsHandler.qr_code_cache_size.set(len(self.mapping))
            logger.debug(f"removed qr code at {path} for alias {alias}")

    def clear(self):
        try:
            for alias in self.mapping.keys():
                self.delete(alias)
            self.mapping.clear()
            logger.debug("Cleared qr code folder")
        except Exception:
            logger.exception("An unexpected error occurred clearing the cache")

    # when server starts, load the cache state from JSON file
    def read_cache_state(self):
        try:
            with open(self.cache_state_file, "r") as json_file:
                self.mapping = json.load(json_file)
        except FileNotFoundError:
            logger.exception(
                f"Could not find cache state file: {self.cache_state_file}"
            )
        except json.JSONDecodeError:
            logger.exception(
                f"Error when reading JSON from cache state file: {self.cache_state_file}"
            )
        except Exception:
            logger.exception(
                f"An unexpected error occurred while reading cache state file: {self.cache_state_file}"
            )

    # when server shuts down, save the cache state to file
    def write_cache_state(self):
        try:
            with open(self.cache_state_file, "w") as json_file:
                json.dump(self.mapping, json_file)
        except Exception:
            logger.exception(
                f"An unexpected error occurred while saving cache state file: {self.cache_state_file}"
            )
