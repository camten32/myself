from database import Base
from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, func, ForeignKey
import enum



class UserRole(str, enum.Enum):
    Doctor = "doctor"
    Nurse = "nurse"
    patient = "patient"
    visitor = "visitor"
    Admin = "admin"


class User(Base):
    __tablename__ = "Users"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String(50), nullable=False)
    email: str = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password: str = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.visitor)
    is_active: bool = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    lifestyle = Column(String(255), default="입력된 정보가 없습니다.")


#예약

class ReservationStatus(str, enum.Enum):
    pending = "예약 대기"
    confirmed = "예약 확정"
    canceled = "예약 취소"

class Reservation(Base):
    __tablename__ = "Reservations"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("Users.id"), nullable=False)
    department: str = Column(String(50), nullable=False)
    symptoms: str = Column(String(50), nullable=False)
    reservation_time: DateTime = Column(DateTime(timezone=True), nullable=False)
    status: ReservationStatus = Column(Enum(ReservationStatus), nullable=False, default=ReservationStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


