from __future__ import annotations

from bias_core.extensions import ExtensionEventListenerDefinition

from bias_ext_points.backend.listeners import (
    handle_discussion_created,
    handle_post_created,
    handle_post_liked,
)


def discussion_event_listener_definitions():
    return (
        ExtensionEventListenerDefinition(
            event_type="discussions.discussion.created",
            handler=handle_discussion_created,
            description="讨论发布成功后奖励作者积分。",
        ),
    )


def post_event_listener_definitions():
    return (
        ExtensionEventListenerDefinition(
            event_type="posts.post.created",
            handler=handle_post_created,
            description="回复发布成功后奖励作者积分。",
        ),
    )


def like_event_listener_definitions():
    return (
        ExtensionEventListenerDefinition(
            event_type="likes.post.liked",
            handler=handle_post_liked,
            description="回复被点赞后奖励作者积分。",
        ),
    )
