from dataclasses import dataclass
from typing import List, Iterable, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlalchemy.orm import sessionmaker
from app.model.student_analytics_model import StudentAnalytics
from app.model.student_classification_model import ClassificationLabel
from dataclasses import asdict

@dataclass
class CreateStudentAnalytics:
    analytics_id: Optional[UUID] = None
    date_recorded: Optional[datetime] = None
    # store gratitude_flag as integer (0 or 1) for DB compatibility
    gratitude_flag: Optional[int] = 0
    p_anxiety: Optional[float] = None
    p_normal: Optional[float] = None
    p_stressed: Optional[float] = None
    p_suicidal: Optional[float] = None
    p_depressed: Optional[float] = None
    mood_happy: Optional[int] = None
    mood_energized: Optional[int] = None
    mood_excited: Optional[int] = None
    mood_motivated: Optional[int] = None
    mood_calm: Optional[int] = None
    mood_relaxed: Optional[int] = None
    mood_peaceful: Optional[int] = None
    mood_content: Optional[int] = None
    mood_anxious: Optional[int] = None
    mood_angry: Optional[int] = None
    mood_stressed: Optional[int] = None
    mood_restless: Optional[int] = None
    mood_depressed: Optional[int] = None
    mood_sad: Optional[int] = None
    mood_exhausted: Optional[int] = None
    mood_hopeless: Optional[int] = None
    f_and_f_in_crisis: Optional[float] = None
    f_and_f_struggling: Optional[float] = None
    f_and_f_thriving: Optional[float] = None
    f_and_f_excelling: Optional[float] = None
    f_and_f_final_category: Optional[float] = None
    classification: Optional[str] = None

class StudentAnalyticsRepository:

    def __init__(self, session_factory: sessionmaker):
        self.session_factory: sessionmaker = session_factory

    def _to_enum(self, val: Any) -> Optional[ClassificationLabel]:
        if val is None:
            return None
        if isinstance(val, ClassificationLabel):
            return val
        if isinstance(val, str):
            normalized = val.strip().replace("-", "_").replace(" ", "_").lower()
            for e in ClassificationLabel:
                if e.value.lower() == normalized or e.name.lower() == normalized:
                    return e
        raise ValueError(f"Unknown classification: {val}")

    async def create(self, payload: CreateStudentAnalytics) -> StudentAnalytics:
        async with self.session_factory() as session:  # type: AsyncSession
            data = asdict(payload)
            data["analytics_id"] = data.get("analytics_id") or uuid4()
            data["date_recorded"] = data.get("date_recorded") or datetime.now(timezone.utc)
            data["classification"] = self._to_enum(data.get("classification"))
            inst = StudentAnalytics(**data)
            session.add(inst)
            await session.commit()
            await session.refresh(inst)
            return inst

    async def bulk_create(self, items: Iterable[CreateStudentAnalytics]) -> List[StudentAnalytics]:
        created: List[StudentAnalytics] = []
        async with self.session_factory() as session:  # type: AsyncSession
            for payload in items:
                data = asdict(payload)
                data["analytics_id"] = data.get("analytics_id") or uuid4()
                data["date_recorded"] = data.get("date_recorded") or datetime.now(timezone.utc)
                data["classification"] = self._to_enum(data.get("classification"))
                created.append(StudentAnalytics(**data))
            session.add_all(created)
            await session.commit()
            for inst in created:
                await session.refresh(inst)
            return created