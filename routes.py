from flask import Flask, request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import os
from dotenv import load_dotenv
from database import Base, Appointment, Client, Service, SessionLocal
# Load environment variables
load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')

WORK_HOURS_START = int(os.getenv("WORK_HOURS_START", 0))
WORK_HOURS_END = int(os.getenv("WORK_HOURS_END", 0))
BREAK_TIME = int(os.getenv("BREAK_TIME", 0))
SLOT_DURATION = int(os.getenv("SLOT_DURATION", 0))
WORK_DAYS = os.getenv("WORK_DAYS", "").split(",")

        start_time = datetime.strptime(f"{day} {WORK_HOURS_START}:00", "%A %H:%M")
        end_time = datetime.strptime(f"{day} {WORK_HOURS_END}:00", "%A %H:%M")
        current_time = start_time
        while current_time + timedelta(minutes=SLOT_DURATION) <= end_time:
                app_end = app_start + timedelta(minutes=services.get(appointment.service_id, SLOT_DURATION))
                if not (current_time >= app_end or current_time + timedelta(minutes=SLOT_DURATION) <= app_start):
            current_time += timedelta(minutes=SLOT_DURATION + BREAK_TIME)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)