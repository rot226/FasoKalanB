from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse


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

    def test_dashboard_contains_expected_sections(self):
        user = self.user_model.objects.create_user(
            username="direction-user",
            password="test-pass-123",
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertContains(response, "Tableau de bord")
        self.assertContains(response, "Alertes")
        self.assertContains(response, "Effectifs")
        self.assertContains(response, "Paiements (total)")

    def test_dashboard_widget_filtering_by_role(self):
        admin_user = self._create_user_with_role("admin-role-user", "admin")
        self.client.force_login(admin_user)
        admin_response = self.client.get(self.url)

        self.assertContains(admin_response, "Groupes utilisateurs")
        self.assertNotContains(admin_response, "Anomalies dossiers")

        finance_user = self._create_user_with_role("finance-role-user", "finance")
        self.client.force_login(finance_user)
        finance_response = self.client.get(self.url)

        self.assertContains(finance_response, "Échéances en retard")
        self.assertNotContains(finance_response, "Groupes utilisateurs")
