import logging
import os
import uuid

from PIL import Image
import pyqrcode

logger = logging.getLogger(__name__)


class QRCode:
    def __init__(self, base_url, qr_cache_path, max_size, qr_image_path) -> None:
        self.mapping = {}
        self.base_url = base_url
        self.qr_cache_path = qr_cache_path
        self.max_size = max_size
        self.qr_image_path = qr_image_path

    def add(self, alias: str):
        try:
            if len(self.mapping) >= self.max_size:  # removes files if exceeds size
                remove_alias, remove_path = self.mapping.popitem()
                os.remove(remove_path)
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
