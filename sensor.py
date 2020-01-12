#MCP3008 modules
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_dht
import busio
import digitalio
import board
import time
from picamera import PiCamera
from PIL import Image
from io import BytesIO
import numpy as np
from datetime import datetime
import os
import RPi.GPIO as GPIO

if not os.path.exists('static'):
    os.mkdir('static')
if not os.path.exists('static/plant_photos'):
    os.mkdir('static/plant_photos')

spi = busio.SPI(clock=11, MISO=9, MOSI=10)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)

class Pins:
    """
   * DHT11 is connected to GPIO17 and powered by 3.3V without a pull resistor (DHT22 sensor not working)
    * MCP3008 is MISO: GPIO9, MOSI:GPIO10, Clock: GPIO11 and CS GPIO05
    * Pumps are connected to GPIO23 and GPIO24 (the two pins between two GND)
    """

    mcp = mcp
    dht = adafruit_dht.DHT11(board.D17)
    pumps = (digitalio.DigitalInOut(board.D23), digitalio.DigitalInOut(board.D24))
    pumps[0].direction = digitalio.Direction.OUTPUT
    pumps[1].direction = digitalio.Direction.OUTPUT
    rain = digitalio.DigitalInOut(board.D20)

    @property
    def moisture(self):
        return round(100 - AnalogIn(self.mcp, MCP.P0).voltage/3.26*100)

    @property
    def brightness(self):
        """
        Corrected to percent where 100% is as bright as it gets, while 30% is pitch darkness.
        The 0.3V is the value when the gnd is pull out from the photoresistor
        :return: brightness
        """
        return round(100 - AnalogIn(self.mcp, MCP.P1).voltage/0.30*100)

    @property
    def temperature(self):
        while True:
            try:
                return self.dht.temperature
            except:
                pass

    @property
    def humidity(self):
        while True:
            try:
                d = self.dht.humidity
                assert d < 101
                return self.dht.humidity
            except:
                pass

    def engage_pump(self, number=0, secs=1):
        self.pumps[number].value = True
        time.sleep(secs)
        self.pumps[number].value = False
        return self

    @property
    def tank_filled(self):
        if AnalogIn(self.mcp, MCP.P2).voltage > 1.5:
            return True
        else:
            return False

    @property
    def spilled(self):
        # Three pronged: error, D0 and A0
        # just in case.
        try:
            if self.rain.value:
                return True
            elif AnalogIn(self.mcp, MCP.P3).voltage < 3:
                return True
            else:
                return False
        except:
            return True


    def cleanup(self):
        GPIO.cleanup()

class Flash:
    light = digitalio.DigitalInOut(board.D21)
    light.direction = digitalio.Direction.OUTPUT
    strip = (digitalio.DigitalInOut(board.D13), #R
             digitalio.DigitalInOut(board.D19), #G
             digitalio.DigitalInOut(board.D26)) #B
    for i in range(3):
        strip[i].direction = digitalio.Direction.OUTPUT

    def __init__(self, mode='strip'):
        self.mode = mode
        assert mode in ('led', 'strip')

    def __enter__(self):
        if self.mode == 'strip':
            for i in range(3): self.strip[i].value = True
        else:
            self.light = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.light = False
        for i in range(3): self.strip[i].value = False

class Photo:
    _camera = None
    # _camera  is a SIGINT death safeguard.
    # it is this or the gc ...

    def __init__(self):
        self.data = np.zeros((480, 720, 3))
        with Flash(mode='led'):
            while np.max(self.data) < 255:
                np.add(self.data, np.asarray(self.capture()))
        self.data = self.per_channel(self.scale, self.data)
        self.data = self.per_channel(self.histogram_stretch, self.data)
        self.image = Image.fromarray(self.data)
        self.save()

    @staticmethod
    def per_channel(fx, t):
        a = [fx(t[:, :, c]) for c in range(3)]
        return np.stack(a, axis=-1)

    @staticmethod
    def scale(matrix: np.ndarray, interval=(0, 255)) -> np.ndarray:
        minima = np.min(matrix)
        maxima = np.max(matrix)
        scaled = (matrix - minima) / (maxima - minima) * interval[1] + interval[0]
        return scaled

    def histogram_stretch(t: np.ndarray) -> np.ndarray:
        hist, bins = np.histogram(t.flatten(), 256, [0, 256])
        cdf = hist.cumsum()
        cdf_normalized = cdf * hist.max() / cdf.max()
        cdf_m = np.ma.masked_equal(cdf, 0)
        cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
        cdf = np.ma.filled(cdf_m, 0)
        return cdf[t.astype('uint8')].astype('uint8')

    def capture(self, warmup=2) -> Image:
        with PiCamera() as camera:
            self.__class__._camera = camera
            stream = BytesIO()
            camera.start_preview()
            time.sleep(warmup)
            camera.capture(stream, format='jpeg')
            self.__class__._camera = None
            stream.seek(0)
            im = Image.open(stream)
        return im

    def rotate(self) -> Image:
        # Image
        return self.image.transpose(Image.ROTATE_180)

    def save(self):
        self.image.save('static/plant_photos/'+datetime.now().isoformat(timespec='seconds')+'.jpg')