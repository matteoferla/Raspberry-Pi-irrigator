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
import operator
import functools
from datetime import datetime
import os

class Cam:
    def __init__(self):
        self.camera = PiCamera()
        if not os.path.exists('album'):
            os.mkdir('album')
        if not os.path.exists('album/plant_photos'):
            os.mkdir('album/plant_photos')


    def capture(self):
        stream = BytesIO()
        self.camera.start_preview()
        time.sleep(5)
        self.camera.capture(stream, format='jpeg')
        stream.seek(0)
        im = Image.open(stream)
        return im

    def rotate(self, im):
        return im.transpose(Image.ROTATE_180)

    def equalize(self, im):
        # https://stackoverflow.com/questions/7116113/normalize-histogram-brightness-and-contrast-of-a-set-of-images-using-python-im
        h = im.convert("L").histogram()
        lut = []
        for b in range(0, len(h), 256):
            # step size
            step = functools.reduce(operator.add, h[b:b + 256]) / 255
            # create equalization lookup table
            n = 0
            for i in range(256):
                lut.append(n / step)
                n = n + h[i + b]
        # map image through lookup table
        return im.point(lut * 3)

    def whitebalance(self, im):
        # code copied from https://codeandlife.com/2019/08/17/correcting-image-white-balance-with-python-pil-and-numpy/
        # in turn from https://stackoverflow.com/a/34913974/2721685
        def rgb2ycbcr(im):
            xform = np.array([[.299, .587, .114], [-.1687, -.3313, .5], [.5, -.4187, -.0813]])
            ycbcr = im.dot(xform.T)
            ycbcr[:, :, [1, 2]] += 128
            return ycbcr  # np.uint8(ycbcr)

        def ycbcr2rgb(im):
            xform = np.array([[1, 0, 1.402], [1, -0.34414, -.71414], [1, 1.772, 0]])
            rgb = im.astype(np.float)
            rgb[:, :, [1, 2]] -= 128
            rgb = rgb.dot(xform.T)
            np.putmask(rgb, rgb > 255, 255)
            np.putmask(rgb, rgb < 0, 0)
            return np.uint8(rgb)

        data = np.asarray(im)
        # Convert data and sample to YCbCr
        ycbcr = rgb2ycbcr(data)
        # ysub = rgb2ycbcr(sub)
        # Calculate mean components
        yc = list(np.mean(ycbcr[:, :, i]) for i in range(3))
        # Center cb and cr components of image based on sample
        for i in range(1, 3):
            ycbcr[:, :, i] = np.clip(ycbcr[:, :, i] + (128 - yc[i]), 0, 255)
        rgb = ycbcr2rgb(ycbcr)  # Convert back
        return Image.fromarray(rgb)

    def save(self, im):
        im.save('static/plant_photos/'+datetime.now().isoformat(timespec='seconds')+'.jpg')

class Pins:
    """
   * DHT11 is connected to GPIO17 and powered by 3.3V without a pull resistor (DHT22 sensor not working)
    * MCP3008 is MISO: GPIO9, MOSI:GPIO10, Clock: GPIO11 and CS GPIO05
    * Pumps are connected to GPIO23 and GPIO24 (the two pins between two GND)
    """
    spi = busio.SPI(clock=11, MISO=9, MOSI=10)
    cs = digitalio.DigitalInOut(board.D5)
    mcp = MCP.MCP3008(spi, cs)
    dht = adafruit_dht.DHT11(board.D17)
    pumps = (digitalio.DigitalInOut(board.D23), digitalio.DigitalInOut(board.D24))
    pumps[0].direction = digitalio.Direction.OUTPUT
    pumps[1].direction = digitalio.Direction.OUTPUT

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
        try:
            return self.dht.humidity
        except:
            pass

    def engage_pump(self, number=0, secs=1):
        self.pumps[number].value = True
        time.sleep(secs)
        self.pumps[number].value = False
        return self