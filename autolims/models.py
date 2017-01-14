from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from autoprotocol.container_type import _CONTAINER_TYPES



#iterate through container types




@python_2_unicode_compatible
class Sample(models.Model):
    
    container_type_id = models.CharField(max_length=200,
                                         choices=zip(_CONTAINER_TYPES.keys(),
                                                     _CONTAINER_TYPES.keys()))
    
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    def __str__(self):
        return self.question_text    

    def was_published_recently(self):
        return self.pub_date >= timezone.now() - datetime.timedelta(days=1)  