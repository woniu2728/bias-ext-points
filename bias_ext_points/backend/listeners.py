from __future__ import annotations

from bias_ext_points.backend.settings import get_points_settings
from bias_ext_points.backend.services import award_points


def get_user_service():
    from bias_core.extensions.runtime import get_runtime_service

    return get_runtime_service("users.service")


def _service_method(service, name: str):
    if isinstance(service, dict):
        method = service.get(name)
    else:
        method = getattr(service, name, None)
    if not callable(method):
        raise RuntimeError(f"Points 扩展运行时服务缺少方法: {name}")
    return method


def handle_discussion_created(event) -> None:
    settings = get_points_settings()
    if not settings.enabled or not getattr(event, "is_approved", True):
        return
    user = _resolve_user_or_none(getattr(event, "actor_user_id", 0))
    if user is None:
        return
    award_points(
        user,
        settings.discussion_create_reward,
        reason="discussion_created",
        idempotency_key=f"discussion:create:{event.discussion_id}",
        source_type="discussion",
        source_id=event.discussion_id,
        meta={"event": "DiscussionCreatedEvent"},
    )


def handle_post_created(event) -> None:
    settings = get_points_settings()
    if not settings.enabled or not getattr(event, "is_approved", True):
        return
    user = _resolve_user_or_none(getattr(event, "actor_user_id", 0))
    if user is None:
        return
    award_points(
        user,
        settings.reply_create_reward,
        reason="reply_created",
        idempotency_key=f"post:create:{event.post_id}",
        source_type="post",
        source_id=event.post_id,
        meta={"event": "PostCreatedEvent", "discussion_id": getattr(event, "discussion_id", None)},
    )


def handle_post_liked(event) -> None:
    settings = get_points_settings()
    if not settings.enabled or settings.like_received_reward <= 0:
        return
    post_user_id = int(getattr(event, "post_user_id", 0) or 0)
    actor_user_id = int(getattr(event, "actor_user_id", 0) or 0)
    if not post_user_id or post_user_id == actor_user_id:
        return
    user = _resolve_user_or_none(post_user_id)
    if user is None:
        return
    award_points(
        user,
        settings.like_received_reward,
        reason="like_received",
        idempotency_key=f"post:like-received:{event.post_id}:{actor_user_id}",
        source_type="post",
        source_id=getattr(event, "post_id", ""),
        meta={"event": "PostLikedEvent", "from_user_id": actor_user_id},
    )


def _resolve_user_or_none(user_id: int):
    try:
        return _service_method(get_user_service(), "get_by_id")(int(user_id or 0))
    except Exception:
        return None

