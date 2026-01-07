from datetime import datetime, timezone
from typing import List
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from lingual import db

user_languages = db.Table(
    'user_languages',
    db.metadata,
    db.Column('user_id', db.ForeignKey('user.id', ondelete="CASCADE"), primary_key=True),
    db.Column('language_id', db.ForeignKey('language.id', ondelete="CASCADE"), primary_key=True)
)

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    last_name: Mapped[str] = mapped_column(db.String(150), nullable=True)
    email: Mapped[str] = mapped_column(db.String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(256), nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    last_login: Mapped[datetime | None] = mapped_column(db.DateTime)

    languages: Mapped[List["Language"]] = relationship(
        secondary=user_languages, 
        back_populates="students",
        lazy="selectin"
    )

    # Logic: Secure Password Management
    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Logic: Representation for debugging
    def __repr__(self) -> str:
        return f"<User {self.email} ({len(self.languages)} languages)>"


class Language(db.Model):
    __tablename__ = "language"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(db.String(10), unique=True, index=True) # e.g., 'jp-JP'
    name: Mapped[str] = mapped_column(db.String(100), unique=True) # e.g., 'Japanese'

    students: Mapped[List["User"]] = relationship(
        secondary=user_languages, 
        back_populates="languages"
    )

    def __repr__(self) -> str:
        return f"<Language {self.code}>"
