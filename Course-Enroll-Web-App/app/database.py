from typing import Generator

from sqlalchemy import inspect
from sqlmodel import SQLModel, Session, create_engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Note: check_same_thread=False is required for SQLite when using in-process threads
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})


def _schema_is_compatible() -> bool:
    inspector = inspect(engine)

    if "course" not in inspector.get_table_names():
        return True

    course_columns = {col["name"] for col in inspector.get_columns("course")}
    expected_course_columns = {
        "course_id",
        "course_name",
        "department",
        "credits",
        "capacity",
        "instructor_id",
        "schedule_days",
        "schedule_time",
        "classroom_location",
        "created_at",
        "updated_at",
    }
    return expected_course_columns.issubset(course_columns)


def init_db() -> None:
    if not _schema_is_compatible():
        # Local development fallback: reset old schema from earlier project versions.
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
