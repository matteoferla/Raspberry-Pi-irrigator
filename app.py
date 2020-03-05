from core import app  # Flask app is initiated but without Models
from models import db, Measurement  # Models initiated.
from scheduled import Schedule

from waitress import serve
import os, json
from flask import render_template, request, Response
from datetime import datetime, timedelta, time


############ View

def read_data(start, stop):
    dt = []
    temp = []
    hum = []
    b = []
    wtA = []
    wtB = []
    moistA = []
    moistB = []
    for m in Measurement.query.filter(Measurement.datetime > start) \
            .filter(Measurement.datetime < stop).all():  # Measurement.query.all():
        temp.append(m.temperature)
        dt.append(m.datetime)
        hum.append(m.humidity)
        b.append(m.brightness)
        wtA.append(m.wateringtime_A)
        moistA.append(m.soil_A_moisture)
        wtB.append(m.wateringtime_B)
        moistB.append(m.soil_B_moisture)
    # smooth = lambda a: savgol_filter(a, 31, 3).tolist()
    smooth = lambda a: a
    return dict(datetime=json.dumps([d.strftime('%Y-%m-%d %H:%M:%S') for d in dt]),
                temperature=smooth(temp),
                humidity=smooth(hum),
                soil_A_moisture=smooth(moistA),
                soil_B_moisture=smooth(moistB),
                brightness=smooth(b),
                wateringtime_A=smooth(wtA),
                wateringtime_B=smooth(wtB))

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
                           #watertimetext_A=[str(x) + ' sec.' for x in data['wateringtime_A']],
                           #watertimetext_B=[str(x) + ' sec.' for x in data['wateringtime_B']],
                           N_elements=len(data['datetime']),
                           album=list(sorted(os.listdir('static/plant_photos'), reverse=True))[:24:3],
                           **data)

@app.route('/trigger')
def sense_route():
    if 'mode' in request.args:
        mode = request.args.get('mode')
    else:
        mode = 'all'
    if 'key' not in request.args:
        return Response(status=401)
    elif request.args.get('key') != os.environ['IRRIGATOR_KEY']:
        return Response(status=401)
    if mode == 'all':
        schedule.check_tank()
        schedule.check_spill()
        schedule.sense()
        schedule.photo()
    elif mode == 'photo':
        schedule.photo()
    elif mode == 'measure':
        schedule.sense()
    elif mode == 'tank':
        schedule.check_tank()
    elif mode == 'water':
        schedule.pins.engage_pump(number=request.args.get('pump'), secs=10)
    else:
        pass
    return 'OK'


############# Main
if __name__ == '__main__':
    schedule = Schedule()
    if not os.path.exists('moisture.sqlite'):
        db.create_all()
    serve(app, host='0.0.0.0', port=5000)
