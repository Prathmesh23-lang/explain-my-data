from sqlalchemy import Column, String, Integer, ForeignKey, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from datetime import datetime
from database import Base   # ✅ IMPORTANT FIX

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filename = Column(Text)
    file_path = Column(Text)
    row_count = Column(Integer)
    col_count = Column(Integer)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    profile_json = Column(JSONB)
    charts_json = Column(JSONB)
    insights_json = Column(JSONB)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id"))
    role = Column(Text)
    message = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)