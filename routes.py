from flask import Flask, request, jsonify, render_template
from sqlalchemy import and_, case
from datetime import datetime
import os
from dotenv import load_dotenv
from database import Base, Appointment, Client, Service, Conversation, SimulationState
import threading

from utils import shedule_plot, time_add
from db_functions import db_session_handler, get_appointments_for_plot, get_simulation_state

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

WORK_HOURS_START = int(os.getenv("WORK_HOURS_START", 0))
WORK_HOURS_END = int(os.getenv("WORK_HOURS_END", 0))
BREAK_TIME = int(os.getenv("BREAK_TIME", 0))
SLOT_DURATION = int(os.getenv("SLOT_DURATION", 0))
WORK_DAYS = os.getenv("WORK_DAYS", "").split(",")

time_lock = threading.Lock()



@app.route('/')
@db_session_handler
def index(db):
    appos = get_appointments_for_plot(db)
    state = get_simulation_state(db)
    print(state['is_running'])
    shedule_plot(appos, state['day'], datetime.strptime(state['time'], "%H:%M").time())
    return render_template('index.html')


@app.route("/time", methods=["GET"])
@db_session_handler
def get_time(db):
    res = jsonify(get_simulation_state(db))
    return res


@app.route("/time", methods=["POST"])
@db_session_handler
def set_time(db):
    data = request.get_json()
    print(data)

    if not data:
        return jsonify({"error": "No data received"}), 400

    if data.get("action") == "toggle":
        state = db.get(SimulationState, 1)
        if state:
            state.is_running = not state.is_running
            db.commit()
            return jsonify({
                "success": True,
                "is_running": state.is_running
            }), 200

    elif data.get("action") == "set":
        try:
            new_time = data.get("time")
            new_day = data.get("day")
            if not new_time:
                return jsonify({"error": "No time provided"}), 400

            new_hour, new_minute = map(int, new_time.split(":"))

            if new_day not in WORK_DAYS:
                return jsonify({"error": "Invalid day"}), 400

            if new_hour < 9 or new_hour > 15:
                return jsonify({"error": "Invalid hour"}), 400

            state = db.get(SimulationState, 1)
            if not state:
                return jsonify({"error": "Simulation state not found"}), 404

            state.time = datetime.strftime(datetime.strptime(f"{new_hour}:{new_minute}", "%H:%M"), "%H:%M")
            state.day = new_day

            db.commit()

            return jsonify({"success": True,
                            "day": state.day,
                            "time": state.time,
                            "is_running": state.is_running})

        except Exception as e:
            return jsonify({"error": "Invalid time format", "message": str(e)}), 400
    

@app.route('/clients', methods=['GET'])
@db_session_handler
def get_clients(db):
    clients = db.query(Client).all()
    result = [{'id': c.id, 'name': c.name} for c in clients]
    return jsonify(result)


@app.route('/services', methods=['GET'])
@db_session_handler
def get_services(db):
    services = db.query(Service).all()
    result = [{'id': s.id, 'name': s.name, 'duration': s.duration} for s in services]
    return jsonify(result)


@app.route('/available_slots', methods=['GET'])
@db_session_handler
def available_slots(db):
    return jsonify(get_available_slots(db))

@app.route('/appointments', methods=['GET'])
@db_session_handler
def get_all_appointments(db):
    appointments = db.query(Appointment).all()
    result = [
        {
            'id': a.id,
            'client_id': a.client_id,
            'service_id': a.service_id,
            'start_time': a.start_time,
            'day': a.day
        }
        for a in appointments
    ]
    return jsonify(result)

@app.route('/send_message', methods=['POST'])
@db_session_handler
def send_message(db):
    global simulation_time, simulation_day

    data = request.json
    client_id = data.get("client_id")
    message = data.get("message")
    is_client_sender = data.get("is_client_sender")

    print(f"client_id: {client_id} message: {message} data: {data} simul_day: {simulation_day} simul_time: {simulation_time}")

    if not client_id or not message:
        return jsonify({"error": "Missing client_id or message"}), 400

    chat_message = Conversation(
        client_id=client_id,
        message=message,
        time = simulation_time.strftime('%H:%M'),
        day = simulation_day,
        is_client_sender = is_client_sender
    )
    
    db.add(chat_message)
    db.commit()
    db.refresh(chat_message)

    return jsonify({
        "id": chat_message.id,
        "client_id": chat_message.client_id,
        "message": chat_message.message,
        "day": chat_message.day,
        "time": chat_message.time
    })

@app.route('/chat_history/<int:client_id>', methods=['GET'])
@db_session_handler
def get_chat_history(db, client_id):
    """Get chat history for target client"""

    day_order = case(
        (Conversation.day == 'Sunday', 0),
        (Conversation.day == 'Monday', 1),
        (Conversation.day == 'Tuesday', 2),
        (Conversation.day == 'Wednesday', 3),
        (Conversation.day == 'Thursday', 4),
        (Conversation.day == 'Friday', 5),
        (Conversation.day == 'Saturday', 6),
    )

    messages = db.query(Conversation).filter_by(client_id=client_id).order_by(day_order, Conversation.time).all()

    result = [
        {
            "id": msg.id,
            "message": msg.message,
            "is_client_sender": msg.is_client_sender,
            "time": msg.time,
            "day": msg.day
        }
        for msg in messages
    ]
    return jsonify(result)





# 🔹 POST /appointments – Add new appointment
@app.route('/appointments', methods=['POST'])
@db_session_handler
def add_appointment(db):
    data = request.get_json()

    if 'client_id' not in data or 'service_id' not in data or 'start_time' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    client = db.query(Client).filter(Client.id == data['client_id']).first()
    service = db.query(Service).filter(Service.id == data['service_id']).first()
    if not client or not service:
        return jsonify({'error': 'Client or service not found'}), 404

    start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    end_time = time_add(start_time, minutes=service.duration)

    overlapping_appointments = db.query(Appointment).filter(
        and_(
            datetime.strptime(Appointment.start_time, '%H:%M').time() < end_time,
            time_add(
                datetime.strptime(Appointment.start_time, '%H:%M').time(),
                minutes=db.query(Service.duration).filter(Service.id == Appointment.service_id).scalar()) > start_time
        )
    ).count()

    if overlapping_appointments > 0:
        return jsonify({'error': 'Appointment time conflicts with an existing one'}), 409

    new_appointment = Appointment(
        client_id=data['client_id'],
        service_id=data['service_id'],
        start_time=start_time
    )

    db.add(new_appointment)
    db.commit()

    return jsonify({'message': 'Appointment added successfully'}), 201

# 🔹 PUT /appointments/{id} – appointment reshedule
@app.route('/appointments/<int:appointment_id>', methods=['PUT'])
@db_session_handler
def reschedule_appointment(db, appointment_id):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    data = request.get_json()
    if 'start_time' in data:
        appointment.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        db.commit()
        return jsonify({'message': 'Appointment rescheduled successfully'}), 200
    
    return jsonify({'error': 'Invalid request'}), 400

# 🔹 DELETE /appointments/{id} – Cancel appointment
@app.route('/appointments/<int:appointment_id>', methods=['DELETE'])
@db_session_handler
def delete_appointment(db, appointment_id):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404

    db.delete(appointment)
    db.commit()
    
    return jsonify({'message': 'Appointment deleted successfully'}), 200

def get_available_slots(db):
    appointments = db.query(Appointment).all()
    services = {s.id: s.duration for s in db.query(Service).all()}

    slots = {}

    for day in WORK_DAYS:
        slots[day] = []
        start_time = datetime.strptime(f"{WORK_HOURS_START}:00", "%H:%M").time()
        end_time = datetime.strptime(f"{WORK_HOURS_END}:00", "%H:%M").time()
        current_time = start_time

        while time_add(current_time, minutes=SLOT_DURATION) <= end_time:
            is_free = True
            for appointment in appointments:
                app_start = appointment.start_time
                app_end =  + time_add(app_start, minutes=services.get(appointment.service_id, SLOT_DURATION))
                
                if not (current_time >= app_end or time_add(current_time, minutes=SLOT_DURATION) <= app_start):
                    is_free = False
                    break

            if is_free:
                slots[day].append(current_time.strftime("%H:%M"))
            current_time = time_add(current_time, minutes=SLOT_DURATION + BREAK_TIME)
    
    return slots