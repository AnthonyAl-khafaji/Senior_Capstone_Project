#!/usr/bin/env python3
import csv
from pathlib import Path

from sqlalchemy import func
from sqlmodel import Session, SQLModel, create_engine, select

# Import models so SQLModel metadata includes all tables.
from app.models import Course, Enrollment, Grade, Instructor, Role, Student, User


STUDENT_COUNT = 10
INSTRUCTOR_COUNT = 10
COURSE_COUNT = 30

ADMIN_PROFILES = [
    ("Emma", "Johnson", "emma.johnson", "1234"),
    ("Liam", "Martinez", "liam.martinez", "4321"),
]

STUDENT_PROFILES = [
    ("Olivia", "Nguyen", "olivia.nguyen", "0000"),
    ("Ava", "Rodriguez", "ava.rodriguez", "4321"),
    ("Sophia", "Kim", "sophia.kim", "1234"),
    ("Isabella", "Green", "isabella.green", "0000"),
    ("Mia", "Carter", "mia.carter", "4321"),
    ("Harper", "Lewis", "harper.lewis", "1234"),
    ("Amelia", "Scott", "amelia.scott", "0000"),
    ("Evelyn", "Adams", "evelyn.adams", "1234"),
    ("Abigail", "Turner", "abigail.turner", "4321"),
    ("Emily", "Perez", "emily.perez", "0000"),
]

INSTRUCTOR_PROFILES = [
    ("Noah", "Thompson", "noah.thompson", "1234"),
    ("Ethan", "Walker", "ethan.walker", "0000"),
    ("Mason", "Patel", "mason.patel", "4321"),
    ("Lucas", "Bennett", "lucas.bennett", "1234"),
    ("Logan", "Ramirez", "logan.ramirez", "4321"),
    ("James", "Morris", "james.morris", "0000"),
    ("Benjamin", "Reed", "benjamin.reed", "1234"),
    ("Elijah", "Cook", "elijah.cook", "4321"),
    ("Alexander", "Bailey", "alexander.bailey", "0000"),
    ("Henry", "Rivera", "henry.rivera", "1234"),
]


def reset_database(db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()


def create_tables(engine) -> None:
    SQLModel.metadata.create_all(engine)


def seed_data(engine) -> None:
    with Session(engine) as session:
        admin_users = []
        student_users = []
        instructor_users = []

        for first_name, last_name, username, password in ADMIN_PROFILES:
            admin_users.append(
                User(
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{username}@campus.edu",
                    password=password,
                    role=Role.ADMIN,
                )
            )

        for first_name, last_name, username, password in STUDENT_PROFILES:
            student_users.append(
                User(
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{username}@campus.edu",
                    password=password,
                    role=Role.STUDENT,
                )
            )

        for first_name, last_name, username, password in INSTRUCTOR_PROFILES:
            instructor_users.append(
                User(
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{username}@campus.edu",
                    password=password,
                    role=Role.INSTRUCTOR,
                )
            )

        session.add_all(admin_users + student_users + instructor_users)
        session.commit()

        students = []
        instructors = []

        for i, (user, profile) in enumerate(zip(student_users, STUDENT_PROFILES), start=1):
            first_name, last_name, username, _ = profile
            students.append(
                Student(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{username}+student@campus.edu",
                    major=["Computer Science", "Mathematics", "Biology", "Economics"][i % 4],
                    class_year=f"20{26 + (i % 4)}",
                )
            )

        for i, (user, profile) in enumerate(zip(instructor_users, INSTRUCTOR_PROFILES), start=1):
            first_name, last_name, username, _ = profile
            instructors.append(
                Instructor(
                    user_id=user.id,
                    first_name=first_name,
                    last_name=last_name,
                    email=f"{username}+instructor@campus.edu",
                    department=["CS", "Math", "Physics", "Biology", "History"][i % 5],
                    office_location=f"Building A, Room {100 + i}",
                )
            )

        session.add_all(students)
        session.add_all(instructors)
        session.commit()

        courses = []
        for i in range(1, COURSE_COUNT + 1):
            courses.append(
                Course(
                    course_name=f"Course {i:02d}",
                    department=["CS", "Math", "Physics", "Biology", "History"][i % 5],
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
        grade_values = ["A", "A-", "B+", "B", "B-", "C+", "C", "A", "B+", "A-"]

        for i in range(1, STUDENT_COUNT + 1):
            course_id = i
            enrollments.append(
                Enrollment(
                    student_id=i,
                    course_id=course_id,
                    status="enrolled",
                )
            )
            grades.append(
                Grade(
                    student_id=i,
                    course_id=course_id,
                    instructor_id=((course_id - 1) % INSTRUCTOR_COUNT) + 1,
                    grade=grade_values[i - 1],
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


def write_credentials_csv(project_root: Path) -> None:
    csv_path = project_root / "seeded_users.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["first_name", "last_name", "username", "email", "role", "password"])
        all_rows = (
            [(r[0], r[1], r[2], "admin", r[3]) for r in ADMIN_PROFILES]
            + [(r[0], r[1], r[2], "student", r[3]) for r in STUDENT_PROFILES]
            + [(r[0], r[1], r[2], "instructor", r[3]) for r in INSTRUCTOR_PROFILES]
        )
        for first_name, last_name, username, role, password in all_rows:
            writer.writerow(
                [
                    first_name,
                    last_name,
                    username,
                    f"{username}@campus.edu",
                    role,
                    password,
                ]
            )


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
    write_credentials_csv(project_root)

    print(f"Reset and seeded database at {db_path}")
    print(f"Wrote credentials CSV to {project_root / 'seeded_users.csv'}")
    print("Seeding complete with requested row counts and credential rules.")


if __name__ == "__main__":
    main()
