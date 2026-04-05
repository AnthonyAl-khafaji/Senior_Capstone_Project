# Campus Portal (FastAPI + SQLModel)

Role-based college enrollment system with login/signup and separate student, instructor, and admin workflows.

## Quick Start

1. Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Start the server:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

3. Open:

- App: `http://127.0.0.1:8000/`
- API docs: `http://127.0.0.1:8000/docs`

## Implemented Features

- Login-first portal with signup and login.
- Roles: `student`, `instructor`, `admin`.
- Student dashboard:
  - Course Catalog (view courses, enroll with capacity check)
  - My Courses (drop enrolled courses)
  - Grades (view instructor-posted grades)
  - Schedule (days/time/location from course schedule)
- Instructor dashboard:
  - My Courses
  - Course Roster (student + grade status)
  - Grade Management (create/update/delete grade records)
- Admin dashboard:
  - Course Management (add/edit/delete courses)
  - Instructor Management (update department/office for existing instructors and remove instructor records)
  - Instructor Assignment (assign instructor to course)
  - Schedule Management (days/time/classroom per course)
- Logout button on each role dashboard returns to login view.

## Main API Endpoints

Auth:

- `POST /auth/signup`
- `POST /auth/login`
- `GET /me`

Student:

- `GET /courses`
- `POST /enrollments?course_id={id}`
- `DELETE /enrollments?course_id={id}`
- `GET /student/courses`
- `GET /student/grades`
- `GET /student/schedule`

Instructor:

- `GET /instructor/courses`
- `GET /instructor/courses/{course_id}/roster`
- `POST /instructor/grades`
- `DELETE /instructor/grades/{grade_id}`

Admin:

- `POST /courses`
- `PUT /courses/{course_id}`
- `DELETE /courses/{course_id}`
- `GET /instructors`
- `PUT /admin/instructors/{instructor_id}`
- `PATCH /admin/instructors/{instructor_id}/info`
- `DELETE /admin/instructors/{instructor_id}`
- `POST /admin/courses/{course_id}/assign-instructor`
- `POST /admin/courses/{course_id}/schedule`

Note: authenticated endpoints use header `x-user-id` (the frontend sets this automatically after login).

## Tests

Run:

```bash
. .venv/bin/activate
pytest -q
```

Current status: `4 passed`.
