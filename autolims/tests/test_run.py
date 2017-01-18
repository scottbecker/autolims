import os
import json
from django.test import TestCase
from transcriptic_tools.enums import Temperature
from autolims.models import (Organization, Run, Project, User, 
                             Container)



class RunTestCase(TestCase):
    
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

    def test_run_setup_all_new_containers(self):
        
        #same as https://secure.transcriptic.com/becker-lab/p19aqhcbep8ea/runs/r19u4jkqxhbt8
        with open(os.path.join(os.path.dirname(__file__),'data','oligosynthesis.json')) as f:
            autoprotocol = json.loads(f.read())
    
        run = Run.objects.create(title='Oligosynthesis Run',
                                 test_mode=False,
                                 autoprotocol=autoprotocol,
                                 project = self.project,
                                 owner=self.user)   
        assert isinstance(run,Run)
            
            
        #check that instructions have been created and they aren't executed
        
        self.assertEqual(run.instructions.count(),6)
        
        self.assertEqual(run.containers.count(),2)
        
        
    def test_run_setup_existing_containers(self):
        """ Check that Runs can be created that reference existing containers"""
        
        #create existing containers to be referenced
        
        existing_container = Container.objects.create(container_type_id = 'micro-1.5',
                                                   label = 'My Container',
                                                   test_mode = False,
                                                   storage_condition = Temperature.cold_80.name,
                                                   status = 'available',
                                                   organization = self.org
                                                   ) 
        
        
        
        #same as https://secure.transcriptic.com/becker-lab/p19aqhcbep8ea/runs/r19uqqkmr5u8f
        with open(os.path.join(os.path.dirname(__file__),'data','pellet_bacteria.json')) as f:
            autoprotocol = json.loads(f.read())        
        
        #update the autoprotocol to reference the correct id post import
        
        autoprotocol['refs']['bacteria_tube']['id'] = existing_container.id
        
        
        run = Run.objects.create(title='Pellet Bacteria Run',
                         test_mode=False,
                         autoprotocol=autoprotocol,
                         project = self.project,
                         owner=self.user)   
        assert isinstance(run,Run)
    
    
        #check that refs is updated correctly
        
        self.assertEqual(run.instructions.count(),13)
    
        self.assertEqual(run.containers.count(),4)
    
        
    