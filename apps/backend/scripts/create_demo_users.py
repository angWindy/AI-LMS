"""Create local/demo users for development deployments."""

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User, UserRole

DEMO_USERS = [
    ("admin@test.com", "Admin User", "admin"),
    ("teacher@test.com", "Teacher User", "instructor"),
    ("student@test.com", "Student User", "learner"),
]
DEMO_PASSWORD = "00000000"


def main() -> None:
    db = SessionLocal()
    try:
        for email, full_name, role in DEMO_USERS:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                print(f"- Already exists: {email}")
                continue

            user = User(
                email=email,
                full_name=full_name,
                password_hash=get_password_hash(DEMO_PASSWORD),
                role=UserRole(role),
                is_active=True,
            )
            db.add(user)
            print(f"+ Created: {email}")

        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
