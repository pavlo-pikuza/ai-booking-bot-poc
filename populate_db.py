from sqlalchemy.orm import Session
from database import Client, Service, Appointment, SimulationState, engine, Base, SessionLocal
import random
import os
from dotenv import load_dotenv
from utils import appoinments_gen
from datetime import datetime

load_dotenv()

WORK_HOURS_START = os.getenv("WORK_HOURS_START")
WORK_HOURS_END = int(os.getenv("WORK_HOURS_END"))
BREAK_TIME = int(os.getenv("BREAK_TIME"))
SLOT_DURATION = int(os.getenv("SLOT_DURATION"))
WORK_DAYS = os.getenv("WORK_DAYS").split(",")
GEN_APPOS_COUNT =  int(os.getenv("GEN_APPOS_COUNT"))


def populate_db():

    db: Session = SessionLocal()
    
    try:
        # 🔹 1. Add clients
        if db.query(Client).count() == 0:
            db.add_all([
                Client(name="Alice"),
                Client(name="Bob"),
                Client(name="Charlie"),
            ])
            db.commit()

        if db.query(Service).count() == 0:
            db.add_all([
                Service(name="Manicure", duration=35),
                Service(name="Pedicure", duration=40),
                Service(name="Haircut", duration=30),
            ])
            db.commit()

        
        clients = [client.id for client in db.query(Client).all()]
        services = {service.id: service.duration for service in db.query(Service).all()}

        if db.query(Appointment).count() == 0:

            res, _ = appoinments_gen(
                count=GEN_APPOS_COUNT,
                clients=clients,
                services=services,
                work_days=WORK_DAYS,
                work_hour_start=int(WORK_HOURS_START),
                work_hour_end=WORK_HOURS_END,
                break_time=BREAK_TIME
                )

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

        existing = db.get(SimulationState, 1)
        if not existing:
            default_time = datetime.strptime(WORK_HOURS_START+":00", "%H:%M").time()
            new_state = SimulationState(
                id=1,
                day=WORK_DAYS[0],
                time=default_time.strftime("%H:%M"),
                is_running=True
            )
            db.add(new_state)
            db.commit()
            print("✅ Simulation state initialized.")
        else:
            print("ℹ️ Simulation state already exists.")
        print("✅ Database populated with non-overlapping appointments!")
    except Exception as e:
        db.rollback()
        print(f"❌ DB populating error: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    populate_db()
