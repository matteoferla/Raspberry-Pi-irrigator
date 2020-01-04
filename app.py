from core import app # Flask app is initiated but without Models
from models import db, engine, Measurement # Models initiated.
from sensor import Pins #reads pins

from waitress import serve
import os, json
from time import sleep #avoid clash with datetime.time
from apscheduler.schedulers.background import BackgroundScheduler
from flask import render_template, request
from datetime import datetime, timedelta, time
#from scipy.signal import savgol_filter

###############  Scheduler
pins = Pins()

def sense():
    datum = Measurement(date=datetime.now(),
                        temperature = pins.temperature,
                        humidity = pins.humidity,
                        moisture = pins.moisture,
                        brightness = pins.brightness)
    while pins.moisture < 1:
        pins.engage_pump(secs=5)
        datum.wateringtime += 5
        sleep(5)
    db.session.add(datum)


############ View

def read_data(start, stop):
    dt = []
    temp = []
    hum = []
    b = []
    wt = []
    for m in Measurement.query.filter(Measurement.datetime > start) \
            .filter(Measurement.datetime < stop).all():  # Measurement.query.all():
        temp.append(m.temperature)
        dt.append(m.datetime)
        hum.append(m.humidity)
        b.append(m.brightness)
        wt.append(m.wateringtime)
    # smooth = lambda a: savgol_filter(a, 31, 3).tolist()
    smooth = lambda a: a
    return dict(datetime=json.dumps([d.strftime('%Y-%m-%d %H:%M:%S') for d in dt]),
                temperature=smooth(temp),
                humidity=smooth(hum),
                brightness=smooth(b),
                wateringtime=smooth(wt))


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
    return render_template('moisture.html', **data)

############# Main

if __name__ == '__main__':
    if not os.path.exists('moisture.sqlite'):
        db.create_all()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=sense, trigger="interval", hours=1)
    scheduler.start()
    serve(app, host='0.0.0.0', port=8000)
