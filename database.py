from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, UniqueConstraint
import datetime as dt
import secrets


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    # Primary fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(15), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(250), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    student: Mapped[int] = mapped_column(Integer, nullable=False)
    agreement: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(String(250), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(250), nullable=False)
    
    # Enhanced profile fields
    birthday: Mapped[str] = mapped_column(String(20), nullable=True)
    pronouns: Mapped[str] = mapped_column(String(50), nullable=True)
    location: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Password reset functionality
    temp_password: Mapped[str] = mapped_column(String(250), nullable=True)
    temp_password_expires: Mapped[str] = mapped_column(String(250), nullable=True)
    is_using_temp_password: Mapped[int] = mapped_column(Integer, default=0)
    
    # Admin status
    admin: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Login tracking
    last_login_at: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        """Convert to dictionary format"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    def create(cls, username, email, hashed_password, is_student):
        """Create new user"""
        now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return cls(
            username=username,
            email=email,
            password=hashed_password,
            student=int(is_student),
            agreement=1,
            created_at=now,
            updated_at=now,
            is_using_temp_password=0,
            admin=0
        )

    def generate_temp_password(self):
        """Generate temporary password"""
        temp_password = secrets.token_urlsafe(12)
        expires = (dt.datetime.now() + dt.timedelta(hours=24)).strftime('%Y-%m-%d %H:%M:%S')
        return temp_password, expires


class Question(db.Model):
    """Question model"""
    __tablename__ = 'questions'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True)
    category: Mapped[str] = mapped_column(String(250), nullable=False)
    depth: Mapped[str] = mapped_column(String(250), nullable=False)
    stage: Mapped[str] = mapped_column(String(250), nullable=False)
    question: Mapped[str] = mapped_column(String(5000), nullable=False, unique=True)
    exclude_for_students: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 1 if should hide from students
    created_at: Mapped[str] = mapped_column(String(250), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(250), nullable=False)

    def to_dict(self):
        """Convert to dictionary format"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


class UserAnswer(db.Model):
    """User answer model"""
    __tablename__ = 'user_answers'
    __table_args__ = (
        UniqueConstraint('user_id', 'question_id', name='unique_user_question'),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    student: Mapped[int] = mapped_column(Integer, nullable=False)
    question: Mapped[str] = mapped_column(String(5000), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=True)
    is_public: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String(250), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(250), nullable=False)

    def to_dict(self):
        """Convert to dictionary format"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    def create(cls, user_id, question_id, question_text, answer_text, is_student, is_public=1):
        """Create new answer"""
        now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return cls(
            user_id=user_id,
            question_id=question_id,
            student=is_student,
            question=question_text,
            answer=answer_text,
            is_public=is_public,
            created_at=now,
            updated_at=now
        )


class DeletedUser(db.Model):
    """Deleted user information model (for audit purposes)"""
    __tablename__ = 'deleted_users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    deletion_date: Mapped[str] = mapped_column(String(250), nullable=False)
    deletion_reason: Mapped[str] = mapped_column(String(500), nullable=True)


class Report(db.Model):
    """Report (content reporting) model"""
    __tablename__ = 'reports'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reported_answer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='pending')
    created_at: Mapped[str] = mapped_column(String(250), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(250), nullable=False)

    def to_dict(self):
        """Convert to dictionary format"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

    @classmethod
    def create(cls, reporter_user_id, reported_answer_id, reason=None):
        """Create new report"""
        now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return cls(
            reporter_user_id=reporter_user_id,
            reported_answer_id=reported_answer_id,
            reason=reason,
            status='pending',
            created_at=now,
            updated_at=now
        )


def init_db(app):
    """Initialize database"""
    db.init_app(app)
    
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created/verified successfully")
        except Exception as e:
            print(f"⚠️ Database initialization warning: {e}")
            pass
