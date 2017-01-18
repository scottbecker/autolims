from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.utils.encoding import python_2_unicode_compatible
from transcriptic_tools import utils
from transcriptic_tools.utils import _CONTAINER_TYPES
from transcriptic_tools.enums import Temperature, CustomEnum
from django.core.exceptions import PermissionDenied
from autoprotocol import Unit
from transcriptic_tools.utils import round_volume
from db_file_storage.model_utils import delete_file, delete_file_if_needed


COVER_TYPES = set()
    
for container_type in _CONTAINER_TYPES.values():
    if container_type.cover_types:
        COVER_TYPES.update(container_type.cover_types)
    
COVER_TYPES = list(COVER_TYPES)

CONTAINER_STATUS_CHOICES = ['available','destroyed','returned','inbound','outbound','pending_destroy']
TEMPERATURE_NAMES = [temp.name for temp in Temperature]

RUN_STATUS_CHOICES = ['complete','accepted','in_progress','aborted','canceled']


ALIQUOT_EFFECT_TYPES = ['liquid_transfer_in','liquid_transfer_out','instructions']

DATA_TYPES = ['image_plate','platereader','measure']

RESOURCE_KINDS = ['Reagent','NucleicAcid']

DEFAULT_ORGANIZATION = 1

@python_2_unicode_compatible
class Organization(models.Model):
    name = models.CharField(max_length=200,blank=True,
                            default='')
    subdomain = models.CharField(max_length=200,blank=True,
                                 default='')
    
    users = models.ManyToManyField(User)
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    #custom fields
    updated_at = models.DateTimeField(auto_now=True)    
    
    def __str__(self):
        return self.name if self.name else 'Organization %s'%self.id

@python_2_unicode_compatible
class Project(models.Model):
    
    name = models.CharField(max_length=200,null=True,blank=True)
    
    bsl = models.IntegerField(default=1,blank=False,null=False)
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, 
                                     related_name='projects', 
                                     related_query_name='project',
                                     db_constraint=True,
                                     default=DEFAULT_ORGANIZATION
                                     )  
    
   
    
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    #custom fields
    updated_at = models.DateTimeField(auto_now=True)    
    
    def __str__(self):
        return self.name if self.name else 'Project %s'%self.id    
   
   
class RunContainer(models.Model):
    run = models.ForeignKey('Run', on_delete=models.CASCADE,
                            db_constraint=True,
                            related_name='run_containers', 
                            related_query_name='run_container',                            
                            )
    
    container = models.ForeignKey('Container', on_delete=models.CASCADE,
                               db_constraint=True,
                               related_name='run_containers', 
                               related_query_name='run_container',                                   
                            )    
    
    #the local label of the container within the run
    container_label = models.CharField(max_length=200)
    
        
    class Meta:
        unique_together = ('run', 'container_label', )        
    
   
@python_2_unicode_compatible 
class Run(models.Model):
    
    title = models.CharField(max_length=1000,null=True)
    
    status = models.CharField(max_length=200,
                          choices=zip(RUN_STATUS_CHOICES,
                                      RUN_STATUS_CHOICES),
                          null=False,
                          default='available',
                          blank=False)

    test_mode = models.BooleanField(blank=False,default=False)
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, 
                                related_name='runs', 
                                related_query_name='run',
                                db_constraint=True
                                )
    
    owner = models.ForeignKey(User)
    
    completed_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    aborted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    
    
    flagged = models.BooleanField(default=False,null=False)
    
    properties = JSONField(null=True,blank=True,
                           default=dict)   
    
    autoprotocol = JSONField(null=True,blank=True) 
    
    #we don't know what issued means

    updated_at = models.DateTimeField(auto_now=True)
    
    containers = models.ManyToManyField('Container', related_name='runs', 
                                 related_query_name='run',
                                 through='RunContainer',
                                 db_constraint=True,
                                 null=True,
                                 blank=True)
    
    def add_container(self, container_or_container_id, label):
        
        if isinstance(container_or_container_id,Container):
        
            RunContainer.objects.create(run=self,
                                      container=container_or_container_id,
                                      container_label = label
                                      ) 
        else:
            RunContainer.objects.create(run=self,
                                      container_id=container_or_container_id,
                                      container_label = label
                                      )       
            
    def remove_container(self,container_or_container_id):
        if isinstance(container_or_container_id, Container):
            RunContainer.objects.filter(run=self,
                                      container=container_or_container_id).delete()
        else:
            RunContainer.objects.filter(run=self,
                                      container_id=container_or_container_id).delete()            
        
        
                                 
                                 
    def save(self, *args, **kw):
        
        new_run = False
        
        if self.id is not None:
            orig_run = Run.objects.get(id=self.id)
            if orig_run.autoprotocol != self.autoprotocol:
                raise Exception, "unable to edit autoprotocol on a run"
        #new run
        else:
            new_run = True
            
        if not isinstance(self.properties,dict):
            self.properties = {}
            
        super(Run, self).save(*args, **kw)    
        
        if new_run:
            self.create_instructions()
            self.populate_containers()            
    
    def create_instructions(self):
        for i, instruction_dict in enumerate(self.autoprotocol['instructions']):
            instruction = Instruction.objects.create(run = self,
                                                     operation = instruction_dict,
                                                     sequence_no = i)
    
    def populate_containers(self):
        
        organization = self.project.organization
        
        for label, ref_dict in self.autoprotocol['refs'].items():
            if 'new' in ref_dict:
                
                storage_condition = ref_dict['store']['where'] if 'store' in ref_dict else None
                
                new_container = Container.objects.create(container_type_id = ref_dict['new'],
                                                      label = label,
                                                      test_mode = self.test_mode,
                                                      storage_condition = storage_condition,
                                                      status = 'available',
                                                      generated_by_run = self,
                                                      organization = organization
                                                      )
                self.add_container(new_container, label=label)
            else:
                
                #check that the existing container belongs to this org
                
                existing_container = Container.objects.get(id=ref_dict['id'])
                
                if existing_container.organization_id != self.project.organization_id:
                    raise PermissionDenied('Container %s doesn\'t belong to your org'%existing_container.id)
                
                self.add_container(existing_container, label=label)
    
    def __str__(self):
        return self.title     


@python_2_unicode_compatible
class Container(models.Model):
    
    #transcriptic fields
    container_type_id = models.CharField(max_length=200,
                                         choices=zip(_CONTAINER_TYPES.keys(),
                                                     _CONTAINER_TYPES.keys()))
    
    barcode = models.IntegerField(blank=True,null=True,unique=True, db_index=True)
    
    
    
    
    
    cover = models.CharField(max_length=200,
                             blank=True,
                             null=True,
                             choices=zip(COVER_TYPES,
                                         COVER_TYPES))
    
    test_mode = models.BooleanField(blank=False,default=False)
    
    label = models.CharField(max_length=1000,
                             blank=True,
                             default='',
                             db_index=True
                             )
    
    #location_id
    
    storage_condition = models.CharField(max_length=200,
                                         choices=zip(TEMPERATURE_NAMES,TEMPERATURE_NAMES),
                                         default=Temperature.ambient.name,
                                         null=True,
                                         blank=True)
    
    status = models.CharField(max_length=200,
                              choices=zip(CONTAINER_STATUS_CHOICES,
                                          CONTAINER_STATUS_CHOICES),
                              null=False,
                              default='available',
                              blank=False)
    
    expires_at = models.DateTimeField(null=True, blank=True)
    
    properties = JSONField(null=True,blank=True,
                       default=dict)
    
    generated_by_run = models.ForeignKey(Run, on_delete=models.CASCADE, 
                                     related_name='generated_containers', 
                                     related_query_name='generated_container',
                                     db_constraint=True,
                                     null=True,
                                     blank=True
                                     )
    
    

   
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, 
                                     related_name='containers', 
                                     related_query_name='container',
                                     db_constraint=True
                                     )
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    #custom fields
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        
        if self.barcode == '':
            self.barcode = None
            
        if self.expires_at == '':
            self.expires_at = None
            
        if self.generated_by_run == '':
            self.generated_by_run = None      
            
        if self.generated_by_run_id:
            #check that the project of the generated run and the current org are the same
            assert self.generated_by_run.project.organization_id == self.organization_id, "Can't use a container from one org in another org's run"
        
        if not isinstance(self.properties,dict):
            self.properties = {}            
        
        super(Container, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.label if self.label else 'Container %s'%self.id 

@python_2_unicode_compatible
class Aliquot(models.Model):
    
    name = models.CharField(max_length=200,null=True,blank=True)
    
    container = models.ForeignKey(Container, on_delete=models.CASCADE, 
                                  related_name='aliquots', 
                                  related_query_name='aliquot',
                                  db_constraint=True
                                  )
    well_idx = models.IntegerField(default=0,blank=False, null=False)
    
    #this is a string to keep precision
    
    volume_ul = models.CharField(max_length=200,null=False,default='0',blank=False)
  
    properties = JSONField(null=True,blank=True,
                       default=dict)    
    
    #resource
    #lot_no
    
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    #custom fields
    updated_at = models.DateTimeField(auto_now=True)    
    
    def add_volume(self, volume_to_add):
        """
        Handles volume strings, e.g. '5:nanoliter'
        """
        
        current_volume = Unit(self.volume_ul,'microliter')
        
        if isinstance(volume_to_add,basestring) and ':' in volume_to_add:
            added_volume = Unit(volume_to_add)
        else:
            added_volume = Unit(volume_to_add,'microliter')
            
        #instruments have at most 0.00uL precision
        new_volume = round_volume(current_volume+added_volume,2)
            
        self.volume_ul = str(new_volume.to('microliter').magnitude)
            
    
    def save(self,*args, **kwargs):
        if not isinstance(self.properties,dict):
            self.properties = {}        
        
        super(Aliquot, self).save(*args, **kwargs)
        
    
    def __str__(self):
        return '%s/%s'%(self.container.label,self.well_idx)
    
    
    
@python_2_unicode_compatible
class Instruction(models.Model):
    
    
    run = models.ForeignKey(Run,
                            on_delete=models.CASCADE,
                            related_name='instructions',
                            related_query_name='instruction',
                            db_constraint=True)
    
    operation = JSONField(blank=True,null=True) 
    
    sequence_no = models.IntegerField(null=False,blank=False,
                                      default=0)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)    
        
    updated_at = models.DateTimeField(auto_now=True)       
    
    
    
    class Meta:
        unique_together = ('run', 'sequence_no',)    
    
    def __str__(self):
        return 'Instruction %s'%self.id

class DataImage(models.Model):
    bytes = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=50)
    
class DataFile(models.Model):
    bytes = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=50)
    
@python_2_unicode_compatible
class Data(models.Model):
    
    name = models.CharField(max_length=200,null=True)
    
    data_type = models.CharField(max_length=200,
                                 choices=zip(DATA_TYPES,
                                             DATA_TYPES),
                                 null=False,
                                 default='available',
                                 blank=False)
    
    sequence_no = models.IntegerField(null=False,blank=False,
                                      default=0)    
    
    #upload_to isn't used but is required
    image = models.ImageField(upload_to='autolims.DataImage/bytes/filename/mimetype', null=True, blank=True)
    
    file = models.FileField(upload_to='autolims.DataFile/bytes/filename/mimetype', null=True, blank=True)
    
    json = JSONField(null=True,blank=True)
    
    instruction = models.ForeignKey(Instruction,
                                    on_delete=models.CASCADE,
                                    related_name='data',
                                    related_query_name='data',
                                    db_constraint=True,
                                    null=True,
                                    blank=True)
    
    run = models.ForeignKey(Run, on_delete=models.CASCADE, 
                            related_name='data', 
                            related_query_name='data',
                            db_constraint=True,
                            null=True,
                            blank=True
                            )
    
    class Meta:
        unique_together = ('run', 'sequence_no',)
        verbose_name_plural = "data"
        
    def save(self, *args, **kwargs):
        if self.run and self.instruction and self.run_id != self.instruction.run_id:
            raise Exception, "Instruction must belong to the run of this data object"
        
        super(Data, self).save(*args, **kwargs)
        
        delete_file_if_needed(self, 'file')
        delete_file_if_needed(self, 'image')        
        
    def delete(self, *args, **kwargs):
        super(Data, self).delete(*args, **kwargs)
        delete_file(self, 'file')
        delete_file(self, 'image')    
        
    
    def __str__(self):
        return "Data %s"%self.id

@python_2_unicode_compatible
class AliquotEffect(models.Model):
    #visible in network console as aliquot_effects when loading a well at transcriptic
    
    aliquot = models.ForeignKey(Aliquot,
                                on_delete=models.CASCADE,
                                related_name='aliquot_effects',
                                related_query_name='aliquot_effect',
                                db_constraint=True)
    
    
    instruction = models.ForeignKey(Instruction, on_delete=models.CASCADE, 
                                    related_name='aliquot_effects', 
                                    related_query_name='aliquot_effect', 
                                    db_constraint=True)
    
    data = JSONField(blank=True,null=True)  
    
    type = models.CharField(max_length=200,
                                   choices=zip(ALIQUOT_EFFECT_TYPES,
                                               ALIQUOT_EFFECT_TYPES),
                                   null=False,
                                   default=ALIQUOT_EFFECT_TYPES[0],
                                   blank=False)
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    
    
    updated_at = models.DateTimeField(auto_now=True)   
    
    
    def __str__(self):
        return 'Aliquot Effect %s'%self.id

@python_2_unicode_compatible
class Resource(models.Model):
    name = models.CharField(max_length=200,blank=True,
                            default='')
    
    description = models.TextField(blank=True,null=True)
    

    storage_condition = models.CharField(max_length=200,
                                         choices=zip(TEMPERATURE_NAMES,TEMPERATURE_NAMES),
                                         default=Temperature.ambient.name,
                                         null=True,
                                         blank=True)
    sensitivities = JSONField(null=True,blank=True,
                              default=list)
    
    properties = JSONField(null=True,blank=True,
                       default=dict)  
    
    kind = models.CharField(max_length=200,
                            choices=zip(RUN_STATUS_CHOICES,
                                        RUN_STATUS_CHOICES),
                            null=False,
                            default='available',
                            blank=False)    
    

    transcriptic_id = models.CharField(max_length=200,blank=True,null=True,
                                       default='', db_index=True,
                                       unique=True)

    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    
    
    updated_at = models.DateTimeField(auto_now=True)  
    
    def __str__(self):
        return self.name if self.name else 'Resource %s'%self.id
    
    def save(self, *args, **kwargs):
        
        if self.transcriptic_id == '':
            self.transcriptic_id = None
    
        if not isinstance(self.sensitivities,list):
            self.sensitivities = []           
    
        if not isinstance(self.properties,dict):
            self.properties = []          
    
        super(Resource, self).save(*args, **kwargs)    
    
    
    
#@python_2_unicode_compatible
#class Kit(models.Model):
#https://secure.transcriptic.com/_commercial/kits?format=json

#@python_2_unicode_compatible
#class KitItem(models.Model):
#https://secure.transcriptic.com/_commercial/kits/kit19jybkyf8ddv/kit_items?format=json
    

    
    