from sqlalchemy import Column, Integer, String, DateTime, create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session, relationship, configure_mappers
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

configure_mappers()

# Database configuration
Base = declarative_base()

# Client model
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    appointments = relationship("Appointment", back_populates="client")

# Service model
class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    duration = Column(Integer)  # Duration in minutes
    appointments = relationship("Appointment", back_populates="service")

# Appointment model
class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    start_time = Column(DateTime)
    day = Column(String)

    client = relationship("Client", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")

# Conversation model
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer)
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    print("🛠  Creating tables in the database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For run from terminal
if __name__ == "__main__":
    init_db()