from sqlalchemy import Column, DateTime, Float, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, ENUM as PG_ENUM
from typing import Dict, Any
from datetime import datetime
import uuid

from app.model.student_classification_model import Base, ClassificationLabel

class StudentAnalytics(Base):
    __tablename__ = "student_analytics"

    analytics_id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    date_recorded = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # store gratitude_flag as integer 0/1 in DB
    gratitude_flag = Column(Integer, nullable=False, default=0)

    p_anxiety = Column(Float, nullable=True)
    p_normal = Column(Float, nullable=True)
    p_stressed = Column(Float, nullable=True)
    p_suicidal = Column(Float, nullable=True)
    p_depressed = Column(Float, nullable=True)

    mood_happy = Column(Integer, nullable=True)
    mood_energized = Column(Integer, nullable=True)
    mood_excited = Column(Integer, nullable=True)
    mood_motivated = Column(Integer, nullable=True)
    mood_calm = Column(Integer, nullable=True)
    mood_relaxed = Column(Integer, nullable=True)
    mood_peaceful = Column(Integer, nullable=True)
    mood_content = Column(Integer, nullable=True)
    mood_anxious = Column(Integer, nullable=True)
    mood_angry = Column(Integer, nullable=True)
    mood_stressed = Column(Integer, nullable=True)
    mood_restless = Column(Integer, nullable=True)
    mood_depressed = Column(Integer, nullable=True)
    mood_sad = Column(Integer, nullable=True)
    mood_exhausted = Column(Integer, nullable=True)
    mood_hopeless = Column(Integer, nullable=True)

    f_and_f_in_crisis = Column(Float, nullable=True)
    f_and_f_struggling = Column(Float, nullable=True)
    f_and_f_thriving = Column(Float, nullable=True)
    f_and_f_excelling = Column(Float, nullable=True)

    classification = Column(
        PG_ENUM(
            ClassificationLabel,
            name="student_classification_enum",
            create_type=False,  # enum type created in student_classification_model.py
        ),
        nullable=True,
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analytics_id": str(self.analytics_id) if self.analytics_id else None,
            "date_recorded": self.date_recorded.isoformat() if isinstance(self.date_recorded, datetime) else None,
            # return gratitude_flag as integer 0/1 to match expected API/consumers
            "gratitude_flag": 1 if self.gratitude_flag else 0,
            "p_anxiety": float(self.p_anxiety) if self.p_anxiety is not None else None,
            "p_normal": float(self.p_normal) if self.p_normal is not None else None,
            "p_stressed": float(self.p_stressed) if self.p_stressed is not None else None,
            "p_suicidal": float(self.p_suicidal) if self.p_suicidal is not None else None,
            "p_depressed": float(self.p_depressed) if self.p_depressed is not None else None,
            "mood_happy": int(self.mood_happy) if self.mood_happy is not None else None,
            "mood_energized": int(self.mood_energized) if self.mood_energized is not None else None,
            "mood_excited": int(self.mood_excited) if self.mood_excited is not None else None,
            "mood_motivated": int(self.mood_motivated) if self.mood_motivated is not None else None,
            "mood_calm": int(self.mood_calm) if self.mood_calm is not None else None,
            "mood_relaxed": int(self.mood_relaxed) if self.mood_relaxed is not None else None,
            "mood_peaceful": int(self.mood_peaceful) if self.mood_peaceful is not None else None,
            "mood_content": int(self.mood_content) if self.mood_content is not None else None,
            "mood_anxious": int(self.mood_anxious) if self.mood_anxious is not None else None,
            "mood_angry": int(self.mood_angry) if self.mood_angry is not None else None,
            "mood_stressed": int(self.mood_stressed) if self.mood_stressed is not None else None,
            "mood_restless": int(self.mood_restless) if self.mood_restless is not None else None,
            "mood_depressed": int(self.mood_depressed) if self.mood_depressed is not None else None,
            "mood_sad": int(self.mood_sad) if self.mood_sad is not None else None,
            "mood_exhausted": int(self.mood_exhausted) if self.mood_exhausted is not None else None,
            "mood_hopeless": int(self.mood_hopeless) if self.mood_hopeless is not None else None,
            "f_and_f_in_crisis": float(self.f_and_f_in_crisis) if self.f_and_f_in_crisis is not None else None,
            "f_and_f_struggling": float(self.f_and_f_struggling) if self.f_and_f_struggling is not None else None,
            "f_and_f_thriving": float(self.f_and_f_thriving) if self.f_and_f_thriving is not None else None,
            "f_and_f_excelling": float(self.f_and_f_excelling) if self.f_and_f_excelling is not None else None,
            "classification": (self.classification.value if isinstance(self.classification, ClassificationLabel) else (str(self.classification) if self.classification is not None else None)),
        }