from models import db, Measurement  # Models initiated.
## PI
from warnings import warn
try:
    from sensor import Pins, Photo  # reads pins
except Exception as error:
    from sensor.camera import Photo
    warn(f'Sensors appear non functional: {error}')
    class Pins:
        def cleanup(self):
            pass

## Not PI (Dev)
# from mock_sensor import MockPins as Pins
# from mock_sensor import MockCam as Cam

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from signal import signal, SIGINT
from slack import slack
from threading import Lock


class Schedule:
    lock = Lock() #stop interferring with each other.
    brightness_stack = []

    def __init__(self, sense=True, photo=True, spill=True, bright=True):
        self.pins = Pins()
        signal(SIGINT, self.death_handler)
        ## Scheduler
        scheduler = BackgroundScheduler()
        if sense:
            scheduler.add_job(func=self.sense, trigger="interval", hours=1)
        if photo:
            scheduler.add_job(func=self.photo, trigger="interval", hours=1)
        if spill:
            scheduler.add_job(func=self.check_spill, trigger="interval", minutes=1)
        if bright:
            scheduler.add_job(func=self.continuous_bright, trigger="interval", minutes=1)
        scheduler.start()

    def photo(self):
        with self.lock:
            Photo()


    def death_handler(self, signal_received, frame):
        try:
            if Photo._camera and not Photo._camera.closed:
                Photo._camera.close()
        except:
            pass
        if self.lock.locked(): self.lock.release()
        self.pins.cleanup()
        print('SIGINT or CTRL-C detected. Exiting gracefully')
        slack('Shutting down gracefully')
        exit(0)

    def sense(self):
        """
        Logs data and waters if needed for a max of 60 secs.
        :return:
        """
        try:
            with self.lock:
                self.brightness_stack.append(self.pins.brightness)
                mean_b = sum(self.brightness_stack)/len(self.brightness_stack)
                self.brightness_stack = []
                datum = Measurement(datetime=datetime.now(),
                                    temperature=self.pins.temperature,
                                    humidity=self.pins.humidity,
                                    soil_A_moisture=self.pins.soil_A_moisture,
                                    soil_B_moisture=self.pins.soil_B_moisture,
                                    brightness=mean_b,
                                    wateringtime_A=0,
                                    wateringtime_B=0)
                db.session.add(datum)
                db.session.commit()
        except Exception as err:
            slack('Sensing failed: '+str(err))
            print(str(err))

    def water(self, datum):
        with self.lock:
            for i in (0, 1):
                wateringtime = 0
                while self.pins.get_soil_moisture(i) < 85:
                    if wateringtime >= 30:
                        slack('Soil moisture {m}% but has water for {t} already' \
                              .format(m=self.pins.get_soil_moisture(i), t=wateringtime))
                        break
                    self.pins.engage_pump(number=i, secs=10)
                    wateringtime += 10
                if i == 0:
                    datum.wateringtime_A = wateringtime
                else:
                    datum.wateringtime_B = wateringtime

    def check_tank(self):
        with self.lock:
            if not self.pins.tank_filled:
                slack('Water is getting low')
            else:
                pass

    def check_spill(self):
        with self.lock:
            r = self.pins.spilled
            if r:
                slack(r)

    def continuous_bright(self):
        with self.lock:
            self.brightness_stack.append(self.pins.brightness)


