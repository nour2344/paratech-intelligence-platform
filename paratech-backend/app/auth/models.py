from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    CLIENT = "CLIENT"
    OWNER = "OWNER"
    PHARMACIST = "PHARMACIST"
    CASHIER = "CASHIER"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)

    full_name: str
    email: str = Field(index=True, unique=True)
    hashed_password: str

    role: UserRole = Field(default=UserRole.CLIENT)

    is_active: bool = Field(default=True)