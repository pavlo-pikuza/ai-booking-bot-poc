import functools
from database import SessionLocal, Conversation, ClientSession, Appointment, SimulationState
from sqlalchemy.orm import Session, joinedload
from flask import jsonify
from datetime import datetime
import pandas as pd
import os
from dotenv import load_dotenv

from utils import shedule_plot, time_add

load_dotenv()

WORK_DAYS = os.getenv("WORK_DAYS", "").split(",")

def db_session_handler(func):
    """Decorator to handle database session management and error handling."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        db: Session = SessionLocal()
        try:
            return func(db, *args, **kwargs)
        except Exception as e:
            return jsonify({"error": "Database error","function":f"{func.__name__}", "message":f"{e}"}), 500
        finally:
            db.close()
    return wrapper



def clear_conversation_table(db):
    db.query(Conversation).delete()
    db.commit()


def release_client(db, session_id):
    db.query(ClientSession).filter_by(session_id=session_id).delete()
    db.commit()


def get_appointments_for_plot(db):
    appointments = db.query(Appointment) \
        .options(joinedload(Appointment.client), joinedload(Appointment.service)) \
        .all()
    result = [
        {
            'client': a.client.name,
            'service': a.service.name,
            'start_time': a.start_time,
            'end_time': time_add(datetime.strptime(a.start_time,"%H:%M").time(), minutes=a.service.duration).strftime("%H:%M"),
            'day': a.day,
        }
        for a in appointments
    ]
    return pd.DataFrame(result)


def get_simulation_state(db):
    state = db.query(SimulationState).filter(SimulationState.id == 1).first()
    return state.to_dict()


def advance_time(db):
    """Contain logic of current time calculations. Updates 'current_time' and schedule plot."""

    state = db.get(SimulationState, 1)
    if not state or not state.is_running:
        return
    
    current_time = datetime.strptime(state.time, "%H:%M").time()
    new_time = time_add(current_time, minutes=1)

    if new_time.hour >= 16 and new_time.minute >= 1:
        state.day = "Monday" if state.day == "Friday" else WORK_DAYS[WORK_DAYS.index(state.day) + 1]
        new_time = datetime.strptime("08:59", "%H:%M").time()

        clear_conversation_table(db)
    else:
        print(f"Current day and time: {state.day} {new_time}")
    
    state.time = new_time.strftime("%H:%M")
    db.commit()

    appos = get_appointments_for_plot(db)
    shedule_plot(appos, state.day, state.time)