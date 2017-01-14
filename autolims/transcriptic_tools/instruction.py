import json
from autoprotocol.instruction import Instruction


class MiniPrep(Instruction):

    '''
    A miniprep instruction to isolate plasmid and genomic dna from bacteria
    
    Parameters
    ----------
    groups : list(dict)
        List of `miniprep` groups in the form of:
        .. code-block:: json
        [{
            "to": well,
            "from": well,
        },
        {
            "to": well,
            "from": well,
        }]
        
            
    
    '''

    def __init__(self, groups):
        super(MiniPrep, self).__init__({
            "op": "miniprep",
            "groups": groups
        })