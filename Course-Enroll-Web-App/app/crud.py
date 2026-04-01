from datetime import date
from typing import Optional

from sqlmodel import Session, select

from .models import Course, Enrollment, Grade, Instructor, Role, Student, User, utc_now


def signup_user(
    session: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    role: Role,
) -> User:
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise ValueError("email-exists")

    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        role=role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    if role == Role.STUDENT:
        student = Student(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        session.add(student)
    elif role == Role.INSTRUCTOR:
        instructor = Instructor(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        session.add(instructor)

    session.commit()
    return user


def login_user(session: Session, *, email: str, password: str) -> Optional[User]:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user or user.password != password:
        return None
    return user


def get_student_by_user_id(session: Session, user_id: int) -> Optional[Student]:
    return session.exec(select(Student).where(Student.user_id == user_id)).first()


def get_instructor_by_user_id(session: Session, user_id: int) -> Optional[Instructor]:
    return session.exec(select(Instructor).where(Instructor.user_id == user_id)).first()


def get_students(session: Session):
    return session.exec(select(Student)).all()


def get_instructors(session: Session):
    return session.exec(select(Instructor)).all()


def create_course(
    session: Session,
    *,
    course_name: str,
    department: str,
    credits: int,
    capacity: int,
) -> Course:
    course = Course(
        course_name=course_name,
        department=department,
        credits=credits,
        capacity=capacity,
    )
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def update_course(session: Session, course_id: int, **updates) -> Optional[Course]:
    course = session.get(Course, course_id)
    if not course:
        return None
    for key, value in updates.items():
        if value is not None and hasattr(course, key):
            setattr(course, key, value)
    course.updated_at = utc_now()
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def delete_course(session: Session, course_id: int) -> bool:
    course = session.get(Course, course_id)
    if not course:
        return False
    enrollments = session.exec(select(Enrollment).where(Enrollment.course_id == course_id)).all()
    grades = session.exec(select(Grade).where(Grade.course_id == course_id)).all()
    for row in enrollments + grades:
        session.delete(row)
    session.delete(course)
    session.commit()
    return True


def get_courses(session: Session):
    return session.exec(select(Course)).all()


def get_instructor_courses(session: Session, instructor_id: int):
    return session.exec(select(Course).where(Course.instructor_id == instructor_id)).all()


def assign_instructor(session: Session, course_id: int, instructor_id: int) -> Optional[Course]:
    course = session.get(Course, course_id)
    instructor = session.get(Instructor, instructor_id)
    if not course or not instructor:
        return None
    course.instructor_id = instructor_id
    course.updated_at = utc_now()
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def set_course_schedule(
    session: Session,
    *,
    course_id: int,
    schedule_days: str,
    schedule_time: str,
    classroom_location: str,
) -> Optional[Course]:
    course = session.get(Course, course_id)
    if not course:
        return None
    course.schedule_days = schedule_days
    course.schedule_time = schedule_time
    course.classroom_location = classroom_location
    course.updated_at = utc_now()
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def clear_course_schedule(session: Session, *, course_id: int) -> Optional[Course]:
    course = session.get(Course, course_id)
    if not course:
        return None
    course.schedule_days = None
    course.schedule_time = None
    course.classroom_location = None
    course.updated_at = utc_now()
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def enroll_student(session: Session, student_id: int, course_id: int) -> Enrollment:
    student = session.get(Student, student_id)
    if not student:
        raise ValueError("student-not-found")

    course = session.get(Course, course_id)
    if not course:
        raise ValueError("course-not-found")

    existing = session.exec(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    ).first()
    if existing:
        return existing

    enrolled_count = len(
        session.exec(select(Enrollment).where(Enrollment.course_id == course_id)).all()
    )
    if enrolled_count >= course.capacity:
        raise ValueError("course-full")

    enrollment = Enrollment(student_id=student_id, course_id=course_id)
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment


def drop_enrollment(session: Session, student_id: int, course_id: int) -> bool:
    existing = session.exec(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
    ).first()
    if not existing:
        return False
    session.delete(existing)
    session.commit()
    return True


def get_student_courses(session: Session, student_id: int):
    enrollments = session.exec(select(Enrollment).where(Enrollment.student_id == student_id)).all()
    course_ids = [e.course_id for e in enrollments]
    if not course_ids:
        return []
    return session.exec(select(Course).where(Course.course_id.in_(course_ids))).all()


def get_course_students(session: Session, course_id: int):
    enrollments = session.exec(select(Enrollment).where(Enrollment.course_id == course_id)).all()
    student_ids = [e.student_id for e in enrollments]
    if not student_ids:
        return []
    return session.exec(select(Student).where(Student.student_id.in_(student_ids))).all()


def list_student_schedule(session: Session, student_id: int):
    courses = get_student_courses(session, student_id)
    return [
        {
            "course_id": c.course_id,
            "course_name": c.course_name,
            "days": c.schedule_days,
            "time": c.schedule_time,
            "classroom_location": c.classroom_location,
        }
        for c in courses
    ]


def get_student_grades(session: Session, student_id: int):
    grades = session.exec(select(Grade).where(Grade.student_id == student_id)).all()
    result = []
    for g in grades:
        course = session.get(Course, g.course_id)
        result.append(
            {
                "grade_id": g.grade_id,
                "course_id": g.course_id,
                "course_name": course.course_name if course else "Unknown",
                "grade": g.grade,
                "date_recorded": g.date_recorded,
            }
        )
    return result


def get_course_roster_with_grade_status(session: Session, course_id: int):
    students = get_course_students(session, course_id)
    rows = []
    for s in students:
        grade = session.exec(
            select(Grade).where(Grade.course_id == course_id, Grade.student_id == s.student_id)
        ).first()
        rows.append(
            {
                "student_id": s.student_id,
                "name": f"{s.first_name} {s.last_name}",
                "email": s.email,
                "grade": grade.grade if grade else None,
                "grade_status": "graded" if grade else "not graded",
            }
        )
    return rows


def get_instructor_dashboard_data(session: Session, instructor_id: int):
    courses = get_instructor_courses(session, instructor_id)
    dashboard_courses = []

    for course in courses:
        students = get_course_students(session, course.course_id)
        student_rows = []

        for student in students:
            grade = session.exec(
                select(Grade).where(
                    Grade.course_id == course.course_id,
                    Grade.student_id == student.student_id,
                    Grade.instructor_id == instructor_id,
                )
            ).first()
            student_rows.append(
                {
                    "student_id": student.student_id,
                    "student_name": f"{student.first_name} {student.last_name}",
                    "student_email": student.email,
                    "grade_id": grade.grade_id if grade else None,
                    "grade": grade.grade if grade else None,
                }
            )

        dashboard_courses.append(
            {
                "course_id": course.course_id,
                "course_name": course.course_name,
                "department": course.department,
                "schedule_days": course.schedule_days,
                "schedule_time": course.schedule_time,
                "classroom_location": course.classroom_location,
                "students": student_rows,
            }
        )

    return dashboard_courses


def create_grade(
    session: Session,
    *,
    student_id: int,
    course_id: int,
    instructor_id: int,
    grade_value: str,
) -> Grade:
    grade = session.exec(
        select(Grade).where(
            Grade.student_id == student_id,
            Grade.course_id == course_id,
            Grade.instructor_id == instructor_id,
        )
    ).first()
    if grade:
        raise ValueError("grade-already-exists")

    grade = Grade(
        student_id=student_id,
        course_id=course_id,
        instructor_id=instructor_id,
        grade=grade_value,
    )
    session.add(grade)
    session.commit()
    session.refresh(grade)
    return grade


def update_grade(
    session: Session,
    *,
    student_id: int,
    course_id: int,
    instructor_id: int,
    grade_value: str,
) -> Grade:
    grade = session.exec(
        select(Grade).where(
            Grade.student_id == student_id,
            Grade.course_id == course_id,
            Grade.instructor_id == instructor_id,
        )
    ).first()
    if not grade:
        raise ValueError("grade-not-found")

    grade.grade = grade_value
    grade.date_recorded = date.today()
    grade.updated_at = utc_now()
    session.add(grade)
    session.commit()
    session.refresh(grade)
    return grade


def delete_grade(session: Session, grade_id: int) -> bool:
    grade = session.get(Grade, grade_id)
    if not grade:
        return False
    session.delete(grade)
    session.commit()
    return True


def remove_instructor(session: Session, instructor_id: int) -> bool:
    instructor = session.get(Instructor, instructor_id)
    if not instructor:
        return False

    courses = session.exec(select(Course).where(Course.instructor_id == instructor_id)).all()
    for course in courses:
        course.instructor_id = None
        course.updated_at = utc_now()
        session.add(course)

    grades = session.exec(select(Grade).where(Grade.instructor_id == instructor_id)).all()
    for grade in grades:
        session.delete(grade)

    user = session.get(User, instructor.user_id)
    session.delete(instructor)
    if user:
        session.delete(user)
    session.commit()
    return True
