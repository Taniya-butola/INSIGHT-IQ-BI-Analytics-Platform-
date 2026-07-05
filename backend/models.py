from datetime import datetime, timezone
from extensions import db, bcrypt


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    company_name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # 'user' | 'admin'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    datasets = db.relationship(
        "Dataset", backref="owner", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "company_name": self.company_name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Dataset(db.Model):
    __tablename__ = "datasets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    file_extension = db.Column(db.String(10), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)

    row_count = db.Column(db.Integer, nullable=True)
    column_count = db.Column(db.Integer, nullable=True)
    columns_preview = db.Column(db.JSON, nullable=True)  # list of column names + dtypes

    status = db.Column(
        db.String(20), nullable=False, default="uploaded"
    )  # uploaded -> validated -> cleaned -> analyzed -> failed

    chat_messages = db.relationship(
        "ChatMessage", backref="dataset", lazy=True, cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    # --- Phase 2: validation ---
    validation_report = db.Column(db.JSON, nullable=True)
    validated_at = db.Column(db.DateTime, nullable=True)

    # --- Phase 2: cleaning ---
    cleaning_summary = db.Column(db.JSON, nullable=True)
    cleaned_filename = db.Column(db.String(255), nullable=True)
    cleaned_row_count = db.Column(db.Integer, nullable=True)
    cleaned_column_count = db.Column(db.Integer, nullable=True)
    cleaned_at = db.Column(db.DateTime, nullable=True)

    # --- Phase 3: exploratory data analysis ---
    eda_report = db.Column(db.JSON, nullable=True)
    eda_at = db.Column(db.DateTime, nullable=True)

    # --- Phase 5: predictive analytics ---
    predictive_report = db.Column(db.JSON, nullable=True)
    predictive_at = db.Column(db.DateTime, nullable=True)

    # --- Phase 6: business insights ---
    insights_report = db.Column(db.JSON, nullable=True)
    insights_at = db.Column(db.DateTime, nullable=True)

    uploaded_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "file_extension": self.file_extension,
            "file_size_bytes": self.file_size_bytes,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns_preview": self.columns_preview,
            "status": self.status,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "cleaned_at": self.cleaned_at.isoformat() if self.cleaned_at else None,
            "cleaned_row_count": self.cleaned_row_count,
            "cleaned_column_count": self.cleaned_column_count,
            "eda_at": self.eda_at.isoformat() if self.eda_at else None,
            "predictive_at": self.predictive_at.isoformat() if self.predictive_at else None,
            "insights_at": self.insights_at.isoformat() if self.insights_at else None,
            "has_validation_report": self.validation_report is not None,
            "has_cleaning_summary": self.cleaning_summary is not None,
            "has_eda_report": self.eda_report is not None,
            "has_predictive_report": self.predictive_report is not None,
            "has_insights_report": self.insights_report is not None,
        }


class ChatMessage(db.Model):
    """A single turn in an 'Ask INSIGHT IQ' conversation about one dataset."""

    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=False, index=True)

    role = db.Column(db.String(10), nullable=False)  # 'user' | 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
