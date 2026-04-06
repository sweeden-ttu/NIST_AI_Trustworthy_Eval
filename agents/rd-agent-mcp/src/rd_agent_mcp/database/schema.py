"""Database schema and initialization."""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from rd_agent_mcp.database.models import Base, AgentResultDB, ExperimentConfigDB, TestCaseDB


def get_database_url(path: str = "./research.db") -> str:
    """Get database URL from path."""
    if path.startswith("sqlite"):
        return path
    return f"sqlite:///{path}"


def init_db(db_path: str = "./research.db") -> sessionmaker:
    """Initialize the database and return a session factory."""
    engine = create_engine(
        get_database_url(db_path),
        echo=False,
        connect_args={"check_same_thread": False} if "sqlite" in db_path else {},
    )
    Base.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session(db_path: str = "./research.db") -> Generator[Session, None, None]:
    """Get a database session."""
    engine = init_db(db_path)
    session = engine()
    try:
        yield session
    finally:
        session.close()


class DatabaseManager:
    """Manager for database operations."""

    def __init__(self, db_path: str = "./research.db"):
        self.engine = create_engine(
            get_database_url(db_path),
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in db_path else {},
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_session(self) -> Session:
        """Get a new session."""
        return self.Session()

    def create_agent_result(
        self,
        run_id: str,
        agent_id: str,
        agent_type: str,
        phase: str,
        question_id: str = None,
    ) -> AgentResultDB:
        """Create a new agent result."""
        session = self.get_session()
        try:
            result = AgentResultDB(
                run_id=run_id,
                agent_id=agent_id,
                agent_type=agent_type,
                phase=phase,
                question_id=question_id,
                status="running",
            )
            session.add(result)
            session.commit()
            session.refresh(result)
            return result
        finally:
            session.close()

    def update_agent_result(
        self,
        result_id: int,
        status: str,
        output: dict = None,
        artifacts: list = None,
        error: str = None,
    ):
        """Update an agent result."""
        from datetime import datetime
        import json

        session = self.get_session()
        try:
            result = session.query(AgentResultDB).filter_by(id=result_id).first()
            if result:
                result.status = status
                result.output = json.dumps(output) if output else None
                result.artifacts = json.dumps(artifacts) if artifacts else None
                result.error = error
                if status in ("success", "failed"):
                    result.completed_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def get_agent_results(self, run_id: str = None, phase: str = None) -> list[dict]:
        """Get agent results."""
        session = self.get_session()
        try:
            query = session.query(AgentResultDB)
            if run_id:
                query = query.filter_by(run_id=run_id)
            if phase:
                query = query.filter_by(phase=phase)
            return [r.to_dict() for r in query.all()]
        finally:
            session.close()

    def create_experiment_config(
        self,
        experiment_id: str,
        question_id: str,
        config: dict,
        schema_file: str = None,
    ) -> ExperimentConfigDB:
        """Create a new experiment config."""
        import json

        session = self.get_session()
        try:
            exp = ExperimentConfigDB(
                experiment_id=experiment_id,
                question_id=question_id,
                config=json.dumps(config),
                schema_file=schema_file,
                status="pending",
            )
            session.add(exp)
            session.commit()
            session.refresh(exp)
            return exp
        finally:
            session.close()

    def update_experiment_results(
        self, experiment_id: str, results: dict, status: str = "completed"
    ):
        """Update experiment results."""
        import json
        from datetime import datetime

        session = self.get_session()
        try:
            exp = session.query(ExperimentConfigDB).filter_by(experiment_id=experiment_id).first()
            if exp:
                exp.results = json.dumps(results)
                exp.status = status
                exp.updated_at = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def create_test_case(
        self,
        test_id: str,
        question_id: str,
        test_file: str,
        agent_config: dict = None,
    ) -> TestCaseDB:
        """Create a new test case."""
        import json

        session = self.get_session()
        try:
            tc = TestCaseDB(
                test_id=test_id,
                question_id=question_id,
                test_file=test_file,
                agent_config=json.dumps(agent_config) if agent_config else None,
                status="pending",
            )
            session.add(tc)
            session.commit()
            session.refresh(tc)
            return tc
        finally:
            session.close()

    def update_test_case(
        self, test_id: str, status: str, score: float = None, feedback: str = None
    ):
        """Update a test case."""
        session = self.get_session()
        try:
            tc = session.query(TestCaseDB).filter_by(test_id=test_id).first()
            if tc:
                tc.status = status
                tc.score = score
                tc.feedback = feedback
                session.commit()
        finally:
            session.close()
