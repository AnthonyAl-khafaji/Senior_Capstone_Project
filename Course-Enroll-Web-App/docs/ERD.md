# Database ERD

This ERD is generated from the SQLModel schema in `app/models.py`.

Legend:
- `PK` = Primary Key
- `FK` = Foreign Key
- `UK` = Unique Key

```mermaid
erDiagram
    USER {
        int id PK
        string first_name
        string last_name
        string email UK
        string password
        enum role
        datetime created_at
        datetime updated_at
    }

    STUDENT {
        int student_id PK
        int user_id FK UK
        string first_name
        string last_name
        string email UK
        string major
        string class_year
        datetime created_at
        datetime updated_at
    }

    INSTRUCTOR {
        int instructor_id PK
        int user_id FK UK
        string first_name
        string last_name
        string email UK
        string department
        string office_location
        datetime created_at
        datetime updated_at
    }

    COURSE {
        int course_id PK
        string course_name
        string department
        int credits
        int capacity
        int instructor_id FK
        string schedule_days
        string schedule_time
        string classroom_location
        datetime created_at
        datetime updated_at
    }

    ENROLLMENT {
        int enrollment_id PK
        int student_id FK
        int course_id FK
        date enrollment_date
        string status
        datetime created_at
        datetime updated_at
    }

    GRADE {
        int grade_id PK
        int student_id FK
        int course_id FK
        int instructor_id FK
        string grade
        date date_recorded
        datetime created_at
        datetime updated_at
    }

    USER ||--o| STUDENT : has_profile
    USER ||--o| INSTRUCTOR : has_profile
    INSTRUCTOR ||--o{ COURSE : teaches
    STUDENT ||--o{ ENROLLMENT : enrolls
    COURSE ||--o{ ENROLLMENT : includes
    STUDENT ||--o{ GRADE : receives
    COURSE ||--o{ GRADE : for
    INSTRUCTOR ||--o{ GRADE : records
```
