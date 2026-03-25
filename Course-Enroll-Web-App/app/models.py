from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


def utc_now() -> datetime:
    return datetime.utcnow()


class Role(str, Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(index=True, unique=True)
    password: str
    role: Role = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Student(SQLModel, table=True):
    student_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    first_name: str
    last_name: str
    email: str = Field(index=True, unique=True)
    major: Optional[str] = None
    class_year: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Instructor(SQLModel, table=True):
    instructor_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    first_name: str
    last_name: str
    email: str = Field(index=True, unique=True)
    department: Optional[str] = None
    office_location: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Course(SQLModel, table=True):
    course_id: Optional[int] = Field(default=None, primary_key=True)
    course_name: str
    department: str
    credits: int
    capacity: int = 30
    instructor_id: Optional[int] = Field(default=None, foreign_key="instructor.instructor_id")
    schedule_days: Optional[str] = None
    schedule_time: Optional[str] = None
    classroom_location: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Enrollment(SQLModel, table=True):
    enrollment_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", index=True)
    course_id: int = Field(foreign_key="course.course_id", index=True)
    enrollment_date: date = Field(default_factory=date.today)
    status: str = Field(default="enrolled")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Grade(SQLModel, table=True):
    grade_id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="student.student_id", index=True)
    course_id: int = Field(foreign_key="course.course_id", index=True)
    instructor_id: int = Field(foreign_key="instructor.instructor_id", index=True)
    grade: str
    date_recorded: date = Field(default_factory=date.today)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
