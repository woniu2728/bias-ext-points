from __future__ import annotations

from bias_core.extensions import (
    ApiResourceExtender,
    ApiRoutesExtender,
    ConditionalExtender,
    EventListenersExtender,
    LifecycleExtender,
    ModelExtender,
    ServiceProviderExtender,
    SettingsExtender,
)

from bias_ext_points.backend.api import router as points_router
from bias_ext_points.backend.frontend import frontend_extender
from bias_ext_points.backend.listener_contracts import (
    discussion_event_listener_definitions,
    like_event_listener_definitions,
    post_event_listener_definitions,
)
from bias_ext_points.backend.model_contracts import owned_models
from bias_ext_points.backend.resources import user_points_resource_field_definitions
from bias_ext_points.backend.runtime import points_service_provider
from bias_ext_points.backend.settings_contracts import (
    DEFAULT_SETTINGS,
    FORUM_EXPOSED_SETTINGS,
    setting_definitions,
)


def frontend_extenders():
    return (frontend_extender(),)


def route_extenders():
    return (
        ApiRoutesExtender(
            mounts=(("", points_router),),
            tags=("Points",),
        ),
    )


def event_extenders():
    return ()


def discussion_integration_extenders():
    return (
        EventListenersExtender(
            listeners=discussion_event_listener_definitions(),
        ),
    )


def post_integration_extenders():
    return (
        EventListenersExtender(
            listeners=post_event_listener_definitions(),
        ),
    )


def like_integration_extenders():
    return (
        EventListenersExtender(
            listeners=like_event_listener_definitions(),
        ),
    )


def optional_integration_extenders():
    return (
        ConditionalExtender().when_extension_enabled("discussions", discussion_integration_extenders),
        ConditionalExtender().when_extension_enabled("posts", post_integration_extenders),
        ConditionalExtender().when_extension_enabled("likes", like_integration_extenders),
    )


def settings_extenders():
    extender = SettingsExtender(
        fields=setting_definitions(),
        expose_to_forum=FORUM_EXPOSED_SETTINGS,
    )
    for key, value in DEFAULT_SETTINGS:
        extender = extender.default(key, value)
    return (extender,)


def model_extenders():
    extender = ModelExtender()
    for model, description in owned_models():
        extender = extender.owns(model, description=description)
    return (extender,)


def resource_extenders():
    return (
        ApiResourceExtender().fields(user_points_resource_field_definitions),
    )


def service_extenders():
    return (
        ServiceProviderExtender(
            key="points.service",
            provider=points_service_provider,
        ),
        LifecycleExtender(),
    )
