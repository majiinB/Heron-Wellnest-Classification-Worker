import json
import os
from typing import Any, Dict, Optional

from app.config.pubsub_config import pubsub_publisher
from app.utils.logger_util import logger


async def publish_message(
    topic_name: str,
    payload: Dict[str, Any],
    project_id: Optional[str] = None,
    attributes: Optional[Dict[str, str]] = None,
) -> str:
    """
    Publish a JSON payload to a Pub/Sub topic.

    Args:
        topic_name: Pub/Sub topic name (e.g. "my-topic") or full topic path
            (e.g. "projects/my-project/topics/my-topic").
        payload: JSON-serializable payload object.
        project_id: Optional GCP project id. If omitted, tries environment defaults.
        attributes: Optional string attributes for the message.

    Returns:
        Message ID returned by Pub/Sub.
    """
    if topic_name.startswith("projects/") and "/topics/" in topic_name:
        topic_path = topic_name
    else:
        resolved_project_id = (
            project_id
            or os.getenv("GOOGLE_CLOUD_PROJECT")
            or os.getenv("GCP_PROJECT")
        )
        if not resolved_project_id:
            raise ValueError(
                "Missing project_id. Pass a full topic path, provide project_id, "
                "or set GOOGLE_CLOUD_PROJECT/GCP_PROJECT."
            )
        topic_path = pubsub_publisher.topic_path(resolved_project_id, topic_name)

    data = json.dumps(payload).encode("utf-8")
    attrs = attributes or {}

    try:
        future = pubsub_publisher.publish(topic_path, data=data, **attrs)
        message_id = future.result()
        logger.info("Message %s published to %s", message_id, topic_path)
        return message_id
    except Exception as exc:
        logger.exception("Error publishing to %s: %s", topic_path, exc)
        raise