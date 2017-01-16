from django.test import TestCase
from autolims.models import (Organization, Project, Run,
                             User
                             )

class AutoprotocolInterpreterTestCase(TestCase):
    def setUpClass(self):
        self.org = Organization.objects.create(name="Org 2", subdomain="my_org")
        assert isinstance(self.org, Organization)
        self.project = Project.objects.create(name="Project 1",organization=self.org)
        
        self.user = User.objects.create_user('org 2 user', 
                                             email='test@test.com',
                                             password='top_secret')
        
        self.org.users.add(user)
        
        
        
        
    def setUp(self):
        pass
        
    def test_pipette(self):
        
        autoprotocol = """
        
        """
        
        
        run = Run.objects.create(title='Real Run',
                                 test_mode=False,
                                 autoprotocol=autoprotocol,
                                 project = self.project,
                                 owner=self.user)
        
        
        self.assertEqual(org2.name, 'test2')