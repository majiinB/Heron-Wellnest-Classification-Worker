from fastapi import APIRouter
from app.config.env_config import env
from app.utils.logger_util import logger
from app.services.classification_service import ClassificationService
from app.controllers.classification_controller import ClassificationController
from app.repositories.student_classification_repository import StudentClassificationRepository
from app.repositories.student_analytics_repository import StudentAnalyticsRepository
from app.config.datasource_config import SessionLocal

router = APIRouter()

# Resolve model feature columns: prefer env.MODEL_FEATURES, else use a safe default
DEFAULT_FEATURES = [
    "p_anxiety", "p_normal", "p_depression", "p_suicidal", "p_stress",
    "gratitude_flag",
    "Depressed", "Sad", "Exhausted", "Hopeless",
    "Anxious", "Angry", "Stressed", "Restless",
    "Calm", "Relaxed", "Peaceful", "Content",
    "Happy", "Energized", "Excited", "Motivated",
    "flipfeel_incrisis_pct", "flipfeel_struggling_pct",
    "flipfeel_thriving_pct", "flipfeel_excelling_pct",
]
X_COLUMNS = getattr(env, "MODEL_FEATURES", DEFAULT_FEATURES)

# Instantiate service and controller once at import
clf_service = ClassificationService(model_path=env.MODEL_PATH, model_encoder=env.MODEL_LABEL_ENCODER_PATH, x_columns=X_COLUMNS)

student_analytics_repo = StudentAnalyticsRepository(session_factory=SessionLocal)
student_classification_repo = StudentClassificationRepository(session_factory=SessionLocal)

# Pass both repository instances into the controller
clf_controller = ClassificationController(
    clf_service,
    student_analytics_repo,
    student_classification_repo,
)

@router.post("/daily-scheduler")
async def run_daily_classification():
    """
    Triggers today's (UTC) batch classification via the controller.
    Returns per-user results including prediction and probabilities.
    """
    try:
        await clf_controller.classify_today_entries(top_k=None)
        return {"status": "ok"}, 200
    except Exception as e:
        logger.error(f"Error running daily classification: {e}")
        return {"error": str(e)}, 200

@router.post("/weekly-scheduler")
async def run_weekly_classification():
    """
    Triggers today's (UTC) batch classification via the controller.
    Returns per-user results including prediction and probabilities.
    """
    try:
        await clf_controller.classify_weekly_entries()
        return {"status": "ok"}, 200
    except Exception as e:
        logger.error(f"Error running daily classification: {e}")
        return {"error": str(e)}, 200