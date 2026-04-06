from sqlalchemy import Column, DateTime, Boolean, func, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM
from typing import Dict, Any
from datetime import datetime
import uuid
from enum import Enum
from app.model.student_classification_model import Base

class WeeklyClassificationLabel(Enum):
    Excelling = "Excelling"
    Thriving = "Thriving"
    Struggling = "Struggling"
    InCrisis = "InCrisis"

class StudentWeeklyClassification(Base):
    __tablename__ = "student_weekly_classification"

    weekly_classification_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    student_id = Column(
        PG_UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    week_start = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    week_end = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    dominant_classification = Column(
        PG_ENUM(
            WeeklyClassificationLabel,
            name="student_weekly_classification_enum",
            create_type=True
        ),
        nullable=False,
    )

    is_flagged = Column(
        Boolean,
        server_default="false",
        nullable=False,
    )

    classified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    reason = Column(
        Text,
        nullable=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weekly_classification_id": str(self.weekly_classification_id) if self.weekly_classification_id else None,
            "student_id": str(self.student_id) if self.student_id else None,
            "week_start": self.week_start.isoformat() if isinstance(self.week_start, datetime) else None,
            "week_end": self.week_end.isoformat() if isinstance(self.week_end, datetime) else None,
            "dominant_classification": (self.dominant_classification.value if isinstance(self.dominant_classification, WeeklyClassificationLabel) else str(self.dominant_classification)) if self.dominant_classification is not None else None,
            "is_flagged": bool(self.is_flagged),
            "classified_at": self.classified_at.isoformat() if isinstance(self.classified_at, datetime) else None,
        }