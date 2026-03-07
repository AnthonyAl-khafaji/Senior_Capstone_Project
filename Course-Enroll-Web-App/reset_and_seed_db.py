#!/usr/bin/env python3
from pathlib import Path

from sqlalchemy import func
from sqlmodel import Session, SQLModel, create_engine, select

# Import models so SQLModel metadata includes all tables.
from app.models import Course, Enrollment, Grade, Instructor, Role, Student, User


STUDENT_COUNT = 12
INSTRUCTOR_COUNT = 5
ADMIN_COUNT = 2
COURSE_COUNT = 10


def reset_database(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()


def create_tables(engine) -> None:
    SQLModel.metadata.create_all(engine)


def seed_data(engine) -> None:
    with Session(engine) as session:
        students = []
        instructors = []

        for i in range(1, STUDENT_COUNT + 1):
            user = User(
                first_name=f"Student{i}",
                last_name="User",
                email=f"student_user{i}@example.com",
                password="password123",
                role=Role.STUDENT,
            )
            session.add(user)
            session.commit()
            students.append(
                Student(
                    user_id=user.id,
                    first_name=f"Student{i}",
                    last_name="Demo",
                    email=f"student{i}@example.com",
                    major="Computer Science",
                    class_year=f"20{27 + (i % 4)}",
                )
            )

        for i in range(1, INSTRUCTOR_COUNT + 1):
            user = User(
                first_name=f"Instructor{i}",
                last_name="User",
                email=f"instructor_user{i}@example.com",
                password="password123",
                role=Role.INSTRUCTOR,
            )
            session.add(user)
            session.commit()
            instructors.append(
                Instructor(
                    user_id=user.id,
                    first_name=f"Instructor{i}",
                    last_name="Demo",
                    email=f"instructor{i}@example.com",
                    department="CS",
                    office_location=f"Building A, Room {100 + i}",
                )
            )

        for i in range(1, ADMIN_COUNT + 1):
            session.add(
                User(
                    first_name=f"Admin{i}",
                    last_name="User",
                    email=f"admin{i}@example.com",
                    password="password123",
                    role=Role.ADMIN,
                )
            )

        session.add_all(students)
        session.add_all(instructors)
        session.commit()

        courses = []
        for i in range(1, COURSE_COUNT + 1):
            courses.append(
                Course(
                    course_name=f"Course {i}",
                    department="CS",
                    credits=3 if i % 2 else 4,
                    capacity=30,
                    instructor_id=((i - 1) % INSTRUCTOR_COUNT) + 1,
                    schedule_days="Mon/Wed" if i % 2 else "Tue/Thu",
                    schedule_time=f"{8 + (i % 5)}:00 AM",
                    classroom_location=f"Room {200 + i}",
                )
            )

        session.add_all(courses)
        session.commit()

        enrollments = []
        grades = []
        grade_values = ["A", "A-", "B+", "B", "B-", "C+", "C"]

        # Give each student 3 distinct course enrollments.
        for student_id in range(1, STUDENT_COUNT + 1):
            for offset in range(3):
                course_id = ((student_id + offset - 1) % COURSE_COUNT) + 1
                enrollments.append(
                    Enrollment(
                        student_id=student_id,
                        course_id=course_id,
                        status="enrolled",
                    )
                )

                # Record grades for roughly two thirds of enrollments.
                if (student_id + offset) % 3 != 0:
                    grades.append(
                        Grade(
                            student_id=student_id,
                            course_id=course_id,
                            instructor_id=((course_id - 1) % INSTRUCTOR_COUNT) + 1,
                            grade=grade_values[(student_id + offset) % len(grade_values)],
                        )
                    )

        session.add_all(enrollments)
        session.add_all(grades)
        session.commit()


def _count_rows(session: Session, model) -> int:
    return session.exec(select(func.count()).select_from(model)).one()


def print_summary(engine) -> None:
    with Session(engine) as session:
        counts = {
            "user": _count_rows(session, User),
            "student": _count_rows(session, Student),
            "instructor": _count_rows(session, Instructor),
            "course": _count_rows(session, Course),
            "enrollment": _count_rows(session, Enrollment),
            "grade": _count_rows(session, Grade),
        }

    print("Seeded row counts:")
    for table_name, row_count in counts.items():
        print(f"- {table_name}: {row_count}")


def main() -> None:
    project_root = Path(__file__).resolve().parent
    db_path = project_root / "database.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    reset_database(db_path)
    create_tables(engine)
    seed_data(engine)
    print_summary(engine)

    print(f"Reset and seeded database at {db_path}")
    print("Seeding complete with schema-appropriate row counts.")


if __name__ == "__main__":
    main()
