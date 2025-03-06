from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import and_, create_engine
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from database import Base, Appointment, Client, Service, SessionLocal
import functools

# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

WORK_HOURS_START = int(os.getenv("WORK_HOURS_START", 0))
WORK_HOURS_END = int(os.getenv("WORK_HOURS_END", 0))
BREAK_TIME = int(os.getenv("BREAK_TIME", 0))
SLOT_DURATION = int(os.getenv("SLOT_DURATION", 0))
WORK_DAYS = os.getenv("WORK_DAYS", "").split(",")

def db_session_handler(func):
    """Decorator to handle database session management and error handling."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        db: Session = SessionLocal()
        try:
            return func(db, *args, **kwargs)
        except Exception as e:
            print(f"❌ Database error in {func.__name__}: {e}")
            return jsonify({"error": "Database error"}), 500
        finally:
            db.close()
    return wrapper

def get_available_slots(db):
    appointments = db.query(Appointment).all()
    services = {s.id: s.duration for s in db.query(Service).all()}

    slots = {}

    for day in WORK_DAYS:
        slots[day] = []
        start_time = datetime.strptime(f"{day} {WORK_HOURS_START}:00", "%A %H:%M")
        end_time = datetime.strptime(f"{day} {WORK_HOURS_END}:00", "%A %H:%M")
        current_time = start_time

        while current_time + timedelta(minutes=SLOT_DURATION) <= end_time:
            is_free = True
            for appointment in appointments:
                app_start = appointment.start_time
                app_end = app_start + timedelta(minutes=services.get(appointment.service_id, SLOT_DURATION))
                
                if not (current_time >= app_end or current_time + timedelta(minutes=SLOT_DURATION) <= app_start):
                    is_free = False
                    break

            if is_free:
                slots[day].append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=SLOT_DURATION + BREAK_TIME)
    
    return slots

# 🔹 GET /available_slots – Get all available slots
@app.route('/available_slots', methods=['GET'])
@db_session_handler
def available_slots(db):
    return jsonify(get_available_slots(db))


# 🔹 GET /clients – Get all clients
@app.route('/clients', methods=['GET'])
@db_session_handler
def get_clients(db):
    clients = db.query(Client).all()
    result = [{'id': c.id, 'name': c.name} for c in clients]
    return jsonify(result)

# 🔹 GET /services – Get all services
@app.route('/services', methods=['GET'])
@db_session_handler
def get_services(db):
    services = db.query(Service).all()
    result = [{'id': s.id, 'name': s.name, 'duration': s.duration} for s in services]
    return jsonify(result)

# 🔹 GET /appointments – List all appointments
@app.route('/appointments', methods=['GET'])
@db_session_handler
def get_appointments(db):
    appointments = db.query(Appointment).all()
    result = [
        {
            'id': a.id,
            'client_id': a.client_id,
            'client_name': db.query(Client.name).filter(Client.id == a.client_id).scalar(),
            'service_id': a.service_id,
            'service_name': db.query(Service.name).filter(Service.id == a.service_id).scalar(),
            'start_time': a.start_time.strftime('%Y-%m-%d %H:%M')
        }
        for a in appointments
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

    start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M')
    end_time = start_time + timedelta(minutes=service.duration)

    overlapping_appointments = db.query(Appointment).filter(
        and_(
            Appointment.start_time < end_time,
            (Appointment.start_time + timedelta(minutes=db.query(Service.duration).filter(Service.id == Appointment.service_id).scalar())) > start_time
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
        appointment.start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M')
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

# Запуск сервера Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
