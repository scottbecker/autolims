from django.test import TestCase
import json
import os
from decimal import Decimal
from autolims.autoprotocol_interpreter import execute_run
from autolims.models import (Organization, Project, Run,
                             Container,
                             User, Aliquot
                             )

class AutoprotocolInterpreterTestCase(TestCase):
    
    @classmethod
    def setUpClass(cls):
        
        super(AutoprotocolInterpreterTestCase,cls).setUpClass()
        
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
        
        #two Containers should have been made
        self.assertEqual(run.refs.count(),2)
        
        #check that aliquots have been made and the volumes have been updated for those refs
        
        for container in run.refs.all():
            assert isinstance(container,Container)
            aliquot = container.aliquots.first() # type: Aliquot
            assert isinstance(aliquot, Aliquot)
            self.assertEqual(Decimal(aliquot.volume_ul),
                             250)
            
            #ensure that properties are updated on wells
            
            self.assertDictEqual({
                #created by the oligosynthesis command
                'Sequence':'CCAGCTCGTTGAGTTTCTCC',
                #this really should be 25:nm but autoprotocol has it wrong and its a hassle to change
                'scale':'25nm',
                #created by the out
                'Concentration': '100uM',
                },
                                 aliquot.properties
                                 )
            
        
            #check that there are valid aliquot effects (aka well history on those refs)
            self.assertEqual(aliquot.aliquot_effects.count(),2)
            
            ordered_well_history = aliquot.aliquot_effects.all().order_by('-id')
            
            
            ordered_instructions = [aliquot_effect.generating_instruction \
                                  for aliquot_effect in ordered_well_history]
            
            self.assertListEqual([instruction.operation['op'] \
                                  for instruction in ordered_instructions],
                             ['oligosynthesize','provision'])
            
            self.assertListEqual([instruction.sequence_no \
                                  for instruction in ordered_instructions],
                                 [0,1])            
            
            #check that the instructions are marked executed
            self.assertTrue(all([instruction.completed_at for instruction in ordered_instructions]))
            
        
            
        #check that the run is marked complete            
        self.assertEqual(run.status,'complete')
        self.assertTrue(run.completed_at)
        
        
    def test_existing_containers(self):
        pass
            
        #ensure that volumes on existing inventory are updated
        #ensure that any temp containers are marked discarded
            
        
        
        
        
        
    #@classmethod
    #def tearDownClass(cls):
        #pass
        
        
        