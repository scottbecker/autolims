import os
import json
from django.test import TestCase
from templatetags import run_tags


class TemplateTagsTestCase(TestCase):
    
   
    def test_aliquot_to_container_label(self):
        self.assertEqual(run_tags.aliquot_to_container_label('plate 1/0'),
                         'plate_1')
        
    def test_to_safe_label(self):
        self.assertEqual(run_tags.to_safe_label('plate 1'),
                         'plate_1')    