import os.path
import shutil
import subprocess
import time
from tempfile import TemporaryDirectory
from typing import Tuple

from PIL import Image, ImageGrab


def capture_screen() -> Tuple[Image.Image, float]:
    if shutil.which('scrot'):
        with TemporaryDirectory() as td:
            filename = os.path.join(td, 'screen.png')
            timestamp = time.time()
            process = subprocess.run([shutil.which('scrot'), '-z', '-o', filename])
            process.check_returncode()

            image = Image.open(filename)
            image.load()
    else:
        timestamp = time.time()
        image = ImageGrab.grab()

    return image, timestamp
