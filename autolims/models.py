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
from helper_funcs import str_respresents_int

#create token imports
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from django.conf import settings


COVER_TYPES = set()
    
for container_type in _CONTAINER_TYPES.values():
    if container_type.cover_types:
        COVER_TYPES.update(container_type.cover_types)
    
COVER_TYPES = list(COVER_TYPES)

CONTAINER_STATUS_CHOICES = ['available','destroyed','returned','inbound','outbound','pending_destroy']
TEMPERATURE_NAMES = [temp.name for temp in Temperature]

RUN_STATUS_CHOICES = ['accepted','in_progress','complete','aborted','canceled']

ALIQUOT_EFFECT_TYPES = ['liquid_transfer_in','liquid_transfer_out','instructions']

DATA_TYPES = ['image_plate','platereader','measure']

RESOURCE_KINDS = ['Reagent','NucleicAcid']

DEFAULT_ORGANIZATION = 1

@python_2_unicode_compatible
class Organization(models.Model):
    name = models.CharField(max_length=200,blank=True,
                            default='')
    subdomain = models.CharField(max_length=200,
                                 unique=True,
                                 db_index=True)
    
    users = models.ManyToManyField(User,
                                   related_name='organizations',
                                   related_query_name='orgnization',
                                   db_constraint=True)
    
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    

    #custom fields
    updated_at = models.DateTimeField(auto_now=True)    
    
    def get_absolute_url(self):
        return "/%s/" % self.subdomain    
    
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
    
    def get_absolute_url(self):
        return "/%s/%s/runs"%(self.organization.subdomain,
                                  self.id)
    
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
    
    title = models.CharField(max_length=1000,null=True,blank=True)
    
    status = models.CharField(max_length=200,
                          choices=zip(RUN_STATUS_CHOICES,
                                      RUN_STATUS_CHOICES),
                          null=False,
                          default='accepted',
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
    
    protocol = JSONField(null=True,blank=True) 
    
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
            if orig_run.protocol != self.protocol:
                raise Exception, "unable to edit autoprotocol on a run"
            
            if not self.title:
                self.name = 'Run %s'%self.id
        
        #new run
        else:
            new_run = True
            self.convert_transcriptic_resource_ids()
            
        if not isinstance(self.properties,dict):
            self.properties = {}
            
        assert self.status in RUN_STATUS_CHOICES,\
            'status \'%s\' not found in allowed options %s'%(self.status, str(RUN_STATUS_CHOICES))
                
        super(Run, self).save(*args, **kw)
        
        #only hit if this is a new Run
        if not self.title:
            self.title = self.name = 'Run %s'%self.id
            super(Run, self).save(*args, **kw)
        
        if new_run:
            self.create_instructions()
            self.populate_containers()            
    
    def convert_transcriptic_resource_ids(self):
        for operation in self.protocol['instructions']:
            if operation['op'] != 'provision': continue
            if not isinstance(operation['resource_id'], basestring) or \
               str_respresents_int(operation['resource_id']): continue
            
            resource = Resource.objects.get(transcriptic_id = operation['resource_id'])
            
            operation['resource_id'] = resource.id
                                   
                                
    def create_instructions(self):
        for i, instruction_dict in enumerate(self.protocol['instructions']):
            instruction = Instruction.objects.create(run = self,
                                                     operation = instruction_dict,
                                                     sequence_no = i)
    
    def populate_containers(self):
        
        organization = self.project.organization
        
        for label, ref_dict in self.protocol['refs'].items():
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
                
                if existing_container.status == 'destroyed':
                    raise Exception('Destoryed container referenced in run: Container id %s'%existing_container.id)
                
                if existing_container.organization_id != self.project.organization_id:
                    raise PermissionDenied('Container %s doesn\'t belong to your org'%existing_container.id)
                
                self.add_container(existing_container, label=label)
    
    def __str__(self):
        return self.title    
    
    def get_absolute_url(self):
        return "/%s/%s/runs/%s"%(self.project.organization.subdomain,
                                  self.project_id, self.id)    
    
    class Meta:
        index_together = [
            ['project','test_mode','status']
        ]


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
    
    @classmethod
    def get_container_from_run_and_container_label(cls, run_id, container_label):
        return cls.objects.get(run_container__run_id = run_id,
                               run_container__container_label = container_label)
    
    @property
    def col_count(self):
        container_type = _CONTAINER_TYPES[self.container_type_id]
        return container_type.col_count
    
    @property
    def row_count(self):
        container_type = _CONTAINER_TYPES[self.container_type_id]
        return container_type.row_count()    
    
    def well_indexes_from(self, start, num, columnwise=False):
        """
        Return a list of indexes belonging to this Container starting from
        the index indicated (in integer or string form) and including the
        number of proceeding wells specified. well indexes are counted from the
        starting well rowwise unless columnwise is True.

        Parameters
        ----------
        start : Well, int, str
            Starting well specified as a Well object, a human-readable well
            index or an integer well index.
        num : int
            Number of wells to include in the Wellgroup.
        columnwise : bool, optional
            Specifies whether the wells included should be counted columnwise
            instead of the default rowwise.

        """        
        
        container_type = _CONTAINER_TYPES[self.container_type_id]
        
        start = container_type.robotize(start)
        
        if columnwise:
            row, col = container_type.decompose(start)
            num_rows = self.row_count
            start = col * num_rows + row      
            
    
        return range(start,start + num)
    
    def get_absolute_url(self):
        return "/%s/containers/%s"%(self.organization.subdomain,
                                  self.id)    
    
    def get_column_well_indexes(self, column_index_or_indexes):
            
        if isinstance(column_index_or_indexes,list):
            result = []
            for column_index in column_index_or_indexes:
                result+=self.get_column_wells(self, column_index)
                
            return result
        
        column_index = column_index_or_indexes
        
        num_cols = self.col_count
        num_rows = self.row_count 
        
        if column_index >= num_cols:
            raise ValueError('column index %s is too high, only %s cols in this container'%(column_index,num_cols))
        
        start = num_rows*column_index
        
        return self.all_well_indexes(columnwise=True)[start:start+num_rows]
    
    def all_well_indexes(self, columnwise=False):
        """
        Return a list of indexes representing all Wells belonging to this Container.

        Parameters
        ----------
        columnwise : bool, optional
            returns the WellGroup columnwise instead of rowwise (ordered by
            well index).

        """
        if columnwise:
            num_cols = self.col_count
            num_rows = self.row_count
            
            return [row * num_cols + col
                    for col in xrange(num_cols)
                    for row in xrange(num_rows)]
        else:
            return range(0,self.col_count*self.row_count)  
    
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
        return '%s (%s)'%(self.label,self.id) if self.label else 'Container %s'%self.id 

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
    
    @property
    def human_index(self):
        
        container_type = _CONTAINER_TYPES[self.container.container_type_id]
        
        
        return container_type.humanize(self.well_idx)
        
    def add_volume(self, volume_to_add):
        """
        Handles volume strings, e.g. '5:nanoliter'
        """
        
        current_volume = Unit(self.volume_ul,'microliter')
        
        if isinstance(volume_to_add,basestring) and ':' in volume_to_add:
            added_volume = Unit(volume_to_add)
        else:
            added_volume = Unit(volume_to_add,'microliter')
            
        added_volume = round_volume(added_volume,2)
        
        #instruments have at most 0.00uL precision
        new_volume = round_volume(current_volume+added_volume,2)
            
        self.volume_ul = str(new_volume.to('microliter').magnitude)
        
        return added_volume
    
    def subtract_volume(self, volume_to_add):
        """
        Handles volume strings, e.g. '5:nanoliter'
        """
    
        current_volume = Unit(self.volume_ul,'microliter')
    
        if isinstance(volume_to_add,basestring) and ':' in volume_to_add:
            subtracted_volume = Unit(volume_to_add)
        else:
            subtracted_volume = Unit(volume_to_add,'microliter')
    
        return self.add_volume(-1*subtracted_volume)   
            
    
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
    

    
# This code is triggered whenever a new user has been created and saved to the database

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)