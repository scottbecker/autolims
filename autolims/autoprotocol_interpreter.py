from django.db import transaction
from django.utils import timezone
from autolims.models import (Instruction, Aliquot,Container,
                             AliquotEffect, Resource)

from transcriptic_tools.inventory import get_transcriptic_inventory
from transcriptic_tools.enums import Reagent
from transcriptic_tools.utils import _CONTAINER_TYPES



def get_or_create_aliquot_from_path(run_id, aliquot_path):
    """

    aliquot address is of the format "container label / index"
    
    """
    
    container_label, well_idx_str = aliquot_path.split('/')
    
    well_idx = int(well_idx_str)
    
    container = Container.get_container_from_run_and_container_label(run_id, 
                                                                    container_label)
    
    assert isinstance(container,Container)
    
    #check if the aliquot exists
    
    aliquot_query = container.aliquots.filter(well_idx = well_idx )
    
    if aliquot_query.exists():
        return aliquot_query.first()
    
    return Aliquot.objects.create(well_idx = well_idx,
                           container = container,
                           volume_ul='0')
    

# ------ Instruction Executers --------

def execute_oligosynthesize(instruction):
    operation = instruction.operation
    
    for oligo_info in operation['oligos']:
        
        aliquot = get_or_create_aliquot_from_path(instruction.run_id, oligo_info['destination'])
        aliquot.properties.update({'sequence':oligo_info['sequence'],
                                   'scale':oligo_info['scale'],
                                   'purification':oligo_info['purification']
                                   })
        aliquot.save()
        
        AliquotEffect.objects.create(aliquot = aliquot,
                                     instruction = instruction,
                                     type = 'instruction'
                                    )
        
    #@TODO: make an actual api call to order the oligos
        
    
    mark_instruction_complete(instruction)
    
    
def execute_acoustic_transfer(instruction):
    raise NotImplementedError
    
def execute_gel_purify(instruction):
    raise NotImplementedError

def execute_gel_separate(instruction):
    raise NotImplementedError

def execute_magnetic_transfer(instruction):
    raise NotImplementedError



def simplify_pipette_operations(pipette_group):
    #each group can only have one key

    #check this assumption

    if len(pipette_group.keys())!=1:
        raise NotImplementedError, "We aren't ready for groups to have multiple keys."

    pipette_operation_type = pipette_group.keys()[0]

    pipette_operation_info = pipette_group[pipette_operation_type]

    #dicts of with keys to_aq_path, from_aq_path, volume_str
    volume_transfers = []

    if pipette_operation_type == 'transfer':
        for transfer_op in pipette_operation_info:
            volume_transfers.append({
                'to_aq_path':transfer_op['to'],
                'from_aq_path':transfer_op['from'],
                'volume_str':transfer_op['volume']}
                                    )

    elif pipette_operation_type == 'distribute':
        distribute_op = pipette_operation_info

        for destination_info in distribute_op['to']:
            volume_transfers.append({
                'to_aq_path':destination_info['well'],
                'from_aq_path':distribute_op['from'],
                'volume_str':destination_info['volume']}
                                    )

    elif pipette_operation_type == 'consolidate':
        consolidate_op = pipette_operation_info

        for source_info in consolidate_op['from']:
            volume_transfers.append({
                'to_aq_path':consolidate_op['to'],
                'from_aq_path':source_info['well'],
                'volume_str':source_info['volume']}
                                    )
    elif pipette_operation_type == 'mix':
        pass        
    else:
        raise NotImplementedError, "Uknown pipette operation, %s"%pipette_operation_type    


    return volume_transfers


def execute_pipette(instruction):
    """
    transfer, distribute, consolidate, mix are all pipette operations
    """
    
    operation = instruction.operation
    
    for pipette_group in operation['groups']:
        
        
        volume_transfers = simplify_pipette_operations(pipette_group)
        
        
        for transfer_info in volume_transfers:
            from_aq = get_or_create_aliquot_from_path(instruction.run, transfer_info['from_aq_path'])
            to_aq = get_or_create_aliquot_from_path(instruction.run, transfer_info['to_aq_path'])        
            
            added_volume = to_aq.add_volume(transfer_info['volume_str'])
            from_aq.subtract_volume(transfer_info['volume_str'])
        
            to_aq.save()
            from_aq.save()
        
            AliquotEffect.objects.create(aliquot = to_aq,
                                         instruction = instruction,
                                         data = {"source":{
                                             'container_id': from_aq.container_id,
                                             'well_idx': from_aq.well_idx
                                             },
                                                 'volume_ul': str(added_volume.to('microliter').magnitude) 
                                                 },                                             
                                         type = 'liquid_transfer_in'
                                         )     
        
            AliquotEffect.objects.create(aliquot = from_aq,
                                         instruction = instruction,
                                         data = {"destination":{
                                             'container_id': to_aq.container_id,
                                             'well_idx': to_aq.well_idx
                                             },
                                                 'volume_ul': str(added_volume.to('microliter').magnitude) 
                                                 },
                                         type = 'liquid_transfer_out'
                                         )            
        
        
        
    mark_instruction_complete(instruction)
  
def execute_cover(instruction):
    container = Container.get_container_from_run_and_container_label(instruction.run_id, 
                                                                     instruction.operation['object'])

    container.cover = instruction.operation['lid']
    container.save()

def execute_uncover(instruction):
    container = Container.get_container_from_run_and_container_label(instruction.run_id, 
                                                                     instruction.operation['object'])

    container.cover = None
    container.save()

def execute_provision(instruction):
    operation = instruction.operation
    
    resource_id = operation['resource_id']
    
    #strings are transcriptic id's
    if isinstance(resource_id,basestring):
        resource = Resource.objects.get(transcriptic_id=resource_id)
    else:
        resource = Resource.objects.get(id=resource_id)
    
    for destination_info in operation['to']:
        
        aliquot = get_or_create_aliquot_from_path(instruction.run, destination_info['well'])
        aliquot.properties.update({'resource_id':resource.id,
                                   'resource_name': resource.name
                                   })
        aliquot.add_volume(destination_info['volume'])
        aliquot.save()
        
        AliquotEffect.objects.create(aliquot = aliquot,
                                     instruction = instruction,
                                     type = 'instructions'
                                    )
        
    mark_instruction_complete(instruction)

def execute_dispense(instruction):
    
    
    operation = instruction.operation
    
    resource_id = operation['resource_id']
    
    destination_container = Container.get_container_from_run_and_container_label(instruction.run_id, 
                                                                    operation['object'])
    
    
    #strings are transcriptic id's
    if isinstance(resource_id,basestring):
        resource = Resource.objects.get(transcriptic_id=resource_id)
    else:
        resource = Resource.objects.get(id=resource_id)
    
    for column_info in operation['columns']:
        
        column_id = column_info['column']
        
        #convert columns into well indexes
        well_indexes = destination_container.get_column_well_indexes(column_id)
        
        for well_idx in well_indexes:
        
            aliquot, created = Aliquot.objects.get_or_create(well_idx = well_idx,
                                             container = destination_container)
            aliquot.properties.update({'resource_id':resource.id,
                                       'resource_name': resource.name
                                       })
            aliquot.add_volume(column_info['volume'])
            aliquot.save()
            
            AliquotEffect.objects.create(aliquot = aliquot,
                                         instruction = instruction,
                                         type = 'instructions'
                                        )
        
    mark_instruction_complete(instruction)

def execute_stamp(instruction):
    raise NotImplementedError

def mark_instruction_complete(instruction):
    instruction.completed_at = timezone.now()
    instruction.save()


def get_instruction_executer(operation):
    
    execute_func_name = 'execute_%s'%operation
    
    if execute_func_name in globals():
        return globals()[execute_func_name]
    
    return globals()['mark_instruction_complete']
    

@transaction.atomic
def execute_run(run):
    """
    Executes all the autoprotocol associated with a run.
    Updates the status of the run.
    Updates volumes of all inventory used by the run
    Create new samples as needed.
    
    Ensures that test runs can't access real inventory (and visa versa)
    
    update properties and names of aliquots (see outs of autoprotocol)
    
    Mark Samples as discarded as needed
    
    """
    
    #ensure that the run is accepted
    assert run.status=='accepted','Run must be in accepted state to execute. Currently %s'%run.status
    
    #sequence no asc
    ordered_instructions = run.instructions.all().order_by('sequence_no')
    
    for instruction in ordered_instructions:
        assert isinstance(instruction,Instruction)
        exec_function = get_instruction_executer(instruction.operation['op'])
        
        exec_function(instruction)
        
    #update properties and names of aliquots (see outs of autoprotocol)
  
    
    for container_label, out_info in run.protocol.get('outs',{}).items():
        
        for well_idx_str, well_info in out_info.items():
            aq = get_or_create_aliquot_from_path(run.id, '%s/%s'%(container_label,
                                                                  well_idx_str))
            
            updated = False
            if 'name' in well_info:
                updated=True
                aq.name = well_info['name']
                
            if 'properties' in well_info:
                updated=True
                aq.properties.update(well_info['properties'])
                
            if updated:
                aq.save()
                
                
    
    #discard containers
    for container_label, ref_info in run.protocol['refs'].items():

        if ref_info.get('discard'):
        
            container = Container.get_container_from_run_and_container_label(run.id,
                                                                             container_label)
            
            container.status = 'destroyed'
            
            container.save()
    
    
    run.status = 'complete'
    run.completed_at = timezone.now()
    run.save()