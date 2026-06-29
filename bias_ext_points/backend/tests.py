import json
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase
from ninja_jwt.tokens import RefreshToken

from bias_core.extensions.testing import ExtensionRuntimeTestMixin, build_extension_test_host, save_extension_settings
from bias_core.extensions.runtime import (
    create_runtime_discussion,
    create_runtime_post,
    get_runtime_user_model,
    get_runtime_resource_registry,
)
from bias_ext_points.backend.models import PointLedgerEntry
from bias_ext_points.backend.services import (
    InsufficientPointsError,
    award_points,
    get_balance,
    spend_points,
)


class RuntimeModelProxy:
    def __init__(self, resolver):
        self._resolver = resolver

    def __getattr__(self, name):
        return getattr(self._resolver(), name)


User = RuntimeModelProxy(get_runtime_user_model)


class PointsExtensionDiagnosticsTests(ExtensionRuntimeTestMixin, TestCase):
    def test_points_extension_registers_runtime_service_provider(self):
        application = self.bootstrap_extensions("points")
        service = application.get_service("points.service")
        runtime_view = application.get_runtime_view("points")

        self.assertIn("points.service", application.get_service_provider_keys(extension_id="points"))
        self.assertTrue(callable(service["award"]))
        self.assertTrue(callable(service["spend"]))
        self.assertIn("discussion_create_reward", {item.key for item in runtime_view.settings_schema})

    def test_reward_event_integrations_are_optional(self):
        application = build_extension_test_host("points")

        self.assertEqual(application.events.get_listeners(extension_id="points"), [])
        self.assertIsNone(application.get_service("posts.service"))
        self.assertIsNone(application.get_service("likes.service"))

    def test_discussion_and_post_reward_integrations_register_independently(self):
        application = build_extension_test_host("posts", "points")
        listener_names = {
            listener.handler.__name__
            for listener in application.events.get_listeners(extension_id="points")
        }

        self.assertIsNotNone(application.get_service("posts.service"))
        self.assertIn("handle_discussion_created", listener_names)
        self.assertIn("handle_post_created", listener_names)
        self.assertNotIn("handle_post_liked", listener_names)

    def test_like_reward_integration_requires_likes_event_contract_only(self):
        application = build_extension_test_host("likes", "points")
        listener_names = {
            listener.handler.__name__
            for listener in application.events.get_listeners(extension_id="points")
        }

        self.assertIsNotNone(application.get_service("likes.service"))
        self.assertIn("handle_post_liked", listener_names)

    def test_inspect_reports_points_extension_without_validation_errors(self):
        stdout = StringIO()
        call_command(
            "inspect_extensions",
            "--extension-id",
            "points",
            stdout=stdout,
        )
        payload = json.loads(stdout.getvalue())
        extension = payload["extensions"][0]
        issues = extension["debug_info"]["validation_issues"]

        self.assertEqual(extension["id"], "points")
        self.assertFalse(any(item["level"] == "error" for item in issues))

    def test_points_balance_is_registered_on_all_user_resources(self):
        application = self.bootstrap_extensions("points")
        runtime_view = application.get_runtime_view("points")

        fields = {
            (definition.resource, definition.field)
            for definition in runtime_view.resource_fields
        }

        self.assertTrue({
            ("user_detail", "points_balance"),
            ("user_summary", "points_balance"),
            ("discussion_user", "points_balance"),
            ("post_user", "points_balance"),
            ("search_user", "points_balance"),
        }.issubset(fields))

    def test_points_balance_serializes_on_user_summary_resources(self):
        self.bootstrap_extensions("points")
        user = User.objects.create_user(
            username="points-resource-user",
            email="points-resource-user@example.com",
            password="password123",
            is_email_confirmed=True,
        )
        award_points(
            user,
            12,
            reason="manual_award",
            idempotency_key="manual:resource:award",
        )
        registry = get_runtime_resource_registry()

        for resource in ("user_detail", "user_summary", "discussion_user", "post_user", "search_user"):
            with self.subTest(resource=resource):
                payload = registry.serialize(resource, user)
                self.assertEqual(payload["points_balance"], 12)


class PointsServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="points-user",
            email="points-user@example.com",
            password="password123",
            is_email_confirmed=True,
        )

    def test_award_and_spend_points_update_balance(self):
        award_points(
            self.user,
            10,
            reason="manual_award",
            idempotency_key="manual:award:1",
        )
        spend_points(
            self.user,
            4,
            reason="manual_spend",
            idempotency_key="manual:spend:1",
        )

        self.assertEqual(get_balance(self.user), 6)
        self.assertEqual(PointLedgerEntry.objects.count(), 2)

    def test_idempotency_key_prevents_duplicate_award(self):
        first = award_points(
            self.user,
            10,
            reason="manual_award",
            idempotency_key="manual:award:duplicate",
        )
        second = award_points(
            self.user,
            10,
            reason="manual_award",
            idempotency_key="manual:award:duplicate",
        )

        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(get_balance(self.user), 10)
        self.assertEqual(PointLedgerEntry.objects.count(), 1)

    def test_spend_points_rejects_insufficient_balance(self):
        with self.assertRaises(InsufficientPointsError):
            spend_points(
                self.user,
                5,
                reason="manual_spend",
                idempotency_key="manual:spend:insufficient",
            )


class PointsApiTests(ExtensionRuntimeTestMixin, TestCase):
    def setUp(self):
        self.bootstrap_extensions("points")
        self.user = User.objects.create_user(
            username="points-api-user",
            email="points-api-user@example.com",
            password="password123",
            is_email_confirmed=True,
        )
        award_points(
            self.user,
            15,
            reason="manual_award",
            idempotency_key="manual:api:award",
        )

    def auth_header(self):
        token = RefreshToken.for_user(self.user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def test_current_points_accepts_access_token_user(self):
        response = self.client.get("/api/points/me", **self.auth_header())

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["balance"], 15)

    def test_points_ledger_accepts_access_token_user(self):
        response = self.client.get("/api/points/ledger", **self.auth_header())

        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()
        self.assertEqual(payload["data"][0]["balance_after"], 15)


class PointsRewardIntegrationTests(ExtensionRuntimeTestMixin, TestCase):
    def setUp(self):
        self.bootstrap_extensions("points")
        save_extension_settings("points", {
            "enabled": True,
            "discussion_create_reward": 10,
            "reply_create_reward": 3,
            "like_received_reward": 1,
        })
        self.author = User.objects.create_user(
            username="points-author",
            email="points-author@example.com",
            password="password123",
            is_email_confirmed=True,
        )

    def test_discussion_and_reply_creation_award_points_once(self):
        with self.captureOnCommitCallbacks(execute=True):
            discussion = create_runtime_discussion(
                title="Points discussion",
                content="Initial post",
                user=self.author,
            )
        with self.captureOnCommitCallbacks(execute=True):
            create_runtime_post(
                discussion_id=discussion.id,
                content="Rewarded reply",
                user=self.author,
            )

        self.assertEqual(get_balance(self.author), 13)
        reasons = list(PointLedgerEntry.objects.order_by("id").values_list("reason", flat=True))
        self.assertEqual(reasons, ["discussion_created", "reply_created"])

    def test_like_reward_uses_likes_event_author_contract(self):
        from bias_ext_points.backend.listeners import handle_post_liked

        liker = User.objects.create_user(
            username="points-liker",
            email="points-liker@example.com",
            password="password123",
            is_email_confirmed=True,
        )
        event = SimpleNamespace(
            post_id=55,
            actor_user_id=liker.id,
            post_user_id=self.author.id,
        )

        with patch(
            "bias_ext_points.backend.listeners.get_runtime_post_by_id",
            create=True,
            side_effect=AssertionError("points should use the likes event author contract"),
        ):
            handle_post_liked(event)

        self.assertEqual(get_balance(self.author), 1)
        self.assertEqual(
            PointLedgerEntry.objects.get(reason="like_received").meta["from_user_id"],
            liker.id,
        )


