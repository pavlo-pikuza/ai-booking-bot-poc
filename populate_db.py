from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, Client, Service, Appointment
import random

# Open a database session
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
    Service(name="Manicure", duration=45),
    Service(name="Pedicure", duration=60),
    Service(name="Haircut", duration=30),
]

db.add_all(services)
db.commit()

# Retrieve service IDs
service_dict = {service.name: service.id for service in db.query(Service).all()}

# 🔹 3. Generate appointments for the next 7 days
start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # Start at 9:00 AM
appointments = []

for client_name, client_id in client_dict.items():
    for day_offset in range(5):  # Generate for one week
        day_start = start_date + timedelta(days=day_offset)  # Start of the day
        current_time = day_start  # Start time for appointments

        # Assign 3-4 appointments per day per client
        for _ in range(3):
            service_name, service_id = random.choice(list(service_dict.items()))  # Randomly select a service
            
            appointments.append(
                Appointment(client_id=client_id, service_id=service_id, start_time=current_time)
            )
            
            # Add a 10-minute gap before the next appointment
            current_time += timedelta(minutes=services[service_id - 1].duration + 10)

# 🔹 4. Insert all appointments into the database
db.add_all(appointments)
db.commit()
db.close()

print("✅ Database populated: clients, services, and appointments scheduled for one week!")