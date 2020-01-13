from core import app  # Flask app is initiated but without Models
from models import db, engine, Measurement  # Models initiated.
## PI
from sensor import Pins, Photo  # reads pins
## Not PI (Dev)
# from mock_sensor import MockPins as Pins
# from mock_sensor import MockCam as Cam

from waitress import serve
import os, json
# from time import sleep #avoid clash with datetime.time
from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template, request
from datetime import datetime, timedelta, time
from signal import signal, SIGINT
from slack import slack

# from scipy.signal import savgol_filter

###############  Scheduler

def sense():
    """
    Logs data and waters if needed for a max of 60 secs.
    :return:
    """
    datum = Measurement(datetime=datetime.now(),
                        temperature=pins.temperature,
                        humidity=pins.humidity,
                        moisture=pins.moisture,
                        brightness=pins.brightness,
                        wateringtime=0)
    #tasks
    water(datum)
    check_tank()
    db.session.add(datum)
    db.session.commit()

def water(datum):
    while pins.moisture < 50:
        if datum.wateringtime >= 60:
            slack('Soil moisture {m}% but has water for {t} already' \
                  .format(m=pins.moisture, t=datum.wateringtime))
            break
        pins.engage_pump(secs=10)
        datum.wateringtime += 10

def check_tank():
    if not pins.tank_filled:
        slack('Water is getting low')
    else:
        pass


############ View

def read_data(start, stop):
    dt = []
    temp = []
    hum = []
    b = []
    wt = []
    moist = []
    for m in Measurement.query.filter(Measurement.datetime > start) \
            .filter(Measurement.datetime < stop).all():  # Measurement.query.all():
        temp.append(m.temperature)
        dt.append(m.datetime)
        hum.append(m.humidity)
        b.append(m.brightness)
        wt.append(m.wateringtime)
        moist.append(m.moisture)
    # smooth = lambda a: savgol_filter(a, 31, 3).tolist()
    smooth = lambda a: a
    return dict(datetime=json.dumps([d.strftime('%Y-%m-%d %H:%M:%S') for d in dt]),
                temperature=smooth(temp),
                humidity=smooth(hum),
                moisture=smooth(moist),
                brightness=smooth(b),
                wateringtime=smooth(wt))

def check_spill():
    if pins.spilled:
        slack('There is a spill!')

@app.route('/')
def serve_data():
    if 'stop' in request.args:
        # %Y-%m-%d
        stop = datetime(*map(int, request.args.get('stop').split('-')))
    else:
        stop = datetime.now()
    if 'start' in request.args:
        start = datetime(*map(int, request.args.get('start').split('-')))
    else:
        start = datetime.combine((datetime.now() - timedelta(days=5)).date(), time.min)
    data = read_data(start, stop)
    return render_template('moisture.html',
                           today=str(datetime.now().date()),
                           yesterday=str((datetime.now() - timedelta(days=1)).date()),
                           threedaysago=str((datetime.now() - timedelta(days=3)).date()),
                           aweekago=str((datetime.now() - timedelta(days=7)).date()),
                           watertimetext=[str(x) + ' sec.' for x in data['wateringtime']],
                           N_elements=len(data['datetime']),
                           album=list(sorted(os.listdir('static/plant_photos'), reverse=True))[:24:3],
                           **data)


############# Main
def death_handler(signal_received, frame):
    try:
        if Photo._camera and not Photo._camera.closed:
            Photo.camera.close()
    except:
        pass
    pins.cleanup()
    print('SIGINT or CTRL-C detected. Exiting gracefully')
    slack('Shutting down gracefully')
    exit(0)

if __name__ == '__main__':
    pins = Pins()
    signal(SIGINT, death_handler)
    if not os.path.exists('moisture.sqlite'):
        db.create_all()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=sense, trigger="interval", hours=1)
    scheduler.add_job(func=Photo, trigger="interval", hours=1)
    scheduler.add_job(func=check_spill, trigger="interval", minutes=1)
    scheduler.start()
    serve(app, host='0.0.0.0', port=5000)
