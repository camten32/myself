from fastapi import APIRouter, FastAPI, Depends, status, HTTPException
from database import get_db
from schemas import UserCreate, UserResponse, UserLogin, Token, UserRoleUpdate, UserRole
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import User, UserRole
from core.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user,
    decode_access_token,
    check_user_role
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post(
        "/signup",
        summary="회원가입",
        status_code=status.HTTP_201_CREATED,
        response_model=UserResponse
)
async def signup(
    body: UserCreate,
    db: AsyncSession = Depends(get_db)
):

    existing_user_result = await db.execute(
        select(User).where(User.email == body.email)
    )

    existing_user = existing_user_result.scalar()

    if existing_user:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "이미 존재하는 이메일입니다."
        )

    if len(body.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 최소 6자 이상이어야 합니다."
        )

    if body.password.isdigit() or body.password.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호는 숫자와 문자를 혼합하여 사용해야 합니다."
        )

    secure_password = get_password_hash(body.password)

    db_user = User(
        email=body.email,
        hashed_password=secure_password,
        name=body.name,
        role=UserRole.visitor
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.post(
    "/login",
    summary="로그인",
    status_code=status.HTTP_200_OK,
    response_model=Token
)
async def Login(
        body: UserLogin,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.email == body.email)
    )
    db_user = result.scalar()

    if not db_user or not verify_password(body.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 잘못되었습니다."
        )

    access_token = create_access_token(
        data={"sub": db_user.email, 
        "role": db_user.role}
    )

    return {"access_token": access_token, "token_type": "bearer"}

security = HTTPBearer()

@router.get(
    "/me",
    summary="내 정보 조회",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse
)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete(
    "/delete",
    summary="회원 탈퇴",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials
    email = decode_access_token(token)

    result = await db.execute(
        select(User).where(User.email == email)
    )
    db_user = result.scalar()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    await db.delete(db_user)
    await db.commit()

    return {"message": "회원탈퇴 성공했습니다."}


allow_admin_only = check_user_role([UserRole.Admin])

@router.patch("/role", summary="사용자 권한 변경(관리자용)")
async def update_user_role(
    body: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(allow_admin_only)
):
    result = await db.execute(select(User).where(User.email == body.email))
    target_user = result.scalar()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 사용자를 찾을 수 없습니다."
        )

    target_user.role = body.new_role
    db.add(target_user)
    await db.commit()
    await db.refresh(target_user)

    return{
        "message": f"성공적으로 변경했습니다.",
        "email": target_user.email,
        "update_role": target_user.role
    }


@router.patch("/lifestyle")
async def update_life_style(
    new_lifestyle: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.lifestyle = new_lifestyle
    await db.commit()
    return {"message": "생활습관이 저장되었습니다.", "lifestyle": current_user.lifestyle}