"""SQLAlchemy models for agent results and experiment configs."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import String, Text, Float, Integer, DateTime, JSON, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """SQLAlchemy base class."""

    pass


class AgentResultDB(Base):
    """SQLAlchemy model for agent results."""

    __tablename__ = "agent_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    agent_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_type: Mapped[str] = mapped_column(String, nullable=False)  # rd-agent, adk-ralph
    phase: Mapped[str] = mapped_column(String, nullable=False, index=True)
    question_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # running, success, failed
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    artifacts: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "phase": self.phase,
            "question_id": self.question_id,
            "status": self.status,
            "output": self.output,
            "artifacts": self.artifacts,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ExperimentConfigDB(Base):
    """SQLAlchemy model for experiment configurations."""

    __tablename__ = "experiment_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    question_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    config: Mapped[str] = mapped_column(Text, nullable=False)  # YAML/JSON config
    schema_file: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    results: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "question_id": self.question_id,
            "config": self.config,
            "schema_file": self.schema_file,
            "status": self.status,
            "results": self.results,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TestCaseDB(Base):
    """SQLAlchemy model for test cases."""

    __tablename__ = "test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    question_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    test_file: Mapped[str] = mapped_column(Text, nullable=False)
    solution_file: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agent_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # YAML
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "test_id": self.test_id,
            "question_id": self.question_id,
            "test_file": self.test_file,
            "solution_file": self.solution_file,
            "agent_config": self.agent_config,
            "status": self.status,
            "score": self.score,
            "feedback": self.feedback,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Pydantic models for API
class AgentResult(BaseModel):
    """Pydantic model for agent results."""

    run_id: str
    agent_id: str
    agent_type: str
    phase: str
    question_id: Optional[str] = None
    status: str
    output: Optional[dict] = None
    artifacts: list[str] = []
    error: Optional[str] = None


class ExperimentConfig(BaseModel):
    """Pydantic model for experiment config."""

    experiment_id: str
    question_id: str
    config: dict
    schema_file: Optional[str] = None
    status: str = "pending"
    results: Optional[dict] = None


class TestCase(BaseModel):
    """Pydantic model for test case."""

    test_id: str
    question_id: str
    test_file: str
    solution_file: Optional[str] = None
    agent_config: Optional[dict] = None
    status: str = "pending"
    score: Optional[float] = None
    feedback: Optional[str] = None
