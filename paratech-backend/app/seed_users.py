from sqlmodel import Session, select

from app.auth.models import User, UserRole
from app.auth.security import hash_password
from app.database import engine


def create_user_if_not_exists(
    full_name: str,
    email: str,
    password: str,
    role: UserRole,
):
    with Session(engine) as session:
        existing_user = session.exec(
            select(User).where(User.email == email)
        ).first()

        if existing_user:
            print(f"{email} already exists")
            return

        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )

        session.add(user)
        session.commit()

        print(f"Created {role.value}: {email}")


if __name__ == "__main__":
    create_user_if_not_exists(
        "Parapharmacy Owner",
        "owner@paratech.com",
        "owner123",
        UserRole.OWNER,
    )

    create_user_if_not_exists(
        "Pharmacist User",
        "pharmacist@paratech.com",
        "pharma123",
        UserRole.PHARMACIST,
    )

    create_user_if_not_exists(
        "Cashier User",
        "cashier@paratech.com",
        "cashier123",
        UserRole.CASHIER,
    )