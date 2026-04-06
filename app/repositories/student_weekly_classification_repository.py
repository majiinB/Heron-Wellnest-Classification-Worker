# python
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from app.utils.db_utils import fetch_one, fetch_all, execute
from app.model.student_weekly_classification_model import WeeklyClassificationLabel


def _row_to_dict(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        "weekly_classification_id": str(row.get("weekly_classification_id")) if row.get("weekly_classification_id") is not None else None,
        "student_id": str(row.get("student_id")) if row.get("student_id") is not None else None,
        "week_start": row.get("week_start").isoformat() if row.get("week_start") is not None else None,
        "week_end": row.get("week_end").isoformat() if row.get("week_end") is not None else None,
        "dominant_classification": row.get("dominant_classification"),
        "classified_at": row.get("classified_at").isoformat() if row.get("classified_at") is not None else None,
    }


class StudentWeeklyClassificationRepository:
    """
    Repository for storing and retrieving StudentWeeklyClassification rows.
    Uses `fetch_one`, `fetch_all`, `execute` from `app.utils.db_utils`.
    """

    async def create(
        self,
        student_id: str,
        week_start: datetime,
        week_end: datetime,
        is_flagged: bool,
        reason: Optional[str] = None,
        dominant_classification: Optional[str] = None,
        classified_at: Optional[datetime] = None,
        weekly_classification_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """
        Insert a new weekly classification and return the created row as dict.
        `dominant_classification` may be a WeeklyClassificationLabel or string.
        """
        if isinstance(dominant_classification, WeeklyClassificationLabel):
            dc = dominant_classification.value
        else:
            dc = dominant_classification

        if weekly_classification_id is None:
            weekly_classification_id = uuid.uuid4()

        query = """
        INSERT INTO student_weekly_classification
            (weekly_classification_id, student_id, week_start, week_end, dominant_classification, classified_at, is_flagged, reason)
        VALUES
            (:weekly_classification_id, :student_id, :week_start, :week_end, :dominant_classification, COALESCE(:classified_at, now()), :is_flagged, :reason) )
        RETURNING *;
        """
        params = {
            "weekly_classification_id": str(weekly_classification_id),
            "student_id": student_id,
            "week_start": week_start,
            "week_end": week_end,
            "is_flagged": is_flagged,
            "reason": reason,
            "dominant_classification": dc,
            "classified_at": classified_at,
        }
        row = await fetch_one(query, params)
        return _row_to_dict(row)

    async def get_by_id(self, weekly_classification_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM student_weekly_classification WHERE weekly_classification_id = :id LIMIT 1;"
        row = await fetch_one(query, {"id": weekly_classification_id})
        return _row_to_dict(row)

    async def get_by_student_and_week(self, student_id: str, week_start: datetime) -> Optional[Dict[str, Any]]:
        """
        Fetch a record by student and exact week_start.
        """
        query = """
        SELECT * FROM student_weekly_classification
        WHERE student_id = :student_id AND week_start = :week_start
        LIMIT 1;
        """
        row = await fetch_one(query, {"student_id": student_id, "week_start": week_start})
        return _row_to_dict(row)

    async def get_latest_for_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        query = """
        SELECT * FROM student_weekly_classification
        WHERE student_id = :student_id
        ORDER BY week_start DESC
        LIMIT 1;
        """
        row = await fetch_one(query, {"student_id": student_id})
        return _row_to_dict(row)

    async def list_for_student(
        self,
        student_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        List records for a student optionally constrained by week_start / week_end bounds.
        """
        if start and end:
            query = """
            SELECT * FROM student_weekly_classification
            WHERE student_id = :student_id
              AND week_start >= :start AND week_end <= :end
            ORDER BY week_start ASC;
            """
            params = {"student_id": student_id, "start": start, "end": end}
        else:
            query = """
            SELECT * FROM student_weekly_classification
            WHERE student_id = :student_id
            ORDER BY week_start ASC;
            """
            params = {"student_id": student_id}

        rows = await fetch_all(query, params)
        return [ _row_to_dict(r) for r in (rows or []) ]

    async def delete_by_id(self, weekly_classification_id: str) -> bool:
        query = "DELETE FROM student_weekly_classification WHERE weekly_classification_id = :id;"
        affected = await execute(query, {"id": weekly_classification_id})
        return bool(affected)