from autoprotocol import Unit
from transcriptic_tools.custom_protocol import CustomProtocol as Protocol
from transcriptic_tools.utils import ul, convert_to_wellgroup, ceil_volume, set_property
from transcriptic_tools.enums import Antibiotic,Reagent        
    
def copy_antibiotic_name(from_wellorcontainer, to_wellorcontainer):
    set_property(to_wellorcontainer,'antibiotic',get_antibiotic_name(from_wellorcontainer))

def get_antibiotic_name(wellorcontainer):
    wells = convert_to_wellgroup(wellorcontainer)
    
    return wells[0].properties['antibiotic']

