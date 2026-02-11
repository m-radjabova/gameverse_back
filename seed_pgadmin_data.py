from datetime import datetime, timedelta, timezone

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    Assignment,
    AssignmentSubmission,
    Category,
    Course,
    Lesson,
    User,
)


def get_or_create(db, model, lookup: dict, create_data: dict):
    instance = db.query(model).filter_by(**lookup).first()
    if instance:
        return instance, False

    payload = {**lookup, **create_data}
    instance = model(**payload)
    db.add(instance)
    db.flush()
    return instance, True


def seed_data():
    db = SessionLocal()
    created = {
        "users": 0,
        "categories": 0,
        "courses": 0,
        "lessons": 0,
        "assignments": 0,
        "submissions": 0,
    }

    try:
        users_payload = [
            {
                "username": "student_demo",
                "email": "student_demo@example.com",
                "password": "DemoPass123",
                "roles": ["user"],
                "avatar": None,
            },
            {
                "username": "student_ali",
                "email": "student_ali@example.com",
                "password": "DemoPass123",
                "roles": ["user"],
                "avatar": None,
            },
            {
                "username": "student_lola",
                "email": "student_lola@example.com",
                "password": "DemoPass123",
                "roles": ["user"],
                "avatar": None,
            },
            {
                "username": "teacher_demo",
                "email": "teacher_demo@example.com",
                "password": "DemoPass123",
                "roles": ["teacher"],
                "avatar": None,
            },
            {
                "username": "admin_demo",
                "email": "admin_demo@example.com",
                "password": "DemoPass123",
                "roles": ["admin"],
                "avatar": None,
            },
        ]

        users = {}
        for item in users_payload:
            user, is_created = get_or_create(
                db,
                User,
                lookup={"username": item["username"]},
                create_data={
                    "email": item["email"],
                    "hashed_password": hash_password(item["password"]),
                    "roles": item["roles"],
                    "avatar": item["avatar"],
                },
            )
            users[item["username"]] = user
            created["users"] += int(is_created)

        categories_payload = [
            {
                "name": "Python Backend",
                "description": "FastAPI va PostgreSQL bo'yicha amaliy kurslar",
                "icon": None,
            },
            {
                "name": "Frontend React",
                "description": "React, TypeScript va API integratsiya",
                "icon": None,
            },
            {
                "name": "DevOps Basics",
                "description": "Docker, CI/CD va deploy asoslari",
                "icon": None,
            },
            {
                "name": "Data Engineering",
                "description": "ETL, Airflow va ma'lumotlar pipeline",
                "icon": None,
            },
            {
                "name": "Mobile Development",
                "description": "Flutter va mobil ilova arxitekturasi",
                "icon": None,
            },
        ]

        categories = {}
        for item in categories_payload:
            category, is_created = get_or_create(
                db,
                Category,
                lookup={"name": item["name"]},
                create_data={
                    "description": item["description"],
                    "icon": item["icon"],
                },
            )
            categories[item["name"]] = category
            created["categories"] += int(is_created)

        courses_payload = [
            {
                "category_name": "Python Backend",
                "title": "FastAPI Zero to Hero",
                "description": "REST API, auth va deploy mavzulari",
                "image": None,
                "level": "beginner",
                "price": 0,
                "duration": 480,
                "rating": 5,
            },
            {
                "category_name": "Frontend React",
                "title": "React Practical",
                "description": "Komponentlar, routing va state management",
                "image": None,
                "level": "intermediate",
                "price": 120,
                "duration": 600,
                "rating": 4,
            },
            {
                "category_name": "Frontend React",
                "title": "UI/UX Design Masterclass",
                "description": "UI va UX prinsiplaridan to real loyiha prototipigacha",
                "image": None,
                "level": "beginner",
                "price": 89,
                "duration": 300,
                "rating": 5,
            },
            {
                "category_name": "DevOps Basics",
                "title": "Docker from Scratch",
                "description": "Containerlar va production workflow",
                "image": None,
                "level": "beginner",
                "price": 90,
                "duration": 420,
                "rating": 5,
            },
            {
                "category_name": "Data Engineering",
                "title": "Airflow ETL Mastery",
                "description": "DAG, scheduler va ETL amaliyoti",
                "image": None,
                "level": "advanced",
                "price": 150,
                "duration": 700,
                "rating": 4,
            },
            {
                "category_name": "Mobile Development",
                "title": "Flutter App Builder",
                "description": "UI, state va API bilan ishlash",
                "image": None,
                "level": "intermediate",
                "price": 110,
                "duration": 560,
                "rating": 5,
            },
            {
                "category_name": "Mobile Development",
                "title": "React Native Mobile Development",
                "description": "React Native bilan mobil ilova yaratish va publish",
                "image": None,
                "level": "beginner",
                "price": 94,
                "duration": 240,
                "rating": 5,
            },
        ]

        courses = {}
        for item in courses_payload:
            category = categories[item["category_name"]]
            course, is_created = get_or_create(
                db,
                Course,
                lookup={"category_id": category.id, "title": item["title"]},
                create_data={
                    "description": item["description"],
                    "image": item["image"],
                    "level": item["level"],
                    "price": item["price"],
                    "duration": item["duration"],
                    "rating": item["rating"],
                },
            )
            courses[item["title"]] = course
            created["courses"] += int(is_created)

        video_urls = [
            "https://download.samplelib.com/mp4/sample-5s.mp4",
            "https://download.samplelib.com/mp4/sample-10s.mp4",
            "https://download.samplelib.com/mp4/sample-15s.mp4",
            "https://download.samplelib.com/mp4/sample-20s.mp4",
            "https://download.samplelib.com/mp4/sample-30s.mp4",
            "https://download.samplelib.com/mp4/sample-40s.mp4",
            "https://download.samplelib.com/mp4/sample-1mb.mp4",
            "https://download.samplelib.com/mp4/sample-2mb.mp4",
            "https://download.samplelib.com/mp4/sample-3mb.mp4",
            "https://download.samplelib.com/mp4/sample-5mb.mp4",
        ]

        lesson_topics_by_course = {
            "FastAPI Zero to Hero": [
                "Kirish va loyiha struktura",
                "Router va endpointlar",
                "Pydantic schema bilan validatsiya",
                "SQLAlchemy model asoslari",
                "CRUD service qatlami",
                "JWT autentifikatsiya",
                "Role-based authorization",
                "Pagination va filter",
                "Alembic migration",
                "Deploy va production sozlama",
            ],
            "React Practical": [
                "React Setup va JSX",
                "Komponentlar va props",
                "State va event handling",
                "Hooklar bilan ishlash",
                "React Router",
                "Form validatsiya",
                "Axios bilan API chaqirish",
                "Context API",
                "Reusable UI komponentlar",
                "Build va deploy",
            ],
            "UI/UX Design Masterclass": [
                "Introduction to Design",
                "Design Thinking asoslari",
                "User Persona yaratish",
                "User Journey Map",
                "Wireframe tayyorlash",
                "Color Theory va typography",
                "Design System asoslari",
                "Prototyping amaliyoti",
                "Usability testing",
                "Portfolio case study",
            ],
            "Docker from Scratch": [
                "Docker Fundamentals",
                "Image va layer tushunchasi",
                "Dockerfile best practice",
                "Container networking",
                "Volume va data persist",
                "Docker Compose",
                "Multi-stage build",
                "Environment variables",
                "Registry bilan ishlash",
                "Production container strategy",
            ],
            "Airflow ETL Mastery": [
                "Airflow Intro",
                "DAG arxitekturasi",
                "Operatorlar bilan ishlash",
                "Task dependency",
                "XCom va parametrlar",
                "Schedule va trigger",
                "Retry va alert sozlamasi",
                "ETL pipeline dizayni",
                "Monitoring va logging",
                "Production best practice",
            ],
            "Flutter App Builder": [
                "Flutter Widgets",
                "Layout va navigation",
                "State management",
                "Form input va validation",
                "REST API integratsiya",
                "Local storage",
                "Authentication flow",
                "Responsive UI",
                "Performance optimization",
                "Release build",
            ],
            "React Native Mobile Development": [
                "React Native Intro",
                "Environment setup",
                "Core components",
                "Navigation stack",
                "State management",
                "API integration",
                "Authentication flow",
                "Local storage",
                "Performance tuning",
                "Build and release",
            ],
        }

        lessons_payload = []
        for course_title, topics in lesson_topics_by_course.items():
            for idx, topic in enumerate(topics, start=1):
                lessons_payload.append(
                    {
                        "course_title": course_title,
                        "order": idx,
                        "title": topic,
                        "description": f"{course_title} kursi uchun {topic} darsi.",
                        "is_free": idx <= 2,
                        "video_url": video_urls[idx - 1],
                        "duration_sec": 600 + (idx * 60),
                    }
                )

        lessons = {}
        for item in lessons_payload:
            course = courses[item["course_title"]]
            lesson, is_created = get_or_create(
                db,
                Lesson,
                lookup={"course_id": course.id, "order": item["order"]},
                create_data={
                    "title": item["title"],
                    "description": item["description"],
                    "is_free": item["is_free"],
                    "video_url": item["video_url"],
                    "duration_sec": item["duration_sec"],
                },
            )
            lessons[f"{item['course_title']}#{item['order']}"] = lesson
            created["lessons"] += int(is_created)

        assignments_payload = []
        for lesson_key, lesson in lessons.items():
            for order in range(1, 4):
                assignments_payload.append(
                    {
                        "lesson_key": lesson_key,
                        "order": order,
                        "title": f"{lesson.title} - Vazifa {order}",
                        "description": f"{lesson.title} bo'yicha {order}-amaliy topshiriq.",
                        "max_score": 100,
                        "is_required": True,
                        "due_days": 5 + order,
                    }
                )

        assignments = []
        for item in assignments_payload:
            lesson = lessons[item["lesson_key"]]
            assignment, is_created = get_or_create(
                db,
                Assignment,
                lookup={"lesson_id": lesson.id, "order": item["order"]},
                create_data={
                    "title": item["title"],
                    "description": item["description"],
                    "due_at": datetime.now(timezone.utc) + timedelta(days=item["due_days"]),
                    "max_score": item["max_score"],
                    "is_required": item["is_required"],
                },
            )
            assignments.append(assignment)
            created["assignments"] += int(is_created)

        submission_targets = [
            ("student_demo", 0),
            ("student_ali", 1),
            ("student_lola", 2),
            ("student_demo", 3),
            ("student_ali", 4),
        ]

        for idx, (username, assignment_index) in enumerate(submission_targets, start=1):
            assignment = assignments[assignment_index]
            user = users[username]
            _, is_created = get_or_create(
                db,
                AssignmentSubmission,
                lookup={"assignment_id": assignment.id, "user_id": user.id},
                create_data={
                    "text_answer": f"Submission #{idx} by {username}",
                    "file_url": None,
                    "status": "submitted",
                    "score": None,
                },
            )
            created["submissions"] += int(is_created)

        db.commit()

        print("Seed yakunlandi.")
        print(f"Yaratildi: {created}")
        print("Demo loginlar:")
        print("- student_demo / DemoPass123")
        print("- student_ali / DemoPass123")
        print("- student_lola / DemoPass123")
        print("- teacher_demo / DemoPass123")
        print("- admin_demo / DemoPass123")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
