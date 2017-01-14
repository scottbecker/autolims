from __future__ import print_function
import json
import io
from transcriptic_tools.custom_protocol import CustomProtocol as Protocol
import argparse
import sys
from autoprotocol.harness import Manifest, UserError, seal_on_store

if sys.version_info[0] >= 3:
    string_type = str
else:
    string_type = basestring

'''
    :copyright: 2016 by The Autoprotocol Development Team, see AUTHORS
        for more details.
    :license: BSD, see LICENSE for more details

'''

#This is copied verbatum except the one commented code block
def run(fn, protocol_name=None, seal_after_run=True,
        #this is new to allow testing
        config = None
        
        ):
    """
    Run the protocol specified by the function.

    If protocol_name is passed, use preview parameters from the protocol with
    the matching "name" value in the manifest.json file to run the given
    function.  Otherwise, take configuration JSON file from the command line
    and run the given function.

    Parameters
    ----------
    fn : function
        Function that generates Autoprotocol
    protocol_name :  str, optional
        str matching the "name" value in the manifest.json file
    seal_after_run : bool, optional
        Implicitly add a seal/cover to all stored refs within the protocol
        using seal_on_store()
    """
    #new to allow config
    if not config:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            'config',
            help='JSON-formatted protocol configuration file')
        args = parser.parse_args()
        #new
        config = args.config

    source = json.loads(io.open(config, encoding='utf-8').read())
    protocol = Protocol()
    if protocol_name:
        manifest_json = io.open('manifest.json', encoding='utf-8').read()
        manifest = Manifest(json.loads(manifest_json))
        
        # ---- This block is custom to dtx -----
        
        if not source:
            print(io.open('fake_protocol.json', encoding='utf-8').read())
            return
        
        
        # ------End of custom block ------
        
        params = manifest.protocol_info(protocol_name).parse(protocol, source)
    else:
        params = protocol._ref_containers_and_wells(source["parameters"])

    #----- This block is custom to dtx -----
    
    protocol.set_test_mode(params.get("test_mode",True))
    
    #----- End of New Block ------

    try:
        fn(protocol, params)
        if seal_after_run:
            seal_on_store(protocol)
            
        #---- This block is custom to dtx -----
        
        protocol.assert_valid_state()
        
        #---- End of New Block -------
            
    except UserError as e:
        print(json.dumps({
            'errors': [
                {
                    'message': e.message,
                    'info': e.info
                }
            ]
        }, indent=2))
        return
    #----- This block is custom to dtx -----
    except:    
        e = sys.exc_info()[1]
        
        additional_information = '\n'+'*'*50+\
            '\n inputs were %s\n'%json.dumps(source,
                                             indent=4)\
            +'*'*50+'\n'                        
        print(additional_information,file=sys.stderr)
        #aise type(e), e.message, sys.exc_info()[2]
        raise
    
    #----- End of New Block ------    
    

    print(json.dumps(protocol.as_dict(), indent=2))
