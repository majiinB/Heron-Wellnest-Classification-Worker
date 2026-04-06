from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime, timedelta
from uuid import UUID

from app.repositories.student_classification_repository import StudentClassificationRepository
from app.repositories.student_weekly_classification_repository import StudentWeeklyClassificationRepository


# severity ordering for trend detection (lower = better)
_SEVERITY_ORDER = {
    "Excelling": 0,
    "Thriving": 1,
    "Struggling": 2,
    "InCrisis": 3,
    # allow alternative forms if present
    "Excelling".lower(): 0,
    "Thriving".lower(): 1,
    "Struggling".lower(): 2,
    "InCrisis".lower(): 3,
}

def _classification_to_str(c: Any) -> Optional[str]:
    if c is None:
        return None
    # SQLAlchemy enum objects commonly expose .value or .name
    try:
        if hasattr(c, "value"):
            return str(c.value)
    except Exception:
        pass
    try:
        return str(c)
    except Exception:
        return None


class WeeklyClassificationService:
    """
    Rule-based weekly classification service.
    Uses StudentClassificationRepository to read daily classifications and
    StudentWeeklyClassificationRepository to persist the weekly result.
    """

    def __init__(
        self,
        classification_repo: StudentClassificationRepository,
        weekly_repo: StudentWeeklyClassificationRepository,
    ):
        self.classification_repo = classification_repo
        self.weekly_repo = weekly_repo

    async def classify_and_record_week(
        self,
        student_id: UUID,
        week_start: datetime,
        week_end: datetime,
    ) -> Dict[str, Any]:
        """
        Compute weekly metrics and flag according to rules, persist a weekly record.
        Returns a dict with computed metrics, flags, and the persisted row (if created).
        """
        # Fetch recent daily classifications (take a reasonably large limit)
        # repository returns list ordered by classified_at desc (per its implementation)
        items = await self.classification_repo.list_for_student(student_id, limit=200)

        # Filter to entries within [week_start, week_end)
        week_entries = [
            it for it in items
            if getattr(it, "classified_at", None) is not None
               and (it.classified_at >= week_start and it.classified_at < week_end)
        ]

        # Normalize into (date, label_str) and sort ascending by date
        normalized: List[Dict[str, Any]] = []
        for it in week_entries:
            label = _classification_to_str(getattr(it, "classification", None))
            normalized.append({"date": it.classified_at, "label": label})
        normalized.sort(key=lambda x: x["date"])

        labels = [x["label"] for x in normalized if x["label"] is not None]

        # Dominant classification: most common; on tie choose the most recent occurrence among tied labels
        dominant = None
        if labels:
            counts = Counter(labels)
            most_common_count = max(counts.values())
            candidates = [lab for lab, cnt in counts.items() if cnt == most_common_count]
            if len(candidates) == 1:
                dominant = candidates[0]
            else:
                # pick most recent label from normalized list that is in candidates
                for rec in reversed(normalized):
                    if rec["label"] in candidates:
                        dominant = rec["label"]
                        break

        # computed metrics
        count_in_crisis = sum(1 for l in labels if (l and l.lower() == "incrisis".lower()))
        count_struggling = sum(1 for l in labels if (l and l.lower() == "struggling".lower()))
        total_valid_days = len(labels)

        # recent trend - last 3 days' labels
        last3 = [l for l in labels[-3:]]
        # convert to severity ints when possible
        def severity(label: Optional[str]) -> Optional[int]:
            if not label:
                return None
            return _SEVERITY_ORDER.get(label, _SEVERITY_ORDER.get(label.lower()))

        last3_sev = [severity(l) for l in last3]

        # Rule evaluations
        reasons: List[str] = []
        flag = False
        review_for_missing = False

        # R6: Missing data (<4 valid daily classifications)
        if total_valid_days < 4:
            review_for_missing = True
            reasons.append("R6: <4 valid daily classifications (data anomaly)")

        # R1: Critical frequency
        if count_in_crisis >= 2:
            flag = True
            reasons.append("R1: count_in_crisis >= 2")

        # R2: Persistent struggle
        if count_struggling >= 4:
            flag = True
            reasons.append("R2: count_struggling >= 4")

        # R3: Downward trend - last 3 days strictly worsening severity
        if len(last3_sev) == 3 and None not in last3_sev:
            if last3_sev[0] < last3_sev[1] < last3_sev[2]:
                flag = True
                reasons.append("R3: downward trend in last 3 days")

        # R4: Mixed but worrying
        if (count_in_crisis + count_struggling) >= 3:
            last_label = last3[-1] if last3 else (labels[-1] if labels else None)
            if last_label and last_label.lower() in ("struggling", "incrisis"):
                flag = True
                reasons.append("R4: mixed but worrying counts and last is Struggling or InCrisis")

        # R5: Stable improvement -> explicit do-not-flag override
        if len(last3) == 3 and all((l and l.lower() in ("thriving", "excelling")) for l in last3):
            # override any flag
            flag = False
            # reasons = [r for r in reasons if not r.startswith("R")]  # remove rule explanations if desired
            reasons.append("R5: stable improvement (do not flag)")

        # Persist weekly classification (dominant may be None)
        try:
            created = await self.weekly_repo.create(
                student_id=str(student_id),
                week_start=week_start,
                week_end=week_end,
                is_flagged=flag,
                reason=reasons,
                dominant_classification=dominant,
            )
        except Exception as exc:
            created = None
            reasons.append(f"persist_error: {exc}")

        result = {
            "student_id": str(student_id),
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "dominant_classification": dominant,
            "count_in_crisis": count_in_crisis,
            "count_struggling": count_struggling,
            "total_valid_days": total_valid_days,
            "last_3_labels": last3,
            "flagged": bool(flag),
            "review_for_missing": bool(review_for_missing),
            "reasons": reasons,
            "persisted_row": created,
        }
        return result