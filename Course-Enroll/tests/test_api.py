import pathlib
import sys

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

# Ensure project root is importable when running pytest
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import app.main as main


@pytest.fixture()
def test_engine(tmp_path):
    db_file = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture()
def client(test_engine):
    def get_session_override():
        with Session(test_engine) as session:
            yield session

    main.app.dependency_overrides[main.get_session] = get_session_override
    c = TestClient(main.app)
    yield c
    main.app.dependency_overrides.pop(main.get_session, None)


def signup_and_login(client, *, role, first, last, email, password="pw123"):
    r = client.post(
        "/auth/signup",
        json={
            "first_name": first,
            "last_name": last,
            "email": email,
            "password": password,
            "role": role,
        },
    )
    assert r.status_code == 200

    r2 = client.post("/auth/login", json={"email": email, "password": password})
    assert r2.status_code == 200
    return r2.json()


def test_signup_login_and_me(client):
    user = signup_and_login(
        client,
        role="student",
        first="Alice",
        last="Stone",
        email="alice@example.com",
    )

    me = client.get("/me", headers={"x-user-id": str(user["user_id"])})
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["role"] == "student"
    assert me_data["email"] == "alice@example.com"


def test_admin_course_management_and_student_enrollment_flow(client):
    admin = signup_and_login(
        client,
        role="admin",
        first="Admin",
        last="User",
        email="admin@example.com",
    )
    student = signup_and_login(
        client,
        role="student",
        first="Bob",
        last="Lee",
        email="bob@example.com",
    )

    create = client.post(
        "/courses",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "course_name": "Intro to CS",
            "department": "CS",
            "credits": 3,
            "capacity": 1,
        },
    )
    assert create.status_code == 200
    cid = create.json()["course_id"]

    enroll = client.post(
        f"/enrollments?course_id={cid}",
        headers={"x-user-id": str(student["user_id"])},
    )
    assert enroll.status_code == 200
    assert enroll.json()["status"] == "enrolled"

    student_courses = client.get(
        "/student/courses",
        headers={"x-user-id": str(student["user_id"])},
    )
    assert student_courses.status_code == 200
    assert len(student_courses.json()) == 1

    drop = client.delete(
        f"/enrollments?course_id={cid}",
        headers={"x-user-id": str(student["user_id"])},
    )
    assert drop.status_code == 200
    assert drop.json()["status"] == "dropped"


def test_capacity_limit(client):
    admin = signup_and_login(
        client,
        role="admin",
        first="Admin",
        last="User",
        email="capadmin@example.com",
    )
    student1 = signup_and_login(
        client,
        role="student",
        first="S1",
        last="A",
        email="s1@example.com",
    )
    student2 = signup_and_login(
        client,
        role="student",
        first="S2",
        last="B",
        email="s2@example.com",
    )

    create = client.post(
        "/courses",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "course_name": "Data Structures",
            "department": "CS",
            "credits": 4,
            "capacity": 1,
        },
    )
    cid = create.json()["course_id"]

    e1 = client.post(
        f"/enrollments?course_id={cid}",
        headers={"x-user-id": str(student1["user_id"])},
    )
    assert e1.status_code == 200

    e2 = client.post(
        f"/enrollments?course_id={cid}",
        headers={"x-user-id": str(student2["user_id"])},
    )
    assert e2.status_code == 400


def test_role_restriction_for_course_creation(client):
    student = signup_and_login(
        client,
        role="student",
        first="No",
        last="Admin",
        email="student.only@example.com",
    )

    create = client.post(
        "/courses",
        headers={"x-user-id": str(student["user_id"])},
        json={
            "course_name": "Illegal Course",
            "department": "X",
            "credits": 1,
            "capacity": 10,
        },
    )
    assert create.status_code == 403


def test_admin_can_update_created_schedule(client):
    admin = signup_and_login(
        client,
        role="admin",
        first="Sched",
        last="Admin",
        email="schedadmin@example.com",
    )

    create = client.post(
        "/courses",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "course_name": "Algorithms",
            "department": "CS",
            "credits": 3,
            "capacity": 30,
        },
    )
    assert create.status_code == 200
    cid = create.json()["course_id"]

    update_before_create = client.put(
        f"/admin/courses/{cid}/schedule",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "schedule_days": "Tue/Thu",
            "schedule_time": "09:00-10:15",
            "classroom_location": "B201",
        },
    )
    assert update_before_create.status_code == 400

    create_schedule = client.post(
        f"/admin/courses/{cid}/schedule",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "schedule_days": "Mon/Wed",
            "schedule_time": "10:00-11:15",
            "classroom_location": "A101",
        },
    )
    assert create_schedule.status_code == 200

    update_created = client.put(
        f"/admin/courses/{cid}/schedule",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "schedule_days": "Tue/Thu",
            "schedule_time": "09:00-10:15",
            "classroom_location": "B201",
        },
    )
    assert update_created.status_code == 200
    payload = update_created.json()
    assert payload["schedule_days"] == "Tue/Thu"
    assert payload["schedule_time"] == "09:00-10:15"
    assert payload["classroom_location"] == "B201"

    partial_update = client.put(
        f"/admin/courses/{cid}/schedule",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "classroom_location": "C303",
        },
    )
    assert partial_update.status_code == 200
    partial_payload = partial_update.json()
    assert partial_payload["schedule_days"] == "Tue/Thu"
    assert partial_payload["schedule_time"] == "09:00-10:15"
    assert partial_payload["classroom_location"] == "C303"

    deleted = client.delete(
        f"/admin/courses/{cid}/schedule",
        headers={"x-user-id": str(admin["user_id"])},
    )
    assert deleted.status_code == 200
    deleted_payload = deleted.json()
    assert deleted_payload["schedule_days"] is None
    assert deleted_payload["schedule_time"] is None
    assert deleted_payload["classroom_location"] is None


def test_instructor_dashboard_shows_students_and_grades(client):
    admin = signup_and_login(
        client,
        role="admin",
        first="Admin",
        last="Dash",
        email="dashadmin@example.com",
    )
    instructor = signup_and_login(
        client,
        role="instructor",
        first="Ivy",
        last="Teach",
        email="ivy@example.com",
    )
    student = signup_and_login(
        client,
        role="student",
        first="Stu",
        last="Dent",
        email="stud@example.com",
    )

    create = client.post(
        "/courses",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "course_name": "Operating Systems",
            "department": "CS",
            "credits": 3,
            "capacity": 30,
        },
    )
    assert create.status_code == 200
    course_id = create.json()["course_id"]

    instructors = client.get(
        "/instructors",
        headers={"x-user-id": str(admin["user_id"])},
    )
    assert instructors.status_code == 200
    instructor_id = instructors.json()[0]["instructor_id"]

    assigned = client.post(
        f"/admin/courses/{course_id}/assign-instructor",
        headers={"x-user-id": str(admin["user_id"])},
        json={"instructor_id": instructor_id},
    )
    assert assigned.status_code == 200

    enrolled = client.post(
        f"/enrollments?course_id={course_id}",
        headers={"x-user-id": str(student["user_id"])},
    )
    assert enrolled.status_code == 200

    dashboard_before_grade = client.get(
        "/instructor/dashboard",
        headers={"x-user-id": str(instructor["user_id"])},
    )
    assert dashboard_before_grade.status_code == 200
    row = dashboard_before_grade.json()["courses"][0]["students"][0]
    assert row["student_name"] == "Stu Dent"
    assert row["grade"] is None

    saved_grade = client.post(
        "/instructor/grades",
        headers={"x-user-id": str(instructor["user_id"])},
        json={"student_id": row["student_id"], "course_id": course_id, "grade": "A"},
    )
    assert saved_grade.status_code == 200

    dashboard_after_grade = client.get(
        "/instructor/dashboard",
        headers={"x-user-id": str(instructor["user_id"])},
    )
    assert dashboard_after_grade.status_code == 200
    row_after = dashboard_after_grade.json()["courses"][0]["students"][0]
    assert row_after["grade"] == "A"


def test_admin_can_update_instructor_assignment(client):
    admin = signup_and_login(
        client,
        role="admin",
        first="Assign",
        last="Admin",
        email="assignadmin@example.com",
    )
    signup_and_login(
        client,
        role="instructor",
        first="First",
        last="Instructor",
        email="firstins@example.com",
    )
    signup_and_login(
        client,
        role="instructor",
        first="Second",
        last="Instructor",
        email="secondins@example.com",
    )

    create = client.post(
        "/courses",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "course_name": "Networks",
            "department": "CS",
            "credits": 3,
            "capacity": 20,
        },
    )
    assert create.status_code == 200
    course_id = create.json()["course_id"]

    instructors = client.get(
        "/instructors",
        headers={"x-user-id": str(admin["user_id"])},
    )
    assert instructors.status_code == 200
    by_email = {ins["email"]: ins["instructor_id"] for ins in instructors.json()}
    first_instructor_id = by_email["firstins@example.com"]
    second_instructor_id = by_email["secondins@example.com"]

    assigned = client.post(
        f"/admin/courses/{course_id}/assign-instructor",
        headers={"x-user-id": str(admin["user_id"])},
        json={"instructor_id": first_instructor_id},
    )
    assert assigned.status_code == 200
    assert assigned.json()["instructor_id"] == first_instructor_id

    updated = client.put(
        f"/admin/courses/{course_id}/update-instructor",
        headers={"x-user-id": str(admin["user_id"])},
        json={"instructor_id": second_instructor_id},
    )
    assert updated.status_code == 200
    assert updated.json()["instructor_id"] == second_instructor_id


def test_student_catalog_defaults_to_available_courses_only(client):
    admin = signup_and_login(
        client,
        role="admin",
        first="Catalog",
        last="Admin",
        email="catalogadmin@example.com",
    )
    student1 = signup_and_login(
        client,
        role="student",
        first="Catalog",
        last="One",
        email="catalog1@example.com",
    )
    student2 = signup_and_login(
        client,
        role="student",
        first="Catalog",
        last="Two",
        email="catalog2@example.com",
    )

    full_course = client.post(
        "/courses",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "course_name": "Full Course",
            "department": "BUS",
            "credits": 3,
            "capacity": 1,
        },
    )
    assert full_course.status_code == 200
    full_course_id = full_course.json()["course_id"]

    available_course = client.post(
        "/courses",
        headers={"x-user-id": str(admin["user_id"])},
        json={
            "course_name": "Open Course",
            "department": "ENG",
            "credits": 3,
            "capacity": 2,
        },
    )
    assert available_course.status_code == 200
    open_course_id = available_course.json()["course_id"]

    enroll = client.post(
        f"/enrollments?course_id={full_course_id}",
        headers={"x-user-id": str(student1["user_id"])},
    )
    assert enroll.status_code == 200

    default_catalog = client.get(
        "/student/catalog",
        headers={"x-user-id": str(student2["user_id"])},
    )
    assert default_catalog.status_code == 200
    default_ids = {row["course_id"] for row in default_catalog.json()}
    assert open_course_id in default_ids
    assert full_course_id not in default_ids

    with_unavailable = client.get(
        "/student/catalog?include_unavailable=true",
        headers={"x-user-id": str(student2["user_id"])},
    )
    assert with_unavailable.status_code == 200
    with_unavailable_rows = {row["course_id"]: row for row in with_unavailable.json()}
    assert open_course_id in with_unavailable_rows
    assert full_course_id in with_unavailable_rows
    assert with_unavailable_rows[full_course_id]["is_available"] is False
    assert with_unavailable_rows[full_course_id]["seats_remaining"] == 0
