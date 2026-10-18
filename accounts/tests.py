from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from documents.models import Document, DocumentCategory

User = get_user_model()


class AdminAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='admin_test', password='AdminPass123!',
            email='admin@test.com', role='admin',
        )
        self.student = User.objects.create_user(
            username='student_test', password='StudentPass123!',
            email='student@test.com', role='student',
        )
        self.category = DocumentCategory.objects.create(
            name='Test Category', description='Test', is_active=True
        )

    # 1. Admin can access Admin Dashboard
    def test_admin_can_access_dashboard(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.get('/dashboard/admin/')
        self.assertEqual(response.status_code, 200)

    # 2. Student cannot access Admin Dashboard
    def test_student_cannot_access_admin_dashboard(self):
        self.client.login(username='student_test', password='StudentPass123!')
        response = self.client.get('/dashboard/admin/')
        # Should redirect to student dashboard
        self.assertNotEqual(response.status_code, 200)
        # Or redirected away
        self.assertIn(response.status_code, [302, 403])

    # 3. Admin can view their profile
    def test_admin_can_view_profile(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.get('/admin-profile/')
        self.assertEqual(response.status_code, 200)

    # 4. Student cannot access admin profile
    def test_student_cannot_access_admin_profile(self):
        self.client.login(username='student_test', password='StudentPass123!')
        response = self.client.get('/admin-profile/')
        self.assertEqual(response.status_code, 403)

    # 5. Admin can access change password page
    def test_admin_can_access_change_password(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.get('/admin-profile/change-password/')
        self.assertEqual(response.status_code, 200)

    # 6. Admin can view users list
    def test_admin_can_view_users(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.get('/manage/users/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'student_test')

    # 7. Student cannot access user management
    def test_student_cannot_access_user_management(self):
        self.client.login(username='student_test', password='StudentPass123!')
        response = self.client.get('/manage/users/')
        self.assertEqual(response.status_code, 403)

    # 8. Admin can activate/deactivate users
    def test_admin_can_toggle_user_active(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.post(f'/manage/users/{self.student.pk}/toggle/')
        self.assertEqual(response.status_code, 302)
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)

    # 9. Admin can access document management
    def test_admin_can_access_document_management(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.get('/documents/admin/')
        self.assertEqual(response.status_code, 200)

    # 10. Unauthenticated users cannot access admin pages
    def test_unauthenticated_cannot_access_admin_profile(self):
        response = self.client.get('/admin-profile/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response['Location'])

    # 11. Admin can access category management
    def test_admin_can_access_categories(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.get('/documents/admin/categories/')
        self.assertEqual(response.status_code, 200)

    # 12. Student cannot access category management
    def test_student_cannot_access_categories(self):
        self.client.login(username='student_test', password='StudentPass123!')
        response = self.client.get('/documents/admin/categories/')
        self.assertEqual(response.status_code, 403)

    # 13. Admin cannot deactivate themselves
    def test_admin_cannot_deactivate_self(self):
        self.client.login(username='admin_test', password='AdminPass123!')
        response = self.client.post(f'/manage/users/{self.admin.pk}/toggle/')
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)  # Should still be active