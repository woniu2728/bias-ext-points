from __future__ import annotations

from bias_core.extensions import setting_field


FORUM_EXPOSED_SETTINGS = (
    "enabled",
    "ai_question_coach_cost",
    "ai_role_summon_cost",
    "ai_bounty_judge_cost",
    "ai_discussion_summary_cost",
)


DEFAULT_SETTINGS = (
    ("enabled", True),
    ("discussion_create_reward", 10),
    ("reply_create_reward", 3),
    ("like_received_reward", 1),
    ("ai_question_coach_cost", 2),
    ("ai_role_summon_cost", 3),
    ("ai_bounty_judge_cost", 5),
    ("ai_discussion_summary_cost", 8),
)


def setting_definitions():
    return (
        setting_field({
            "key": "enabled",
            "label": "启用积分系统",
            "type": "boolean",
            "default": True,
            "help_text": "关闭后不再自动发放或消费积分，但历史账本保留。",
            "order": 5,
        }),
        setting_field({
            "key": "discussion_create_reward",
            "label": "发主题奖励",
            "type": "number",
            "default": 10,
            "help_text": "审核通过的主题创建后奖励作者的积分。",
            "order": 10,
        }),
        setting_field({
            "key": "reply_create_reward",
            "label": "回复奖励",
            "type": "number",
            "default": 3,
            "help_text": "审核通过的回复创建后奖励作者的积分。",
            "order": 20,
        }),
        setting_field({
            "key": "like_received_reward",
            "label": "收到点赞奖励",
            "type": "number",
            "default": 1,
            "help_text": "回复被其他用户点赞后奖励作者的积分。",
            "order": 30,
        }),
        setting_field({
            "key": "ai_question_coach_cost",
            "label": "AI 提问教练消耗",
            "type": "number",
            "default": 2,
            "help_text": "每次使用 AI 提问教练消耗的积分。",
            "order": 100,
        }),
        setting_field({
            "key": "ai_role_summon_cost",
            "label": "AI 角色召唤消耗",
            "type": "number",
            "default": 3,
            "help_text": "每次召唤 AI 书记员、侦探或挑战官消耗的积分。",
            "order": 110,
        }),
        setting_field({
            "key": "ai_bounty_judge_cost",
            "label": "AI 悬赏裁判消耗",
            "type": "number",
            "default": 5,
            "help_text": "每次使用 AI 悬赏裁判消耗的积分。",
            "order": 120,
        }),
        setting_field({
            "key": "ai_discussion_summary_cost",
            "label": "AI 讨论纪要消耗",
            "type": "number",
            "default": 8,
            "help_text": "每次生成讨论纪要消耗的积分。",
            "order": 130,
        }),
    )
