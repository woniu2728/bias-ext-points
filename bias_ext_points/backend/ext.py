from bias_ext_points.backend.extenders import (
    event_extenders,
    frontend_extenders,
    model_extenders,
    optional_integration_extenders,
    resource_extenders,
    route_extenders,
    service_extenders,
    settings_extenders,
)


def extend():
    return [
        *route_extenders(),
        *frontend_extenders(),
        *event_extenders(),
        *optional_integration_extenders(),
        *service_extenders(),
        *settings_extenders(),
        *model_extenders(),
        *resource_extenders(),
    ]
