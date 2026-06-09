from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(func.lower(User.email) == email.lower()).first()

    def get_by_login(self, login: str) -> User | None:
        value = login.strip()
        if not value:
            return None
        return (
            self.db.query(User)
            .filter(or_(User.username == value, func.lower(User.email) == value.lower()))
            .first()
        )

    def list(self, *, role: str | None = None, status: str | None = None, is_active: bool | None = None) -> list[User]:
        query = self.db.query(User)
        if role:
            query = query.filter(User.role == role)
        if status:
            query = query.filter(User.status == status)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        return query.order_by(User.created_at.desc()).all()
