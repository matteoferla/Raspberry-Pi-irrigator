__doc__ = """This is just a mock sensor to test the code in PyCharm on my Macbook,
while the real sensor class is tested in a Jupyter notebook hosted on the pi.
"""

import random
from PIL import Image

class MockPins:

    @property
    def moisture(self):
        return random.randint(0, 100)

    @property
    def brightness(self):
        return random.randint(0, 100)

    @property
    def temperature(self):
        return random.randint(20, 30)

    @property
    def humidity(self):
        return random.randint(0, 100)

    def engage_pump(self, number=0, secs=1):
        return self

class MockCam:
    def __init__(self):
        self.camera = None

    def capture(self):
        return Image.open('irrigator.jpg')

    def rotate(self, im):
        return im

    def equalize(self, im):
        return im

    def whitebalance(self, im):
        return im