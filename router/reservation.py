from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials   
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Reservation, ReservationStatus, User
from schemas import ReservationCreate, ReservationResponse, UserResponse
from database import get_db
from core.auth import decode_access_token, get_current_user


router = APIRouter(
    prefix="/reservations",
    tags=["reservations"]
)

security = HTTPBearer()

@router.post(
    "/",
    summary="진료 예약",
    status_code=status.HTTP_201_CREATED,
    response_model=ReservationResponse
)
async def create_reservation(
    body: ReservationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    db_reservation = Reservation(
        user_id=current_user.id,
        department=body.department,
        symptoms=body.symptoms,
        reservation_time=body.reservation_time,
        status=ReservationStatus.pending
    )

    db.add(db_reservation)
    await db.commit()
    await db.refresh(db_reservation)

    return db_reservation



@router.get(
    "/get",
    summary="예약 조회",
    status_code=status.HTTP_200_OK,
    response_model=list[ReservationResponse]
)
async def get_reservation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    reservation_result = await db.execute(
        select(Reservation).where(Reservation.user_id == current_user.id)
    )

    reservations = reservation_result.scalars().all()

    return reservations