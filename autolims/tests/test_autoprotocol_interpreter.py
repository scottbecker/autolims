from django.test import TestCase
import json
import os
from decimal import Decimal
from autolims.autoprotocol_interpreter import execute_run
from autolims.models import (Organization, Project, Run,
                             Container,
                             User, Aliquot
                             )
from transcriptic_tools.enums import Temperature

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
        self.assertEqual(run.containers.count(),2)
        
        #check that aliquots have been made and the volumes have been updated for those containers
        
        for container in run.containers.all():
            assert isinstance(container,Container)
            aliquot = container.aliquots.first() # type: Aliquot
            assert isinstance(aliquot, Aliquot)
            self.assertEqual(Decimal(aliquot.volume_ul),
                             250)
            
            #ensure that properties are updated on wells
            
            self.assertDictContainsSubset({
                #created by the oligosynthesis command
                'sequence':'CCAGCTCGTTGAGTTTCTCC',
                #this really should be 25:nm but autoprotocol has it wrong and its a hassle to change
                'scale':'25nm',
                #created by the out
                'Concentration': '100uM',
                },
                                        aliquot.properties
                                 )
            
        
            #check that there are valid aliquot effects (aka well history on those containers)
            self.assertEqual(aliquot.aliquot_effects.count(),2)
            
            ordered_well_history = aliquot.aliquot_effects.all().order_by('id')
            
            
            ordered_instructions = [aliquot_effect.instruction \
                                  for aliquot_effect in ordered_well_history]
            
            self.assertListEqual([instruction.operation['op'] \
                                  for instruction in ordered_instructions],
                             ['oligosynthesize','provision'])
            
            self.assertListEqual([instruction.sequence_no \
                                  for instruction in ordered_instructions],
                                 [0,3])            
            
            #check that the instructions are marked executed
            self.assertTrue(all([instruction.completed_at for instruction in ordered_instructions]))
            
        
        self.assertTrue(all([container.status=='available' for container in run.containers.all()]))        
            
        #check that the run is marked complete            
        self.assertEqual(run.status,'complete')
        self.assertTrue(run.completed_at)
        
        
    def test_existing_containers(self):
        #create existing containers to be referenced

        existing_container = Container.objects.create(container_type_id = 'micro-1.5',
                                                      label = 'bacteria_tube',
                                                      test_mode = False,
                                                      storage_condition = Temperature.cold_80.name,
                                                      status = 'available',
                                                      organization = self.org
                                                      )
        existing_aq = Aliquot.objects.create(container = existing_container,
                               well_idx = 0,
                               volume_ul = "115")
            
        #same as https://secure.transcriptic.com/becker-lab/p19aqhcbep8ea/runs/r19uqqkmr5u8f
        with open(os.path.join(os.path.dirname(__file__),'data','pellet_bacteria.json')) as f:
            autoprotocol = json.loads(f.read())             

        #update the autoprotocol to reference the correct id post import

        autoprotocol['refs']['bacteria_tube']['id'] = existing_container.id

        run = Run.objects.create(title='Real Run',
                                 test_mode=False,
                                 autoprotocol=autoprotocol,
                                 project = self.project,
                                 owner=self.user)
        assert isinstance(run, Run)
    
        execute_run(run)

        #two Containers should have been made
        self.assertEqual(run.containers.count(),4)        

        #ensure that volumes on existing inventory are updated  (40.12)
        
        existing_aq = Aliquot.objects.get(id=existing_aq.id)
        
        self.assertEqual(Decimal(existing_aq.volume_ul), Decimal('40.12'))
        
        #ensure all aliquots on the growth plate were made (32) and have the same volume (15ul)
        
        growth_plate = run.containers.get(label='growth_plate')
        
        self.assertEqual(growth_plate.aliquots.count(),4*8)
        
        self.assertTrue(all([Decimal(aq.volume_ul)==Decimal('15') for aq in growth_plate.aliquots.all()]))
        
        #ensure containers are discarded
        
        destroyed_containers = Container.objects.filter(run_container__run_id = run.id,
                                                        run_container__container_label__in = ['absorbance_plate',
                                                                                              'bacteria_tube',
                                                                                              'trash_plate'])
        
        self.assertEqual(destroyed_containers.count(),3)
        
        self.assertTrue(all([container.status=='destroyed' for container in destroyed_containers]))
        
        
    def test_pipette_operations(self):
    
        #same as https://secure.transcriptic.com/becker-lab/p19aqhcbep8ea/runs/r19uvbk55tb54
        with open(os.path.join(os.path.dirname(__file__),'data','pipette_operations.json')) as f:
            autoprotocol = json.loads(f.read())             
    
        run = Run.objects.create(title='Pipette Operation Run',
                                 test_mode=False,
                                 autoprotocol=autoprotocol,
                                 project = self.project,
                                 owner=self.user)
        assert isinstance(run, Run)
    
        execute_run(run)
    
        self.assertEqual(run.containers.count(),1)   
        self.assertEqual(run.instructions.count(),2)    
    
        test_plate = run.containers.get(label='test plate')
        
        volumes = [Decimal('745'),Decimal('85'),Decimal('20'),Decimal('20'),Decimal('30')]
        
        self.assertEqual(test_plate.aliquots.count(),5)
        
        for aq in test_plate.aliquots.all():
            assert isinstance(aq, Aliquot)
            self.assertEqual(Decimal(aq.volume_ul),volumes[aq.well_idx])
        
    