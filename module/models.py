from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    id: Optional[int] = None
    username: str = ""
    full_name: str = ""
    password_hash: str = ""
    salt: str = ""
    is_active: int = 1
    created_at: Optional[str] = None
    last_login: Optional[str] = None


@dataclass
class Member:
    id: Optional[int] = None
    user_id: int = 0
    phone: str = ""
    join_date: Optional[str] = None
    status: str = "active"


@dataclass
class Role:
    id: Optional[int] = None
    role_name: str = ""
    description: str = ""


@dataclass
class Permission:
    id: Optional[int] = None
    permission_key: str = ""
    description: str = ""
