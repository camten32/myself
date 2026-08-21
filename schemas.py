from pydantic import BaseModel, EmailStr, Field, ConfigDict
from models import UserRole, ReservationStatus
from datetime import datetime



class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="이메일을 입력하세요.")
    password: str = Field(..., min_length=6, max_length=72, description="6자 이상 비밀번호를 입력하세요.")
    name: str = Field(..., description="이름을 입력하세요.")


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    is_active: bool
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="이메일을 입력하세요.")
    password: str = Field(..., description="비밀번호를 입력하세요.")

class Token(BaseModel):
    access_token: str
    token_type: str


class ReservationCreate(BaseModel):
    department: str = Field(..., description="진료과를 입력하세요.")
    symptoms: str = Field(..., description="증상을 입력하세요.")
    reservation_time: datetime = Field(..., description="예약 시간을 입력하세요.")


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    department: str
    symptoms: str
    reservation_time: datetime
    status: ReservationStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    email: EmailStr
    new_role: UserRole