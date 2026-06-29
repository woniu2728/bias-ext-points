from __future__ import annotations

from bias_core.extensions import FrontendExtender


def frontend_extender():
    return FrontendExtender(
        forum_entry="extensions/points/frontend/forum/index.js",
    )
