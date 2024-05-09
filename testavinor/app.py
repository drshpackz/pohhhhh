
from flask import Flask, request, render_template, session, redirect, url_for, jsonify
from flask_session import Session
import requests
from xml.etree import ElementTree
from datetime import datetime, timedelta
import pytz
from dateutil import parser, tz
import os
from redis import Redis
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = os.urandom(24)  # Secure random key
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(host='redis-16031.c135.eu-central-1-1.ec2.redns.redis-cloud.com', port=16031, db=0, password='W7BhXAuUWFNmenf026i1wj5mFK4xS7V0')
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

Session(app)
# Add this in your app.py after setting up Redis
try:
    test_key = 'redis_test'
    app.config['SESSION_REDIS'].set(test_key, '1')
    assert app.config['SESSION_REDIS'].get(test_key) == b'1', "Redis connection failed"
    print("Redis is connected and working.")
except Exception as e:
    print("Failed to connect or verify Redis:", e)
# Redis session database

def utc_to_local(utc_dt, local_zone):
    """Convert UTC datetime string to a datetime object in a local timezone."""
    utc_dt = datetime.strptime(utc_dt, '%Y-%m-%dT%H:%M:%SZ')
    utc_zone = pytz.timezone('UTC')
    local_zone = pytz.timezone(local_zone)
    local_dt = utc_zone.localize(utc_dt).astimezone(local_zone)
    return local_dt

def get_hours_to_left(schedule_time, local_zone='Europe/Oslo'):
    """Calculate how many hours and minutes are left until the scheduled time."""
    now = datetime.now(tz.gettz(local_zone))
    schedule = parser.parse(schedule_time)
    schedule = schedule.astimezone(tz.gettz(local_zone))
    if schedule > now:
        delta = schedule - now
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        return f"{hours:02}:{minutes:02}"
    else:
        return "00:00"
    
gate_numbers = {
    "B8": 171, "B7": 172, "B6": 173, "B5": 174, "B4": 175, "B3": 176, "B2": 177, "B1": 178,
    "A2": 28, "A4": 26, "A6": 24, "A8": 22, "A10": 20, "A12": 18, "A14": 16, "A15": 15, "A16": 14,
    "A18": 13, "A19": 13, "A20": 14, "A21": 11, "A22": 12, "A23": 9, "A24": 10, "A25": 7, "A26": 2, "A27": 3,
    "D2": 60, "C2": 60, "D3": 62, "C3": 62, "D4": 64, "C4": 64, "D5": 66, "C5": 66, "D6": 68, "C6": 68,
    "D7": 70, "C7": 70, "D8": 72, "C8": 72, "D9": 74, "C9": 74, "D10": 76, "C10": 76, "D11": 81, "C11": 81,
    "E2": 36, "E3": 37, "E4": 39, "E5": 39, "E6": 40, "E7": 40, "E8": 38, "E9": 48, "E10": 40, "E11": 41,
    "E12": 42, "E13": 43, "E14": 44, "E15": 45, "E16": 46, "E17": 47, "E18": 48, "E19": 49,
    "F21": 51, "F23": 53
}

def get_flight_data(airport_code, direction, flight_type='A'):
    """Fetch flight data from an XML feed, parse it, and format for display."""
    url = f"http://flydata.avinor.no/XmlFeed.asp?TimeFrom=1&TimeTo=17&airport={airport_code}&direction={direction}&lastUpdate=2009-03-10T15:03:00Z"
    response = requests.get(url)
    active_flights = []
    archived_flights = []
    ongoing_flights = []
    excluded_airlines = ['WF', 'SK', 'LH', 'DX', 'KL', 'OS', 'SIU']

    if response.status_code == 200:
        root = ElementTree.fromstring(response.content)
        for flight in root.findall('.//flight'):
            airline = flight.find('flight_id').text[:2]
            if airline in excluded_airlines:
                continue
            dom_int = flight.find('dom_int').text if flight.find('dom_int') is not None else 'A'
            if flight_type == 'x' and dom_int not in ['I', 'S']:  # Combined International and Schengen
                continue
            elif flight_type != 'A' and flight_type != 'x' and dom_int != flight_type:
                continue

            schedule_time = flight.find('schedule_time').text
            local_schedule_time = utc_to_local(schedule_time, 'Europe/Oslo')
            schedule_day = local_schedule_time.strftime('%A')
            formatted_time = local_schedule_time.strftime('%H:%M')
            hours_to_left = get_hours_to_left(schedule_time)

            flight_id = flight.find('flight_id').text
            received_bags = session.get(flight_id, 0)
            status_code = flight.find('status').get('code') if flight.find('status') is not None else 'Scheduled'
            
            if hours_to_left == '00:00':
                status_code = 'Time Out'

            gate = flight.find('gate').text if flight.find('gate') is not None else 'N/A'
            gate_number = gate_numbers.get(gate, 'N/A')

            flight_data = {
                'flight_id': flight_id,
                'dom_int': dom_int,
                'schedule_day': schedule_day,
                'schedule_time': formatted_time,
                'hours_to_left': hours_to_left,
                'arr_dep': flight.find('arr_dep').text,
                'airport': flight.find('airport').text,
                'gate': gate,
                'gate_number': gate_number,
                'status': status_code,
                'status_time': flight.find('status').get('time') if flight.find('status') is not None else 'No update',
                'received_bags': received_bags
            }

            if received_bags >= 1:
                ongoing_flights.append(flight_data)
            elif status_code == 'Time Out' and received_bags == 0:
                archived_flights.append(flight_data)
            else:
                active_flights.append(flight_data)

    return {'active': active_flights, 'archived': archived_flights, 'ongoing': ongoing_flights}


# Archive 
@app.route('/archive')
def archive():
    return render_template('archive.html')
# Parking Functions 

@app.route('/park_baggage/<flight_id>', methods=['POST'])
def park_baggage(flight_id):
    current_gate = request.form.get('current_gate')
    parked_gate = session.get(f'{flight_id}_parked_gate')
    parked_time = session.get(f'{flight_id}_parked_time')
    parked_time_formatted = session.get(f'{flight_id}_parked_time_formatted')  # Retrieve the formatted parked time from session

    # Set the parked visibility flag to true
    session[f'{flight_id}_parked_visible'] = True

    if parked_gate and parked_gate != current_gate:
        response = {
            "status": "error",
            "message": f"GATE IS CHANGED! Previously parked at Gate {parked_gate}, now at Gate {current_gate}.",
            "parked_at": parked_time_formatted,  # Use the formatted parked time from session
            "current_gate": current_gate,
            "previous_gate": parked_gate
        }
    else:
        # Update the parked gate and time
        session[f'{flight_id}_parked_gate'] = current_gate
        session[f'{flight_id}_parked_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Format the parked time if not already formatted and store it in the session
        if not parked_time_formatted:
            parked_time_formatted = datetime.strptime(session[f'{flight_id}_parked_time'], "%Y-%m-%d %H:%M:%S").strftime("%d | %H:%M")
            session[f'{flight_id}_parked_time_formatted'] = parked_time_formatted

        session.modified = True  # Ensure session changes are saved

        response = {
            "status": "success",
            "message": "Baggage parked successfully.",
            "parked_at": parked_time_formatted,
            "gate": current_gate
        }

    return jsonify(response)




@app.route('/update_parking_visibility/<flight_id>', methods=['POST'])
def update_parking_visibility(flight_id):
    visible = request.form.get('visible') == 'true'
    session[f'{flight_id}_parked_visible'] = visible
    session.modified = True
    return jsonify({'status': 'success', 'visible': visible})

@app.route('/test')
def test():
    return render_template('test.html')


@app.route('/park_gate/<flight_id>', methods=['POST'])
def park_gate(flight_id):
    # Logic to park a gate or fetch last parked gate
    return jsonify({"success": True, "message": "Gate parked successfully for " + flight_id})


@app.route('/')
def home():
    airport_code = request.args.get('airport', 'OSL')
    direction = request.args.get('direction', 'D')
    flight_type = request.args.get('flight_type', 'A')  # Get flight type from query parameters
    flights = get_flight_data(airport_code, direction, flight_type)
    return render_template('flights.html', flights=flights)

# Baggage Handling COUNT and DEVLERIED 
@app.route('/baggage_arrived', methods=['POST'])
def baggage_arrived():
    flight_id = request.form.get('flightId')
    if flight_id:
        session[flight_id] = session.get(flight_id, 0) + 1
        session.modified = True
        print("Updated baggage count for flight:", flight_id, session[flight_id])  # Debug statement
        return jsonify({"status": "success", "message": "Baggage count updated", "count": session[flight_id]})
    return jsonify({"status": "error", "message": "No Flight ID provided"}), 400

@app.route('/baggage_delivered', methods=['POST'])
def baggage_delivered():
    flight_id = request.form.get('flightId')
    if flight_id:
        delivered_key = 'delivered_' + flight_id
        session[delivered_key] = session.get(delivered_key, 0) + session.get(flight_id, 0)
        session[flight_id] = 0  # Reset the count for new bags
        session.modified = True
        print("Delivered and reset baggage count for flight:", flight_id)  # Debug statement
        return jsonify({
            "status": "success",
            "message": "Delivery count updated",
            "delivered_count": session[delivered_key],
            "new_count": session[flight_id]
        }), 200
    return jsonify({"status": "error", "message": "No Flight ID provided"}), 400



if __name__ == '__main__':
    app.run(debug=True, host='192.168.10.175', port=8080)
