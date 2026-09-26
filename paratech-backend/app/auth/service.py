from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.auth.models import User, UserRole
from app.auth.schemas import LoginRequest, RegisterRequest
from app.auth.security import create_access_token, hash_password, verify_password


def build_auth_response(user: User):
    role_value = user.role.value if hasattr(user.role, "value") else user.role

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": role_value,
            "user_id": user.id,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": role_value,
        },
    }


def register_client(data: RegisterRequest, session: Session):
    existing_user = session.exec(
        select(User).where(User.email == data.email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    user = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=UserRole.CLIENT,
        is_active=True,
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return build_auth_response(user)


def login_user(data: LoginRequest, session: Session):
    user = session.exec(
        select(User).where(User.email == data.email)
    ).first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return build_auth_response(user)