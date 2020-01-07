#MCP3008 modules
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_dht
import busio
import digitalio
import board
import time
#from datetime import datetime

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