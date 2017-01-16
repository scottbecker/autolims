from django.test import TestCase
from autolims.models import Organization

class OrganizationTestCase(TestCase):
    def setUp(self):
        Organization.objects.create(name="test", subdomain="test")

    def test_organization(self):
        org2 = Organization.objects.create(name="test2", subdomain="test2")
        self.assertEqual(org2.name, 'test2')