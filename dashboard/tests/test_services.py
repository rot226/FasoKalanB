from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from dashboard import services


class DashboardServicesKpiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("kpi-user", password="test-pass-123")

    @patch("dashboard.services.aggregate_student_anomalies", return_value=1)
    @patch("dashboard.services.build_academics_snapshot", return_value={
        "classes_actives": 2,
        "sessions_actives": 3,
        "evenements_imminents": 4,
        "anomalies_planification": 0,
    })
    @patch("dashboard.services.aggregate_students_by_level_and_class", return_value={"by_level": {"6e": 1}, "by_class": {"A": 1}})
    @patch("dashboard.services.aggregate_new_students", return_value=5)
    @patch("dashboard.services.aggregate_total_students", return_value=15)
    def test_build_kpi_snapshot_returns_expected_values(self, *_mocks):
        students_qs = Mock(name="students_qs")
        students_qs.model._meta.get_fields.return_value = []

        payments_qs = Mock(name="payments_qs")
        payments_qs.model._meta.get_fields.return_value = [type("Field", (), {"name": "amount"})(), type("Field", (), {"name": "paid_at"})()]
        monthly_payments_qs = Mock(name="monthly_payments_qs")
        monthly_payments_qs.model._meta.get_fields.return_value = payments_qs.model._meta.get_fields.return_value
        monthly_payments_qs.aggregate.return_value = {"total": Decimal("25000")}
        payments_qs.filter.return_value = monthly_payments_qs

        schedule_qs = Mock(name="schedule_qs")
        schedule_qs.model._meta.get_fields.return_value = [type("Field", (), {"name": "due_date"})(), type("Field", (), {"name": "status"})()]
        overdue_qs = Mock(name="overdue_qs")
        overdue_qs.count.return_value = 2
        near_qs = Mock(name="near_qs")
        near_qs.count.return_value = 6
        schedule_qs.filter.side_effect = [overdue_qs, near_qs]

        with patch("dashboard.services._get_model", side_effect=[object(), object(), object()]), patch(
            "dashboard.services._base_queryset", side_effect=[students_qs, payments_qs, schedule_qs]
        ), patch("dashboard.services.filter_queryset_by_scope", side_effect=[students_qs, payments_qs, schedule_qs]):
            kpis = services.build_kpi_snapshot(self.user)

        self.assertEqual(kpis["effectif_total"], 15)
        self.assertEqual(kpis["nouveaux_inscrits"], 5)
        self.assertEqual(kpis["paiements_mois"], Decimal("25000"))
        self.assertEqual(kpis["impayes"], 2)
        self.assertEqual(kpis["echeances_proches"], 6)
        self.assertEqual(kpis["anomalies"], 1)


class DashboardServicesScopeTests(TestCase):
    def _mock_queryset(self, fields):
        queryset = Mock()
        queryset.model = Mock()
        queryset.model._meta = Mock()
        queryset.model._meta.get_fields.return_value = [type("Field", (), {"name": name})() for name in fields]
        queryset.filter.return_value = queryset
        queryset.none.return_value = queryset
        return queryset

    def test_filter_queryset_by_scope_uses_profile_scope(self):
        user = get_user_model().objects.create_user("profile-scope-user", password="test-pass-123")
        user.profile = type("Profile", (), {"school_id": 42})()
        queryset = self._mock_queryset(["id", "school"])

        services.filter_queryset_by_scope(queryset, user)

        queryset.filter.assert_called_once_with(school_id__in={42})

    def test_filter_queryset_by_scope_falls_back_to_user_field(self):
        user = get_user_model().objects.create_user("owner-user", password="test-pass-123")
        queryset = self._mock_queryset(["id", "user"])

        services.filter_queryset_by_scope(queryset, user)

        queryset.filter.assert_called_once_with(user=user)


class DashboardServicesRoleWidgetsAndEmptyStateTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("direction-role-user", password="test-pass-123")

    def test_unknown_role_maps_to_default_widgets(self):
        kpis = {"effectif_total": 99}

        cards = services._build_summary_cards(kpis, role="role-inconnu")

        expected_keys = [widget.key for widget in services.ROLE_WIDGETS[services.DEFAULT_ROLE]]
        self.assertEqual([card["key"] for card in cards], expected_keys)

    def test_empty_state_is_false_when_default_widgets_exist_even_with_zero_values(self):
        with patch("dashboard.services.build_kpi_snapshot", return_value={}), patch(
            "dashboard.services.get_dashboard_alerts", return_value={"alerts": [], "alerts_sort": "criticite", "alerts_dir": "desc"}
        ):
            payload = services.build_dashboard_context(self.user)

        self.assertFalse(payload["empty_state"]["show"])
        self.assertGreater(len(payload["summary_cards"]), 0)
        self.assertTrue(all(card["value"] == "0" for card in payload["summary_cards"]))

    def test_empty_state_is_true_when_no_widgets_are_configured(self):
        with patch.dict("dashboard.services.ROLE_WIDGETS", {services.DEFAULT_ROLE: []}, clear=True), patch(
            "dashboard.services.build_kpi_snapshot", return_value={}
        ), patch(
            "dashboard.services.get_dashboard_alerts", return_value={"alerts": [], "alerts_sort": "criticite", "alerts_dir": "desc"}
        ):
            payload = services.build_dashboard_context(self.user)

        self.assertTrue(payload["empty_state"]["show"])
        self.assertEqual(payload["summary_cards"], [])
        self.assertEqual(payload["widgets"], [])
