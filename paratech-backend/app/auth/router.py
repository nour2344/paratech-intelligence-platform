from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.auth.schemas import AuthResponse, LoginRequest, RegisterRequest
from app.auth.service import login_user, register_client
from app.database import get_session

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
def register(data: RegisterRequest, session: Session = Depends(get_session)):
    return register_client(data, session)


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, session: Session = Depends(get_session)):
    return login_user(data, session)