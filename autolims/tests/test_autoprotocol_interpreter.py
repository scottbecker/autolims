from django.test import TestCase
import json
import os

from autolims.autoprotocol_interpreter import execute_run
from autolims.models import (Organization, Project, Run,
                             Sample,
                             User
                             )

class AutoprotocolInterpreterTestCase(TestCase):
    
    @classmethod
    def setUpClass(cls):
        
        super(RunTestCase,cls).setUpClass()
        
        cls.org = Organization.objects.create(name="Org 2", subdomain="my_org")
        assert isinstance(cls.org, Organization)
        cls.project = Project.objects.create(name="Project 1",organization=cls.org)
        
        cls.user = User.objects.create_user('org 2 user', 
                                             email='test@test.com',
                                             password='top_secret')
        
        cls.org.users.add(cls.user)
        
        
        
        
    def setUp(self):
        pass
        
    def test_oligosynthesis(self):
        
        #same as https://secure.transcriptic.com/becker-lab/p19aqhcbep8ea/runs/r19u4jkqxhbt8
        with open(os.path.join(os.path.dirname(__file__),'data','oligosynthesis.json')) as f:
            autoprotocol = json.loads(f.read())
        
        run = Run.objects.create(title='Real Run',
                                 test_mode=False,
                                 autoprotocol=autoprotocol,
                                 project = self.project,
                                 owner=self.user)
        assert isinstance(run, Run)
        
        execute_run(run)
        
        #two Samples should have been made
        self.assertEqual(run.refs.count(),2)
        
        
    #@classmethod
    #def tearDownClass(cls):
        #pass
        
        
        