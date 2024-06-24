import pyqrcode
from PIL import Image
import uuid
import os


class QRCode:
    def __init__(self, qr_code_directory: str) -> None:
        """
        __init__ Initializes the qr_code_directory and mapping fields, and creates the qr_code_directory if it does not exist.

        Args:
            qr_code_directory (str): The path to store the generated qr codes.
        """
        self.qr_code_directory = qr_code_directory
        if not os.path.exists(self.qr_code_directory):
            os.mkdir(self.qr_code_directory)
        self.mapping = {}

    def add(self, alias: str, url: str) -> str:
        """
        add Generates a new QR Code and saves it in the qr_code_directory.

        Generates a qr code based on the url passed as an argument. Inserts the SCE logo in the center of the qr code.

        Args:
            alias (str): The alias associated with the qr code url.
            url (str): The url used to generate the qr code.

        Returns:
            str: The filepath of the newly created qr code.
        """
        # Generate a new uuid string as the qr code filename
        filename = str(f"{uuid.uuid4()}.png")
        filepath = os.path.join(self.qr_code_directory, filename)
        # Create a QR Code with high error tolerance (30%) to accommodate for the logo placed in the center
        qrcode = pyqrcode.create(url, error="H")
        # Save the generated QR Code
        qrcode.png(filepath, scale=10)

        # Open the saved QR Code to add the logo in the center
        qrcode_image = Image.open(filepath)
        qrcode_image = qrcode_image.convert("RGBA")

        sce_logo = Image.open("./assets/SCE_logo.png")

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
        qrcode_image.save(filepath, scale=10)

        # Store the filepath with the current alias
        self.mapping[alias] = filepath

        return filepath

    def find(self, alias: str) -> str:
        """
        find Returns the path to the alias if it exists.

        Args:
            alias (str): The url that needs to be looked up.

        Returns:
            str: Returns the path to the alias if it exists and None if it does not exist.
        """
        return self.mapping[alias] if alias in self.mapping else None
