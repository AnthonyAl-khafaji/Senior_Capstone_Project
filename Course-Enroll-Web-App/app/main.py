from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select

import app.crud as crud
from .database import get_session, init_db
from .models import Course, Grade, Instructor, Role, Student, User

app = FastAPI(title="College Enrollment API")

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
def root():
    index = static_dir / "index.html"
    if index.exists():
        return FileResponse(index)
    raise HTTPException(status_code=404, detail="index not found")


@app.on_event("startup")
def on_startup():
    init_db()


class SignupPayload(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    role: Role


class LoginPayload(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    role: Role
    first_name: str
    last_name: str
    email: str


class CourseCreatePayload(BaseModel):
    course_name: str
    department: str
    credits: int
    capacity: int


class CourseUpdatePayload(BaseModel):
    course_name: Optional[str] = None
    department: Optional[str] = None
    credits: Optional[int] = None
    capacity: Optional[int] = None


class InstructorUpdatePayload(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    department: Optional[str] = None
    office_location: Optional[str] = None


class InstructorInfoPayload(BaseModel):
    department: Optional[str] = None
    office_location: Optional[str] = None


class AssignInstructorPayload(BaseModel):
    instructor_id: int


class SchedulePayload(BaseModel):
    schedule_days: str
    schedule_time: str
    classroom_location: str


class GradePayload(BaseModel):
    student_id: int
    course_id: int
    grade: str


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.id,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
    )


def get_current_user(
    x_user_id: Optional[int] = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="missing x-user-id header")
    user = session.get(User, x_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="invalid user")
    return user


def require_role(user: User, allowed: List[Role]) -> None:
    if user.role not in allowed:
        raise HTTPException(status_code=403, detail="forbidden")


@app.post("/auth/signup", response_model=UserResponse)
def signup(payload: SignupPayload, session: Session = Depends(get_session)):
    try:
        user = crud.signup_user(
            session,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
        return to_user_response(user)
    except ValueError as e:
        if str(e) == "email-exists":
            raise HTTPException(status_code=400, detail="email already exists")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", response_model=UserResponse)
def login(payload: LoginPayload, session: Session = Depends(get_session)):
    user = crud.login_user(session, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    return to_user_response(user)


@app.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return to_user_response(user)


@app.get("/courses", response_model=List[Course])
def list_courses(session: Session = Depends(get_session)):
    return crud.get_courses(session)


@app.get("/students", response_model=List[Student])
def list_students(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN, Role.INSTRUCTOR])
    return crud.get_students(session)


@app.get("/instructors", response_model=List[Instructor])
def list_instructors(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    return crud.get_instructors(session)


@app.put("/admin/instructors/{instructor_id}", response_model=Instructor)
def update_instructor(
    instructor_id: int,
    payload: InstructorUpdatePayload,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    instructor = session.get(Instructor, instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="instructor not found")

    owner = session.get(User, instructor.user_id)
    duplicate = session.exec(select(User).where(User.email == payload.email)).first()
    if duplicate and duplicate.id != owner.id:
        raise HTTPException(status_code=400, detail="email already exists")

    owner.first_name = payload.first_name
    owner.last_name = payload.last_name
    owner.email = payload.email
    owner.password = payload.password

    instructor.first_name = payload.first_name
    instructor.last_name = payload.last_name
    instructor.email = payload.email
    instructor.department = payload.department
    instructor.office_location = payload.office_location

    session.add(owner)
    session.add(instructor)
    session.commit()
    session.refresh(instructor)
    return instructor


@app.delete("/admin/instructors/{instructor_id}")
def delete_instructor(
    instructor_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    ok = crud.remove_instructor(session, instructor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="instructor not found")
    return {"status": "deleted", "instructor_id": instructor_id}


@app.patch("/admin/instructors/{instructor_id}/info", response_model=Instructor)
def update_instructor_info(
    instructor_id: int,
    payload: InstructorInfoPayload,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    instructor = session.get(Instructor, instructor_id)
    if not instructor:
        raise HTTPException(status_code=404, detail="instructor not found")

    if payload.department is None and payload.office_location is None:
        raise HTTPException(
            status_code=400,
            detail="provide department and/or office_location",
        )

    if payload.department is not None:
        instructor.department = payload.department
    if payload.office_location is not None:
        instructor.office_location = payload.office_location

    session.add(instructor)
    session.commit()
    session.refresh(instructor)
    return instructor


@app.post("/courses", response_model=Course)
def create_course(
    payload: CourseCreatePayload,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    return crud.create_course(
        session,
        course_name=payload.course_name,
        department=payload.department,
        credits=payload.credits,
        capacity=payload.capacity,
    )


@app.put("/courses/{course_id}", response_model=Course)
def edit_course(
    course_id: int,
    payload: CourseUpdatePayload,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    course = crud.update_course(session, course_id, **payload.model_dump())
    if not course:
        raise HTTPException(status_code=404, detail="course not found")
    return course


@app.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    ok = crud.delete_course(session, course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="course not found")
    return {"status": "deleted", "course_id": course_id}


@app.post("/admin/courses/{course_id}/assign-instructor", response_model=Course)
def assign_instructor(
    course_id: int,
    payload: AssignInstructorPayload,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    course = crud.assign_instructor(session, course_id, payload.instructor_id)
    if not course:
        raise HTTPException(status_code=404, detail="course or instructor not found")
    return course


@app.post("/admin/courses/{course_id}/schedule", response_model=Course)
def manage_schedule(
    course_id: int,
    payload: SchedulePayload,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.ADMIN])
    course = crud.set_course_schedule(
        session,
        course_id=course_id,
        schedule_days=payload.schedule_days,
        schedule_time=payload.schedule_time,
        classroom_location=payload.classroom_location,
    )
    if not course:
        raise HTTPException(status_code=404, detail="course not found")
    return course


@app.post("/enrollments")
def enroll(
    course_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.STUDENT])
    student = crud.get_student_by_user_id(session, user.id)
    if not student:
        raise HTTPException(status_code=404, detail="student profile not found")
    try:
        enrollment = crud.enroll_student(
            session,
            student_id=student.student_id,
            course_id=course_id,
        )
        return {
            "status": "enrolled",
            "student_id": enrollment.student_id,
            "course_id": enrollment.course_id,
        }
    except ValueError as e:
        if str(e) == "student-not-found":
            raise HTTPException(status_code=404, detail="student not found")
        if str(e) == "course-not-found":
            raise HTTPException(status_code=404, detail="course not found")
        if str(e) == "course-full":
            raise HTTPException(status_code=400, detail="course is full")
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/enrollments")
def drop(
    course_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.STUDENT])
    student = crud.get_student_by_user_id(session, user.id)
    if not student:
        raise HTTPException(status_code=404, detail="student profile not found")
    ok = crud.drop_enrollment(session, student_id=student.student_id, course_id=course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="enrollment not found")
    return {"status": "dropped"}


@app.get("/student/courses", response_model=List[Course])
def student_courses(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.STUDENT])
    student = crud.get_student_by_user_id(session, user.id)
    if not student:
        raise HTTPException(status_code=404, detail="student profile not found")
    return crud.get_student_courses(session, student.student_id)


@app.get("/student/grades")
def student_grades(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.STUDENT])
    student = crud.get_student_by_user_id(session, user.id)
    if not student:
        raise HTTPException(status_code=404, detail="student profile not found")
    return crud.get_student_grades(session, student.student_id)


@app.get("/student/schedule")
def student_schedule(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.STUDENT])
    student = crud.get_student_by_user_id(session, user.id)
    if not student:
        raise HTTPException(status_code=404, detail="student profile not found")
    return crud.list_student_schedule(session, student.student_id)


@app.get("/instructor/courses")
def instructor_courses(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.INSTRUCTOR])
    instructor = crud.get_instructor_by_user_id(session, user.id)
    if not instructor:
        raise HTTPException(status_code=404, detail="instructor profile not found")
    return crud.get_instructor_courses(session, instructor.instructor_id)


@app.get("/instructor/courses/{course_id}/roster")
def instructor_course_roster(
    course_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.INSTRUCTOR])
    instructor = crud.get_instructor_by_user_id(session, user.id)
    if not instructor:
        raise HTTPException(status_code=404, detail="instructor profile not found")
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="course not found")
    if course.instructor_id != instructor.instructor_id:
        raise HTTPException(status_code=403, detail="not your course")
    return crud.get_course_roster_with_grade_status(session, course_id)


@app.post("/instructor/grades")
def create_or_update_grade(
    payload: GradePayload,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.INSTRUCTOR])
    instructor = crud.get_instructor_by_user_id(session, user.id)
    if not instructor:
        raise HTTPException(status_code=404, detail="instructor profile not found")

    course = session.get(Course, payload.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="course not found")
    if course.instructor_id != instructor.instructor_id:
        raise HTTPException(status_code=403, detail="not your course")

    grade = crud.upsert_grade(
        session,
        student_id=payload.student_id,
        course_id=payload.course_id,
        instructor_id=instructor.instructor_id,
        grade_value=payload.grade,
    )
    return {
        "grade_id": grade.grade_id,
        "student_id": grade.student_id,
        "course_id": grade.course_id,
        "grade": grade.grade,
    }


@app.delete("/instructor/grades/{grade_id}")
def delete_grade(
    grade_id: int,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    require_role(user, [Role.INSTRUCTOR])
    instructor = crud.get_instructor_by_user_id(session, user.id)
    if not instructor:
        raise HTTPException(status_code=404, detail="instructor profile not found")

    grade = session.get(Grade, grade_id)
    if not grade:
        raise HTTPException(status_code=404, detail="grade not found")
    if grade.instructor_id != instructor.instructor_id:
        raise HTTPException(status_code=403, detail="not your grade record")

    ok = crud.delete_grade(session, grade_id)
    if not ok:
        raise HTTPException(status_code=404, detail="grade not found")
    return {"status": "deleted", "grade_id": grade_id}


@app.get("/admin")
def admin_page():
    admin_html = static_dir / "admin.html"
    if admin_html.exists():
        return FileResponse(admin_html)
    raise HTTPException(status_code=404, detail="admin page not found")
