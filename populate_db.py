from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import Base, SessionLocal, Client, Service, Appointment, engine
import random
import os
from dotenv import load_dotenv

load_dotenv()

WORK_HOURS_START = int(os.getenv("WORK_HOURS_START", 9))
WORK_HOURS_END = int(os.getenv("WORK_HOURS_END", 16))
BREAK_TIME = int(os.getenv("BREAK_TIME", 10))
SLOT_DURATION = int(os.getenv("SLOT_DURATION", 50))
WORK_DAYS = os.getenv("WORK_DAYS", "").split(",")

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
    clients = [
        Client(name="Alice"),
        Client(name="Bob"),
        Client(name="Charlie"),
    ]

    db.add_all(clients)
    db.commit()

    # Retrieve client IDs
    client_dict = {client.name: client.id for client in db.query(Client).all()}

    # 🔹 2. Add services
    services = [
        Service(name="Manicure", duration=35),
        Service(name="Pedicure", duration=40),
        Service(name="Haircut", duration=30),
    ]

    db.add_all(services)
    db.commit()

    # Retrieve service IDs
    service_dict = {service.name: service.id for service in db.query(Service).all()}

    # 🔹 3. Generate non-overlapping appointments for 5 working days
    start_date = datetime.now().replace(hour=WORK_HOURS_START, minute=0, second=0, microsecond=0)
    appointments = []

    print("📌 Generating non-overlapping appointments...")

    for day_offset in range(len(WORK_DAYS)):
        day_start = start_date + timedelta(days=day_offset)
        current_time = day_start

        booked_times = []  # Store already booked time slots

        while current_time.hour < WORK_HOURS_END:  # Ensure within working hours
            service_name, service_id = random.choice(list(service_dict.items()))  # Select a random service
            service_duration = next(s.duration for s in services if s.id == service_id)

            # Check if the time slot is available
            if not any(start <= current_time < end for start, end in booked_times):
                client_name, client_id = random.choice(list(client_dict.items()))  # Select a random client
                appointments.append(
                    Appointment(client_id=client_id, service_id=service_id, start_time=current_time)
                )

                # Mark the time slot as booked (including a 10-minute break)
                booked_times.append((current_time, current_time + timedelta(minutes=service_duration + BREAK_TIME)))
                current_time += timedelta(minutes=service_duration + BREAK_TIME)
            else:
                current_time += timedelta(minutes=BREAK_TIME)  # Skip 10 minutes if the slot is occupied

    # 🔹 4. Insert all appointments into the database
    db.add_all(appointments)
    db.commit()
    db.close()

    print("✅ Database populated with non-overlapping appointments!")


initialize_database()