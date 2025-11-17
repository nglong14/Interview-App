from .database import Base
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Enum, DateTime
from sqlalchemy.sql.sqltypes import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

class User(Base):
    __tablename__="users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    interviews = relationship("Interview", back_populates="user", cascade="all, delete-orphan")


class InterviewType(str, enum.Enum):
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    ONSITE = "onsite"
    FINAL = "final"
    HR = "hr" 

class Interview(Base):
    __tablename__="interview"
    id = Column(Integer, primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    # Use String column instead of Enum to avoid database enum type mismatches
    # Pydantic validation in schemas.py ensures values are valid InterviewType
    interview_type = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    notes = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="interviews")
    questions = relationship("Question", back_populates="interview", cascade="all, delete-orphan")

class QuestionType(str, enum.Enum):
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    CODING = "coding"
    ALGORITHM = "algorithm"
    DATABASE = "database"
    GENERAL = "general"

class Difficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Question(Base):
    __tablename__="questions"
    id = Column(Integer, primary_key=True, nullable=False)
    interview_id = Column(Integer, ForeignKey("interview.id"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    interview = relationship("Interview", back_populates="questions")
