from datetime import datetime, timezone
from flask import current_app
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column
from itsdangerous import URLSafeTimedSerializer as URLSafe
from werkzeug.security import generate_password_hash, check_password_hash
from lingual import db
from lingual.utils.languages import Language, Languages

from sqlalchemy.types import JSON

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(db.String(150), nullable=False)
    email: Mapped[str] = mapped_column(db.String(150), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(256), nullable=False)

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    last_login: Mapped[datetime | None] = mapped_column(db.DateTime)

    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    last_language: Mapped[str | None] = mapped_column(db.String(10), nullable=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def add_language(self, language_code: str):
        if Languages.get_language_by_code(language_code) is None:
            raise ValueError(f"Language code '{language_code}' does not exist.")
        
        if not self.languages:
            self.languages = []

        if language_code not in self.languages:
            self.languages.append(language_code)

    def get_last_language(self) -> Language | None:
        if self.last_language:
            return Languages.get_language_by_code(self.last_language)
        return None
    
    def set_last_language(self, language_code: str):
        if Languages.get_language_by_code(language_code) is None:
            raise ValueError(f"Language code '{language_code}' does not exist.")
        
        self.last_language = language_code

    def remove_language(self, language_code: str):
        if language_code in self.languages:
            self.languages.remove(language_code)

    def get_language_codes(self) -> list[str]:
        return self.languages

    def get_languages(self) -> list['Language']:
        langs = []
        if self.languages:
            for code in self.languages:
                lang = Languages.get_language_by_code(code)
                if lang:
                    langs.append(lang)
        return langs

    def __repr__(self) -> str:
        return f"<User {self.email} ({len(self.languages)} languages)>"

    def get_reset_token(self, expires_seconds=1800) -> str:
        from datetime import timedelta
        s = URLSafe(current_app.config['SECRET_KEY'], salt='password-reset-token')
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)).timestamp()
        return s.dumps({'user_id': self.id, 'expires_at': expires_at})
    
    @staticmethod
    def verify_reset_token(token):
        s = URLSafe(current_app.config['SECRET_KEY'], salt='password-reset-token')
        try:
            data = s.loads(token)
            if datetime.now(timezone.utc).timestamp() > data['expires_at']:
                return None
            return User.query.get(data['user_id'])
        except Exception:
            return None
        
    