from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from unittest.mock import Mock

from dashboard.services import filter_queryset_by_scope


class DashboardHomeViewTests(TestCase):
    def setUp(self):
        self.url = reverse("dashboard:dashboard_home")
        self.user_model = get_user_model()

    def _create_user_with_role(self, username: str, role: str):
        user = self.user_model.objects.create_user(
            username=username,
            password="test-pass-123",
        )
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        return user

    def test_dashboard_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/accounts/login/?next={self.url}", response.url)

    def test_dashboard_access_for_authenticated_user(self):
        user = self._create_user_with_role("admin-user", "admin")
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h1", status_code=200)

    def test_login_redirects_to_dashboard_after_success(self):
        user = self._create_user_with_role("login-user", "direction")

        response = self.client.post(
            reverse("accounts:login"),
            {"username": user.username, "password": "test-pass-123"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url)

    def test_dashboard_contains_expected_sections(self):
        user = self.user_model.objects.create_user(
            username="direction-user",
            password="test-pass-123",
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Indicateurs clés (KPI)")
        self.assertContains(response, "<div id=\"alertes\"", html=False)
        self.assertContains(response, "Raccourcis modules")

    def test_dashboard_widget_filtering_by_role(self):
        admin_user = self._create_user_with_role("admin-role-user", "admin")
        self.client.force_login(admin_user)
        admin_response = self.client.get(self.url)

        self.assertEqual(admin_response.status_code, 200)
        self.assertContains(admin_response, "Groupes utilisateurs")
        self.assertNotContains(admin_response, "Anomalies dossiers")

        finance_user = self._create_user_with_role("finance-role-user", "finance")
        self.client.force_login(finance_user)
        finance_response = self.client.get(self.url)

        self.assertEqual(finance_response.status_code, 200)
        self.assertContains(finance_response, "Échéances en retard")
        self.assertNotContains(finance_response, "Groupes utilisateurs")


    def test_dashboard_render_has_no_template_error_and_shows_welcome_block(self):
        user = self._create_user_with_role("render-user", "direction")
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "TemplateSyntaxError")
        self.assertContains(response, "Bienvenue")
        self.assertContains(response, f"Bonjour {user.username}")

    def test_dashboard_is_not_empty_for_authenticated_user(self):
        user = self._create_user_with_role("not-empty-user", "direction")
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bienvenue")
        self.assertContains(response, "Session active")
        self.assertNotContains(response, "<body></body>", html=False)
        self.assertContains(response, "dashboard-secondary-content")


class DashboardScopeFilterTests(TestCase):
    def _mock_queryset(self, fields):
        queryset = Mock()
        queryset.model = Mock()
        queryset.model._meta = Mock()
        queryset.model._meta.get_fields.return_value = [type("Field", (), {"name": name})() for name in fields]
        queryset.filter.return_value = queryset
        queryset.none.return_value = queryset
        return queryset

    def test_filter_queryset_by_scope_applies_school_filter(self):
        user = get_user_model().objects.create_user("scope-user", password="test-pass-123")
        user.school_id = 12
        queryset = self._mock_queryset(["id", "school"])

        filter_queryset_by_scope(queryset, user)

        queryset.filter.assert_called_once_with(school_id__in={12})

    def test_filter_queryset_by_scope_blocks_cross_school_when_no_scope(self):
        user = get_user_model().objects.create_user("no-scope-user", password="test-pass-123")
        queryset = self._mock_queryset(["id", "school"])

        filter_queryset_by_scope(queryset, user)

        queryset.none.assert_called_once()
        queryset.filter.assert_not_called()

    def test_filter_queryset_by_scope_applies_tenant_filter(self):
        user = get_user_model().objects.create_user("tenant-user", password="test-pass-123")
        user.tenant_id = 7
        queryset = self._mock_queryset(["id", "tenant"])

        filter_queryset_by_scope(queryset, user)

        queryset.filter.assert_called_once_with(tenant_id__in={7})
