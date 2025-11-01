from enum import Enum
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM, JSONB
from sqlalchemy.orm import declarative_base
import uuid
from typing import Dict, Any
from datetime import datetime

Base = declarative_base()

class ClassificationLabel(Enum):
    Excelling = "Excelling"
    Thriving = "Thriving"
    Struggling = "Struggling"
    InCrisis = "InCrisis"

class StudentClassification(Base):
    __tablename__ = "student_classification"

    classification_id = Column(
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

    classification = Column(
        PG_ENUM(
            ClassificationLabel,
            name="student_classification_enum",
            create_type=True
        ),
        nullable=False,
    )

    classified_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    classification_probabilities = Column(
        JSONB,
        nullable=True,
        comment="Probability distribution for each classification label"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return JSON\-serializable dict of the row."""
        return {
            "classification_id": str(self.classification_id) if self.classification_id else None,
            "student_id": str(self.student_id) if self.student_id else None,
            "classification": (self.classification.value if isinstance(self.classification, ClassificationLabel) else str(self.classification)) if self.classification is not None else None,
            "classification_probabilities": self.classification_probabilities,
            "classified_at": self.classified_at.isoformat() if isinstance(self.classified_at, datetime) else None,
        }