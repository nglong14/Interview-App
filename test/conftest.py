import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base, get_db
from backend.config import settings
import redis

SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.database_username}:{settings.database_password}@127.0.0.1:{settings.database_port}/test_url_shortener"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

#Separate Redis database (use localhost for tests, not 'redis' from docker-compose)
test_redis = redis.Redis(
    host='localhost',  # Always use localhost for local tests
    port=settings.redis_port,
    db=15,
    decode_responses=True
)

#Before test: create all tables. After tests: drop all. Ensure fresh database schema
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Create all tables (skip drop to avoid connection issues)
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)

#Create a new session for each test function
@pytest.fixture(scope="function")
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

#Create a TestClient for making HTTP requests to FastAPI app
@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(client):
    user_data ={
        "email": "test@example.com",
        "password": "testpass123"
    }
    response = client.post("/users", json=user_data)
    assert response.status_code == 201
    return user_data

@pytest.fixture
def auth_token(client, test_user):
    response = client.post(
        "/login",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture(autouse=True)
def clear_redis():
    """Clear Redis before/after each test"""
    test_redis.flushdb()
    yield
    test_redis.flushdb()