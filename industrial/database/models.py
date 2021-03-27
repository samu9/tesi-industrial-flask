import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship

from industrial.database.db import Base
from industrial.constants import MACHINE_STOP


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    role = Column(String(100))
    phone = Column(String(30))
    img_url = Column(String(300))
    log = relationship("MachineLog", back_populates="user")
    instruction = relationship("Instruction", back_populates="user")

class Area(Base):
    __tablename__ = "area"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    sectors = relationship("Sector", back_populates="area", uselist=True)


class Sector(Base):
    __tablename__ = "sector"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    area_id = Column(Integer, ForeignKey("area.id"), nullable=False)
    area = relationship("Area", back_populates="sectors")
    machines = relationship("Machine", back_populates="sector", uselist=True)


class Machine(Base):
    __tablename__ = "machine"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    m_type = Column(String(20), nullable=True, default="")
    description = Column(Text)
    sector_id = Column(Integer, ForeignKey("sector.id"), nullable=False)
    sector = relationship("Sector", back_populates="machines")
    data = relationship("MachineData", back_populates="machine")
    log = relationship("MachineLog", back_populates="machine")
    started = Column(Boolean, default=False, nullable=False)
    status = Column(String(5), default=MACHINE_STOP, nullable=False)

class MachineData(Base):
    __tablename__ = "machineData"

    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machine.id"), nullable=False)
    machine = relationship("Machine", back_populates="data")
    value1 = Column(Integer, nullable=False, default=0)
    value2 = Column(Integer, nullable=False, default=0)
    value3 = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, nullable=False)

class MachineLog(Base):
    __tablename__ = "machineLog"

    id = Column(Integer, primary_key=True)
    machine_id = Column(Integer, ForeignKey("machine.id"), nullable=False)
    machine = relationship("Machine", back_populates="log")
    action = Column(String(30))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="log")
    timestamp = Column(DateTime, nullable=False)