from django.db import transaction
from datetime import datetime
from autolims.models import (Instruction, Aliquot,Container,
                             AliquotEffect, Resource)

from transcriptic_tools.inventory import get_transcriptic_inventory
from transcriptic_tools.enums import Reagent

def get_or_create_aliquot_from_path(run_id, aliquot_path):
    """

    aliquot address is of the format "container label / index"
    
    """
    
    container_label, well_idx_str = aliquot_path.split('/')
    
    well_idx = int(well_idx_str)
    
    container = Container.objects.get(run_container__run_id = run_id,
                                      run_container__container_label = container_label)
    
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

def execute_pipette(instruction):
    raise NotImplementedError

def execute_cover(instruction):
    raise NotImplementedError

def execute_uncover(instruction):
    raise NotImplementedError

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

def execute_consolidate(instruction):
    raise NotImplementedError

def execute_dispense(instruction):
    raise NotImplementedError

def execute_stamp(instruction):
    raise NotImplementedError

def mark_instruction_complete(instruction):
    instruction.completed_at = datetime.now()
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
    
    #sequence no asc
    ordered_instructions = run.instructions.all().order_by('sequence_no')
    
    for instruction in ordered_instructions:
        assert isinstance(instruction,Instruction)
        exec_function = get_instruction_executer(instruction.operation['op'])
        
        exec_function(instruction)
        
    #update properties and names of aliquots (see outs of autoprotocol)
    for container_label, out_info in run.autoprotocol['outs'].items():
        
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
    
    
    run.status = 'complete'
    run.completed_at = datetime.now()
    run.save()