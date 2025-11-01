from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Iterable, Any, List
from uuid import UUID, uuid4
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.model.student_classification_model import StudentClassification, ClassificationLabel
from app.model.student_analytics_model import StudentAnalytics

@dataclass
class CreateStudentClassification:
    student_id: UUID
    classification: Optional[str]
    classified_at: Optional[datetime] = None
    classification_id: Optional[UUID] = None
    classification_probabilities: Optional[dict] = None

class StudentClassificationRepository:
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory

    def _to_enum(self, val: Any) -> ClassificationLabel:
        if isinstance(val, ClassificationLabel):
            return val
        if val is None:
            raise ValueError("classification is required")
        if isinstance(val, str):
            for e in ClassificationLabel:
                if e.value == val or e.name == val or e.name.replace("_", "-") == val:
                    return e
        raise ValueError(f"Unknown classification: {val}")

    async def create(
        self,
        student_id: UUID,
        classification: Any,
        classified_at: Optional[datetime] = None,
        classification_id: Optional[UUID] = None,
        classification_probabilities: Optional[dict] = None,
    ) -> StudentClassification:
        async with self.session_factory() as session:  # type: AsyncSession
            inst = StudentClassification(
                classification_id=classification_id or uuid4(),
                student_id=student_id,
                classification=self._to_enum(classification),
                classified_at=classified_at,
                classification_probabilities=classification_probabilities,
            )
            session.add(inst)
            await session.commit()
            await session.refresh(inst)
            return inst

    async def bulk_create(self, items: Iterable[CreateStudentClassification]) -> List[StudentClassification]:
        created: List[StudentClassification] = []
        async with self.session_factory() as session:
            for item in items:
                inst = StudentClassification(
                    classification_id=item.classification_id or uuid4(),
                    student_id=item.student_id,
                    classification=self._to_enum(item.classification),
                    classified_at=item.classified_at,
                    classification_probabilities=item.classification_probabilities,
                )
                created.append(inst)
            session.add_all(created)
            await session.commit()
            for inst in created:
               await session.refresh(inst)
            return created

    async def get_by_id(self, classification_id: UUID) -> Optional[StudentClassification]:
        async with self.session_factory() as session:
            return await session.get(StudentClassification, classification_id)

    async def get_latest_for_student(self, student_id: UUID) -> Optional[StudentClassification]:
        async with self.session_factory() as session:  # type: AsyncSession
            stmt = (
                select(StudentClassification)
                .where(StudentClassification.student_id == student_id)
                .order_by(desc(StudentClassification.classified_at))
                .limit(1)
            )
            result = await session.execute(stmt)
            return result.scalars().one_or_none()

    async def list_for_student(self, student_id: UUID, limit: int = 20) -> List[StudentClassification]:
        async with self.session_factory() as session:  # type: AsyncSession
            stmt = (
                select(StudentClassification)
                .where(StudentClassification.student_id == student_id)
                .order_by(desc(StudentClassification.classified_at))
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def list_all(self, limit: int = 1000, offset: int = 0) -> List[StudentClassification]:
        """
        Return up to `limit` StudentClassification rows ordered by classified_at descending.
        Use `offset` for pagination.
        """
        async with self.session_factory() as session:  # type: AsyncSession
            stmt = (
                select(StudentClassification)
                .order_by(desc(StudentClassification.classified_at))
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def list_between(self, start: datetime, end: datetime) -> List[StudentClassification]:
        """
        Return StudentClassification rows with classified_at in [start, end),
        ordered by classified_at descending.
        """
        async with self.session_factory() as session:  # type: AsyncSession
            stmt = (
                select(StudentClassification)
                .where(
                    StudentClassification.classified_at >= start,
                    StudentClassification.classified_at < end,
                )
                .order_by(desc(StudentClassification.classified_at))
            )
            result = await session.execute(stmt)
            return result.scalars().all()