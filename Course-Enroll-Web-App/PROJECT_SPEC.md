# Project Specification: Campus Portal

Last updated: 2026-03-07

## 1. Purpose and Scope

This project is a FastAPI + SQLModel web application for role-based academic operations across three user types:

- Student
- Instructor
- Admin

The current implementation delivers a login-first system with role-specific dashboards and CRUD workflows for courses, enrollment, grading, instructor assignment, and scheduling.

This document is the canonical handoff/reference for future sessions.

## 2. What Has Been Implemented

### 2.1 Major Functional Milestones Completed

1. Replaced the original basic enrollment app with a role-based architecture.
2. Introduced authentication endpoints (`signup`, `login`) and a current-user endpoint (`/me`).
3. Added normalized domain schema:
   - `User`
   - `Student`
   - `Instructor`
   - `Course`
   - `Enrollment`
   - `Grade`
4. Implemented role-gated backend endpoints for student/instructor/admin workflows.
5. Rebuilt frontend to be login-first with role-switched dashboards.
6. Added startup schema compatibility handling for legacy SQLite layouts.
7. Updated Instructor Management workflow to update existing instructors by `instructor_id` for `department` and `office_location`.
8. Removed old admin API endpoint that created instructors directly (`POST /admin/instructors`).
9. Updated tests and README to align with new system.

### 2.2 Operational Changes Applied During Debugging

1. Fixed runtime schema mismatch (`table course has no column named course_name`) by:
   - adding schema compatibility detection in `app/database.py`
   - auto-dropping/recreating tables when legacy schema is detected
2. Explicitly reset database by deleting `database.db` and recreating schema from code.
3. Repeatedly restarted the server to apply backend/frontend changes.

## 3. Current Architecture

### 3.1 Backend Stack

- Framework: FastAPI
- ORM/Model Layer: SQLModel (SQLAlchemy-based)
- Database: SQLite (`database.db` in repo root)
- App entrypoint: `app/main.py`

### 3.2 Frontend Stack

- Static HTML/CSS/JavaScript served by FastAPI
- Entry page: `app/static/index.html`
- UI behavior: `app/static/app.js`
- Styling: `app/static/style.css`

### 3.3 Key Files

- `app/main.py`: API routes, auth header handling, role checks
- `app/models.py`: SQLModel table definitions and role enum
- `app/crud.py`: business/data operations
- `app/database.py`: engine/session + schema compatibility logic
- `app/static/index.html`: auth + role dashboards
- `app/static/app.js`: all frontend API integration and UI actions
- `tests/test_api.py`: regression tests for auth, enrollment, capacity, role restrictions
- `README.md`: user-facing quick-start + endpoint summary

## 4. Data Model Specification (Current)

Defined in `app/models.py`.

### 4.1 `Role` Enum

- `student`
- `instructor`
- `admin`

### 4.2 `User`

- `id` (PK)
- `first_name`
- `last_name`
- `email` (unique)
- `password` (plaintext currently)
- `role` (`Role`)
- `created_at`
- `updated_at`

### 4.3 `Student`

- `student_id` (PK)
- `user_id` (FK -> `user.id`, unique)
- `first_name`
- `last_name`
- `email` (unique)
- `major` (nullable)
- `class_year` (nullable)
- `created_at`
- `updated_at`

### 4.4 `Instructor`

- `instructor_id` (PK)
- `user_id` (FK -> `user.id`, unique)
- `first_name`
- `last_name`
- `email` (unique)
- `department` (nullable)
- `office_location` (nullable)
- `created_at`
- `updated_at`

### 4.5 `Course`

- `course_id` (PK)
- `course_name`
- `department`
- `credits`
- `capacity`
- `instructor_id` (nullable FK -> `instructor.instructor_id`)
- `schedule_days` (nullable)
- `schedule_time` (nullable)
- `classroom_location` (nullable)
- `created_at`
- `updated_at`

### 4.6 `Enrollment`

- `enrollment_id` (PK)
- `student_id` (FK -> `student.student_id`)
- `course_id` (FK -> `course.course_id`)
- `enrollment_date`
- `status` (default `enrolled`)
- `created_at`
- `updated_at`

### 4.7 `Grade`

- `grade_id` (PK)
- `student_id` (FK -> `student.student_id`)
- `course_id` (FK -> `course.course_id`)
- `instructor_id` (FK -> `instructor.instructor_id`)
- `grade`
- `date_recorded`
- `created_at`
- `updated_at`

## 5. Authentication and Authorization Design

### 5.1 Authentication

- Login endpoint validates against `User` table email/password.
- Session model is simplified:
  - frontend stores returned user object in `localStorage`
  - every authenticated request sends header `x-user-id`

### 5.2 Authorization

- Backend loads user from `x-user-id` (`get_current_user`).
- `require_role` enforces allowed roles per endpoint.
- Unauthorized access returns `401` or `403`.

### 5.3 Security Note

- Passwords are currently stored in plaintext.
- This is suitable for local/dev demo only.
- Planned improvement: password hashing + token-based auth (JWT/session).

## 6. API Specification (Current Contract)

All routes are in `app/main.py`.

### 6.1 Public Routes

- `GET /` -> serves `index.html`
- `POST /auth/signup`
  - body: `{ first_name, last_name, email, password, role }`
- `POST /auth/login`
  - body: `{ email, password }`
- `GET /courses`

### 6.2 Authenticated Shared Route

- `GET /me` (requires `x-user-id`)

### 6.3 Student Routes

- `POST /enrollments?course_id={id}`
- `DELETE /enrollments?course_id={id}`
- `GET /student/courses`
- `GET /student/grades`
- `GET /student/schedule`

### 6.4 Instructor Routes

- `GET /instructor/courses`
- `GET /instructor/courses/{course_id}/roster`
- `POST /instructor/grades`
  - body: `{ student_id, course_id, grade }`
- `DELETE /instructor/grades/{grade_id}`

### 6.5 Admin Routes

- `GET /students`
- `GET /instructors`
- `POST /courses`
  - body: `{ course_name, department, credits, capacity }`
- `PUT /courses/{course_id}`
- `DELETE /courses/{course_id}`
- `PUT /admin/instructors/{instructor_id}`
  - full instructor + account profile update (legacy admin endpoint still present)
- `PATCH /admin/instructors/{instructor_id}/info`
  - body: `{ department?, office_location? }`
  - added to support "update existing instructor by ID" workflow
- `DELETE /admin/instructors/{instructor_id}`
- `POST /admin/courses/{course_id}/assign-instructor`
  - body: `{ instructor_id }`
- `POST /admin/courses/{course_id}/schedule`
  - body: `{ schedule_days, schedule_time, classroom_location }`

## 7. Frontend Behavior Specification

Defined in `app/static/index.html` and `app/static/app.js`.

### 7.1 Entry and Session

- App opens on auth screen with side-by-side Login/Signup sections.
- After login:
  - user object saved in `localStorage` (`portalUser`)
  - app shows role dashboard
- On refresh:
  - app calls `/me` to validate persisted user
- Logout:
  - clears `portalUser`
  - returns to auth view

### 7.2 Student Dashboard

Sections:

1. Course Catalog
   - loads `/courses`
   - per-course enroll button -> `POST /enrollments?course_id=...`
2. My Courses
   - loads `/student/courses`
   - per-course drop button -> `DELETE /enrollments?course_id=...`
3. Grades
   - loads `/student/grades`
4. Schedule
   - loads `/student/schedule`

### 7.3 Instructor Dashboard

Sections:

1. My Courses (`GET /instructor/courses`)
2. Course Roster (`GET /instructor/courses/{id}/roster`)
3. Grade Management
   - create/update: `POST /instructor/grades`
   - delete: `DELETE /instructor/grades/{grade_id}`

### 7.4 Admin Dashboard

Sections:

1. Course Management
   - create/update/delete/list course
2. Instructor Management
   - update existing instructor info by ID (`PATCH /admin/instructors/{id}/info`)
   - remove instructor by ID (`DELETE /admin/instructors/{id}`)
3. Instructor Assignment
   - assign instructor to course
4. Schedule Management
   - set days/time/classroom for a course

## 8. Business Rules and Behaviors

1. Signup creates `User` and role-specific profile rows:
   - student signup -> creates `Student`
   - instructor signup -> creates `Instructor`
   - admin signup -> user only
2. Email uniqueness is enforced at least at `User` table level.
3. Enrolling checks:
   - student exists
   - course exists
   - duplicate enrollment returns existing row (idempotent behavior)
   - capacity not exceeded
4. Deleting instructor:
   - unassigns instructor from courses
   - deletes that instructor's grades
   - deletes instructor profile and linked user row
5. Course delete cascades manually in code for related `Enrollment` and `Grade` rows.

## 9. Database Lifecycle and Compatibility

Defined in `app/database.py`.

- On startup, `init_db()` runs.
- `_schema_is_compatible()` inspects existing `course` table columns.
- If legacy schema is detected, app drops all tables and recreates from model metadata.
- Intended for local development continuity after breaking schema changes.

## 10. Testing Status

Test file: `tests/test_api.py`

Current automated coverage includes:

1. signup/login/me
2. admin course creation + student enroll/drop flow
3. capacity limit rejection
4. role restriction for student trying to create course

Latest status observed: `4 passed`.

## 11. Known Gaps / Risks

1. Plaintext passwords (security risk outside local dev).
2. Header-based pseudo-session (`x-user-id`) is easy to spoof.
3. No migration framework (Alembic) yet; startup fallback may drop data on incompatible schema.
4. Tests do not yet cover all instructor/admin branches (assignment, schedule, roster authorization edge cases).
5. The older full-profile admin update endpoint (`PUT /admin/instructors/{instructor_id}`) still exists alongside new info-only patch endpoint.

## 12. Recommended Next Steps

1. Implement password hashing (e.g., `passlib`) and token/session auth.
2. Introduce migration tooling (Alembic) and retire auto-drop schema fallback.
3. Expand tests for:
   - instructor authorization on foreign course IDs
   - admin assignment/schedule workflows
   - grade lifecycle edge cases
4. Decide whether to deprecate/remove `PUT /admin/instructors/{instructor_id}` if only info-only updates should remain.
5. Add seed data script for demo usage.

## 13. Runbook

### 13.1 Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 13.2 Open

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/docs`

### 13.3 Reset Local Database

```bash
rm -f database.db
```

Then restart the app.

### 13.4 Run Tests

```bash
. .venv/bin/activate
pytest -q
```

## 14. Session Notes Summary (Concise)

- System moved from simple enrollment CRUD to full role-based portal.
- Frontend rebuilt to login-first dashboard model.
- Internal server error from schema mismatch was resolved.
- Instructor management behavior changed per request:
  - no admin creation endpoint
  - update existing instructor info by ID using department/office fields.
