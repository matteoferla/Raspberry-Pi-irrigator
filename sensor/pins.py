#MCP3008 modules
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
#import adafruit_dht
import Adafruit_DHT
import busio
import digitalio
import board
import time
import RPi.GPIO as GPIO
from collections import namedtuple

### startup ###############################################################

spi = busio.SPI(clock=11, MISO=9, MOSI=10)
cs = digitalio.DigitalInOut(board.D5)
mcp = MCP.MCP3008(spi, cs)

###################################################

class Pins:
    """
   * DHT11 is connected to GPIO17 and powered by 3.3V without a pull resistor (DHT22 sensor not working)
    * MCP3008 is D_out -> MISO: GPIO9, D_in -> MOSI:GPIO10, Clock: GPIO11 and CS GPIO05
    * Pumps are connected to GPIO23 and GPIO24 (the two pins between two GND)
    """

    mcp = mcp
    pumps = (digitalio.DigitalInOut(board.D23), digitalio.DigitalInOut(board.D24))
    pumps[0].direction = digitalio.Direction.OUTPUT
    pumps[1].direction = digitalio.Direction.OUTPUT
    spill = digitalio.DigitalInOut(board.D20)
    spill.direction = digitalio.Direction.INPUT
    soil_limits = [1.2, 3.2]

    @property
    def dht(self):
        # imitating the circuitpython dht
        fauxDHT = namedtuple('DHT', ['humidity', 'temperature'])
        return fauxDHT(*Adafruit_DHT.read(22, 17))

    @property
    def brightness(self):
        """
        Corrected to percent based on the values outputted by using 10k&Omega; and 1M&Omega; resistors.
        :return: brightness
        """
        return round((AnalogIn(mcp, MCP.P0).voltage -1.7)/(2.2-1.7)*100)

    @property
    def temperature(self):
        for i in range(10):
            t = self.dht.temperature
            if t is not None:
                return t
        else:
            raise ValueError('Cannot read temperature')

    @property
    def humidity(self):
        for i in range(10):
            h = self.dht.humidity
            if h is not None:
                return h
        else:
            raise ValueError('Cannot read humidity')

    def get_soil_moisture(self, number):
        pin = [MCP.P3, MCP.P4][number]
        return round(100 - (AnalogIn(self.mcp, pin).voltage - self.soil_limits[0]) / (self.soil_limits[1] - self.soil_limits[0]) * 100)

    @property
    def soil_B_moisture(self):
        return self.get_soil_moisture(1)

    @property
    def soil_A_moisture(self):
        return self.get_soil_moisture(0)

    def engage_pump(self, number=0, secs=1):
        self.pumps[number].value = True
        time.sleep(secs)
        self.pumps[number].value = False
        return self


    @property
    def tank_filled(self):
        if self.tank_level > 1.5:
            return True
        else:
            return False

    @property
    def tank_level(self):
        return AnalogIn(self.mcp, MCP.P1).voltage

    @property
    def spill_analog(self):
        return AnalogIn(self.mcp, MCP.P2).voltage

    @property
    def spilled(self):
        # Three pronged: error, D0 and A0
        # just in case.
        try:
            if not self.spill.value:
                return 'Spill detected by the digital pin'
            elif self.spill_analog < 2:
                return 'Spill detected by the analogue pin '+self.spill_analog
            else:
                return None
        except Exception as err:
            return f'Possible spill caused by a shortcircuit ({err})'

    def cleanup(self):
        GPIO.cleanup()