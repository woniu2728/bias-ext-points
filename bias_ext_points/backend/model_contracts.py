from __future__ import annotations

from bias_ext_points.backend.models import PointAccount, PointLedgerEntry


def owned_models():
    return (
        (
            PointAccount,
            "用户积分账户由 points 扩展拥有。",
        ),
        (
            PointLedgerEntry,
            "用户积分账本由 points 扩展拥有。",
        ),
    )
