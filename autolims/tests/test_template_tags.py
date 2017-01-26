import os
import json
from django.test import TestCase
from templatetags import run_tags

from autolims.models import Resource


class TemplateTagsTestCase(TestCase):
    
   
    def test_aliquot_to_container_label(self):
        self.assertEqual(run_tags.aliquot_to_container_label('plate 1/0'),
                         'plate_1')
        
    def test_to_safe_label(self):
        self.assertEqual(run_tags.to_safe_label('plate 1'),
                         'plate_1')    
        
    def test_resource_id_to_name(self):
        
        te_resource = Resource.objects.get(name='TE')
        
        self.assertEqual(run_tags.resource_id_to_name('rs17pwyc754v9t'), 
                         'TE')
        
        self.assertEqual(run_tags.resource_id_to_name(str(te_resource.id)), 
                         'TE')
        
        self.assertEqual(run_tags.resource_id_to_name(te_resource.id), 
                         'TE')        