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

    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="'[]'")
    last_language: Mapped[str | None] = mapped_column(db.String(10), nullable=True)

    def set_password(self, password: str):
        # Todo: add password strength validation
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

            # Dynamically create stats for the new language
            self.create_language_stats(language_code)

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
        self.remove_language_stats(language_code)

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

    def create_language_stats(self, language_code: str):
        # Dynamically create stats for any language
        if language_code == "jp":
            # Check if stats already exist for this user in the database
            existing_stats = db.session.query(JapaneseStats).filter_by(user_id=self.id).first()

            if not existing_stats:
                # If not found, create new stats for the user
                japanese_stats = JapaneseStats(user_id=self.id) # type: ignore
                db.session.add(japanese_stats) # Add to session so it gets an ID

    def remove_language_stats(self, language_code: str):
        # Dynamically remove stats for any language
        if language_code == "jp":
            jp_stats = getattr(self, "jp_stats", None)
            if jp_stats is not None:
                db.session.delete(jp_stats)  # type: ignore[arg-type]

    def get_language_stats(self, language_code: str):
        if not Languages.get_language_by_code(language_code):  # Validate language code
            raise ValueError(f"Language code '{language_code}' does not exist.")
        
        stats_attr = f"{language_code}_stats"
        
        return getattr(self, stats_attr, None)

    def reset_stats(self):
        # Reset all user stats related to language learning
        for lang_code in self.languages:
            self.remove_language_stats(lang_code)

    def delete(self):
        # Delete associated language stats first to maintain referential integrity
        for lang_code in self.languages:
            self.remove_language_stats(lang_code)
        db.session.delete(self)

    @staticmethod
    def verify_reset_token(token):
        s = URLSafe(current_app.config['SECRET_KEY'], salt='password-reset-token')
        try:
            data = s.loads(token)
            if datetime.now(timezone.utc).timestamp() > data['expires_at']:
                return None
            return db.session.get(User, data['user_id'])
        except Exception:
            return None

class LanguageStatsBase(db.Model):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class JapaneseStats(LanguageStatsBase):
    __tablename__ = "jp_stats"

    # Relationship back to User
    user = db.relationship(
        "User",
        backref=db.backref(
            "jp_stats",
            uselist=False,
            passive_deletes=True
        )
    )

    # recent_new_kanji will store the list of kanji characters the user has recently added
    # to their learned list which they haven't learned before. The order is static, showing
    # the most recently added kanji at the end of the list.
    kanji_learned: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="'[]'")

    # kanji_practised will store the list of kanji characters the user has practiced,
    # in the order they were last practiced. This allows features like "review old kanji"
    # or "see recently practiced kanji".
    kanji_practised: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="'[]'")

    def add_kanji_learned(self, kanji: str):
        """
        Add a kanji to the learned list if it's not already there.
        
        Results in the kanji being added to the end of the list, indicating it was recently learned.
        """
        if kanji not in self.kanji_learned:
            self.kanji_learned = self.kanji_learned + [kanji]

    def remove_kanji_learned(self, kanji: str):
        """
        Remove a kanji from the learned list if it exists.

        Args:
            kanji (str): The kanji character to be removed from the learned list.
        """
        if kanji in self.kanji_learned:
            self.kanji_learned = [k for k in self.kanji_learned if k != kanji]

    def get_kanji_learned(self) -> list[str]:
        """
        Retrieve the list of kanji characters that the user has learned.

        Returns:
            list[str]: A list of learned kanji characters.
        """
        return self.kanji_learned

    def add_kanji_practised(self, kanji: str):
        """
        Remove the kanji from the practised list if it already exists to avoid duplicates,
        then add it to the end of the practised list to indicate it was recently practiced.

        Args:
            kanji (str): The kanji character to be added to the practiced list.
        """
        practised_list = [k for k in self.kanji_practised if k != kanji]
        self.kanji_practised = practised_list + [kanji]

    def remove_kanji_practised(self, kanji: str):
        """
        Remove a kanji from the practiced list if it exists.

        Args:
            kanji (str): The kanji character to be removed from the practiced list.
        """
        if kanji in self.kanji_practised:
            self.kanji_practised = [k for k in self.kanji_practised if k != kanji]

    def get_kanji_practised(self) -> list[str]:
        """
        Retrieve the list of kanji characters that the user has practiced.
        
        More recently practiced kanji will be towards the end of the list.
        """
        return self.kanji_practised

    def is_kanji_practiced(self, kanji: str) -> bool:
        """
        Check if a kanji has been practiced.

        Args:
            kanji (str): The kanji character to check.
        """
        return kanji in self.kanji_practised

    def is_kanji_learned(self, kanji: str) -> bool:
        """
        Check if a kanji has been learned.

        Args:
            kanji (str): The kanji character to check.

        Returns:
            bool: True if the kanji is in the learned list, False otherwise.
        """
        return kanji in self.kanji_learned

    def clear_practised_kanji(self):
        """
        Clears the entire list of practiced kanji. 

        Warning: This will remove all kanji from the practiced list!
        """
        self.kanji_practised = list()

    def clear_kanji(self):
        """
        Clears the entire list of learned kanji. 

        Warning: This will remove all kanji from the learned list!
        """
        self.kanji_learned = list()
        self.kanji_practised = list()

    # --- Lessons ---
    
    # lessons_practised will store the list of lesson slugs the user has practiced,
    # in the order they were last practiced. A lesson is counted as practiced if 
    # the user has completed a quiz associated with that lesson.
    lessons_practised: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="'[]'")

    def add_lesson_practised(self, lesson_slug: str):
        """
        Adds a lesson slug to the practised list to track which lessons the user has practiced.
        """
        practised_list = [l for l in self.lessons_practised if l != lesson_slug]
        self.lessons_practised = practised_list + [lesson_slug]
    
    def get_lessons_practised(self) -> list:
        """ Returns a list of lesson slugs in order of last practised (bottom) """
        return self.lessons_practised

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "kanji_learned": self.kanji_learned,
            "kanji_practised": self.kanji_practised,
            "lessons_practised": self.lessons_practised,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
