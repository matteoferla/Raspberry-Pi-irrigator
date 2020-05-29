import digitalio
import board

###################################################
#
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

