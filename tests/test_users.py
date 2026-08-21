import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from main import app
from database import Base, get_db

# 1. 테스트 전용 SQLite 비동기 메모리 DB 설정 (실제 MySQL을 건드리지 않고 테스트용으로 격리)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
test_async_session = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# 2. 테스트용 DB 세션을 FastAPI 의존성(get_db)에 바꿔치기하는 Fixture
@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db():
    async with test_async_session() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# 3. 비동기 HTTP 클라이언트 Fixture
@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        yield ac

@pytest.mark.anyio
async def test_signup_success(async_client: AsyncClient):
    """회원가입 성공 테스트"""
    response = await async_client.post(
        "/users/signup",
        json={
            "email": "홍승완@example.com",
            "password": "password123",  # 문자+숫자 혼합 조건 만족
            "name": "홍승완"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "홍승완@example.com"
    assert data["name"] == "홍승완"
    assert "id" in data

@pytest.mark.anyio
async def test_signup_password_condition(async_client: AsyncClient):
    """비밀번호 조건(문자만 입력) 불만족 시 회원가입 실패 테스트"""
    response = await async_client.post(
        "/users/signup",
        json={
            "email": "test@example.com",
            "password": "onlyletters",  # 숫자 누락
            "name": "테스트"
        }
    )
    assert response.status_code == 400

@pytest.mark.anyio
async def test_login_and_get_me(async_client: AsyncClient):
    """로그인 및 토큰을 이용한 내 정보 조회 테스트"""
    signup_data = {
        "email": "login@example.com",
        "password": "password123",
        "name": "로그인테스트"
    }
    # 1. 먼저 회원가입 진행
    await async_client.post("/users/signup", json=signup_data)

    # 2. 로그인 요청
    login_response = await async_client.post(
        "/users/login",
        json={
            "email": "login@example.com",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    access_token = token_data["access_token"]

    # 3. 토큰을 헤더에 담아 내 정보(/users/me) 조회
    headers = {"Authorization": f"Bearer {access_token}"}
    me_response = await async_client.get("/users/me", headers=headers)
    
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "login@example.com"