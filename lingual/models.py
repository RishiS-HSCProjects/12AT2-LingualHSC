from datetime import datetime, timezone
import hashlib
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

    languages: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    last_language: Mapped[str | None] = mapped_column(db.String(10), nullable=True)

    def set_password(self, password: str):
        # Todo: add password strength validation
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def add_language(self, language_code: str):
        if (Languages.get_language_by_code(language_code)) is None:
            raise ValueError(f"Language code '{language_code}' does not exist.")
        
        if language_code == Languages.TUTORIAL.obj().code:
            raise ValueError("Cannot add tutorial as a language.")
        
        if not self.languages:
            self.languages = []

        if language_code not in self.languages:
            # Reassign list so SQLAlchemy tracks JSON column changes reliably.
            # Fixed an issue where appending to the list directly did not trigger SQLAlchemy change tracking, resulting in language deletions not being reflected on the database.
            # Includes issue with remove_language where the list was being modified in place instead of reassigned, causing the same problem. Both add_language and remove_language now reassign the entire list to ensure changes are detected and saved to the database correctly. This is a common pattern when working with mutable types like lists in SQLAlchemy JSON columns. 16/03/26
            # TODO: Document 16/03/26
            self.languages = [*self.languages, language_code]

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
            self.languages = [code for code in self.languages if code != language_code]
        if self.last_language == language_code:
            self.last_language = None
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
        pwd_sig = hashlib.sha256(self.password_hash.encode('utf-8')).hexdigest() # Create a signature based on the current password hash to invalidate tokens if the password changes
        return s.dumps({'user_id': self.id, 'expires_at': expires_at, 'pwd_sig': pwd_sig})

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
            self.create_language_stats(lang_code)

    def delete(self):
        # Delete associated language stats first to maintain referential integrity
        for lang_code in self.languages:
            self.remove_language_stats(lang_code)
        db.session.delete(self)
    
    def login(self):
        from flask_login import login_user
        login_user(self)

    @staticmethod
    def verify_reset_token(token):
        s = URLSafe(current_app.config['SECRET_KEY'], salt='password-reset-token')
        try:
            data = s.loads(token)
            if datetime.now(timezone.utc).timestamp() > data['expires_at']:
                return None

            user_id = data.get('user_id')
            token_signature = data.get('pwd_sig')

            if not isinstance(user_id, int) or not isinstance(token_signature, str):
                # If the token data is not in the expected format, return None
                return None

            user = db.session.get(User, user_id)
            if not user: # If user not found, return None
                return None

            expected_signature = hashlib.sha256(user.password_hash.encode('utf-8')).hexdigest()
            if token_signature != expected_signature:
                # If the password signature does not match, it means the password has changed since the token was issued, so we should invalidate the token and return None
                return None

            return user # Return the user if everything checks out
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

    kanji_learned: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")
    """ Store the list of kanji characters the user has learned. The order is static,
        showing the most recently added kanji at the end of the list. """

    # kanji_practised will store the list of kanji characters the user has practiced,
    # in the order they were last practiced. This allows features like "review old kanji"
    # or "see recently practiced kanji".
    kanji_practised: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")

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

    # --- Grammar Lessons ---
    
    # grammar_practised will store the list of lesson slugs the user has practiced,
    # in the order they were last practiced. A lesson is counted as practiced if 
    # the user has completed a quiz associated with that lesson.
    grammar_practised: Mapped[list[str]] = mapped_column(JSON, default=list, server_default="[]")

    def add_lesson_practised(self, lesson_slug: str):
        """
        Adds a lesson slug to the practised list to track which lessons the user has practiced.
        """
        practised_list = [l for l in self.grammar_practised if l != lesson_slug] # Reconstruct
        self.grammar_practised = practised_list + [lesson_slug] # Append lesson slug to end of list
    
    def get_grammar_practised(self) -> list:
        """ Returns a list of lesson slugs in order of last practised (bottom) """
        return self.grammar_practised

    def clear_grammar_practised(self) -> None:
        self.grammar_practised = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "kanji_learned": self.kanji_learned,
            "kanji_practised": self.kanji_practised,
            "grammar_practised": self.grammar_practised,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
