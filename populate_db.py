from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import Base, SessionLocal, Client, Service, Appointment, engine
import random
import os
from dotenv import load_dotenv
from utils import appoinments_gen

load_dotenv()

WORK_HOURS_START = int(os.getenv("WORK_HOURS_START", 9))
WORK_HOURS_END = int(os.getenv("WORK_HOURS_END", 16))
BREAK_TIME = int(os.getenv("BREAK_TIME", 10))
SLOT_DURATION = int(os.getenv("SLOT_DURATION", 50))
WORK_DAYS = os.getenv("WORK_DAYS", "").split(",")
GEN_APPOS_COUNT = 25

DB_FILE  = os.getenv("DATABASE_URL", "").replace("sqlite:///", "")


def initialize_database():
    # Remove old database file if it exists

    print(DB_FILE)
    if not os.path.exists(DB_FILE):
        print("🆕 Creating new database...")

        # Создаём новую базу данных
        Base.metadata.create_all(bind=engine)
        db: Session = SessionLocal()
    # 🔹 1. Add clients
    db.add_all([
        Client(name="Alice"),
        Client(name="Bob"),
        Client(name="Charlie"),
    ])
    db.commit()

    # Retrieve client IDs
    clients = [client.id for client in db.query(Client).all()]

    # 🔹 2. Add services
    db.add_all([
        Service(name="Manicure", duration=35),
        Service(name="Pedicure", duration=40),
        Service(name="Haircut", duration=30),
    ])
    db.commit()

    # Retrieve service IDs
    services = {service.id: service.duration for service in db.query(Service).all()}

    # 🔹 3. Generate non-overlapping appointments for 5 working days
    res, appointments = appoinments_gen(
        count=GEN_APPOS_COUNT,
        clients=clients,
        services=services,
        work_days=WORK_DAYS,
        work_hour_start=WORK_HOURS_START,
        work_hour_end=WORK_HOURS_END,
        break_time=BREAK_TIME
        )

    # 🔹 4. Insert all appointments into the database

    appointments_alch = [
        Appointment(
            client_id=appo["client_id"],
            service_id=appo["service_id"],
            start_time=appo["start_time"],
            day = appo['day']
        ) for appo in res
    ]
    db.add_all(appointments_alch)
    db.commit()
    db.close()

    print("✅ Database populated with non-overlapping appointments!")


initialize_database()