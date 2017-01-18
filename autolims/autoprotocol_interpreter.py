from django.db import transaction
from datetime import datetime
from autolims.models import (Instruction, Aliquot,Container,
                             AliquotEffect)

from transcriptic_tools.inventory import get_transcriptic_inventory
from transcriptic_tools.enums import Reagent

def get_or_create_aliquot_from_path(run, aliquot_path):
    """

    aliquot address is of the format "container label / index"
    
    """
    
    container_label, well_idx_str = aliquot_path.split('/')
    
    well_idx = int(well_index_str)
    
    container = Container.objects.filter(runs__run_id=instruction.run_id,
                                         runs__container_label=container_label).first()
    
    assert isinstance(container,Container)
    
    #check if the aliquot exists
    
    aliquot_query = container.aliquots.filter(well_idx = well_idx )
    
    if aliquot_query.exists():
        return aliquot_query.first()
    
    return Aliquot.objects.create(well_idx = well_idx,
                           container = container,
                           volume_ul='0')
    

# ------ Instruction Executers --------

def execute_oligosynthesis(instruction):
    operation = instruction.operation
    
    for oligo_info in operation['oligos']:
        
        aliquot = get_or_create_aliquot_from_path(instruction.run, oligo_info['destination'])
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
    
    resource_name = operation['resource_id']
    
    for oligo_info in operation['oligos']:
        
        aliquot = get_or_create_aliquot_from_path(instruction.run, oligo_info['destination'])
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
    
    ordered_instructions = run.instructions.all().order_by('-sequence_no')
    
    for instruction in ordered_instructions:
        assert isinstance(instruction,Instruction)
        exec_function = get_instruction_executer(instruction.operation['op'])
        
        exec_function(instruction)
        