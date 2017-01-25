""" 

Derived from Brian Naughton @ http://blog.booleanbiotech.com/genetic_engineering_pipeline_python.html

"""
from __future__ import print_function
import datetime
import math
import re
import autoprotocol
from autoprotocol import Unit
from autoprotocol.unit import UnitValueError
from autoprotocol.container import Container
from autoprotocol.container_type import _CONTAINER_TYPES, ContainerType
from autoprotocol.protocol import Protocol, WellGroup, Well
from autoprotocol.protocol import Ref # "Link a ref name (string) to a Container instance."
import requests
import logging
import json
import sys
import numpy
import os
import requests
from lib import round_up
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning, SNIMissingWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(SNIMissingWarning)
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)

#http debugging
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
    
#change this to 2 to show raw http request/responses
http_client.HTTPConnection.debuglevel = 0

experiment_name = ''

# Transcriptic authorization

CONFIG_INITIALIZED = False
TSC_HEADERS = None
ORG_NAME = None

def initialize_config():
    global TSC_HEADERS, CONFIG_INITIALIZED, ORG_NAME
    
    if CONFIG_INITIALIZED: return
    
    if "--test" in sys.argv:
        auth_file = '../test_mode_auth.json'
    else:
        auth_file = '../auth.json'
    
    auth_file_path = os.path.join(os.path.dirname(__file__), auth_file)
    
    auth_config = json.load(open(auth_file_path))
    TSC_HEADERS = {k:v for k,v in auth_config.items() if k in ["X_User_Email","X_User_Token"]}
    
    ORG_NAME = auth_config['org_name']
    
    CONFIG_INITIALIZED = True

# Correction to Transcriptic-specific dead volumes
_CONTAINER_TYPES['96-deep-kf'] = _CONTAINER_TYPES['96-deep-kf']._replace(cover_types = ["standard"])

_CONTAINER_TYPES['6-flat-tc'] = ContainerType(name="6-well tissue cell culture plate",
                                              well_count=6,
                                              well_depth_mm=None,
                                              well_volume_ul=Unit(5000.0, "microliter"),
                                              well_coating=None,
                                              sterile=False,
                                              cover_types=["standard", "universal"],
                                              seal_types=None,
                                              capabilities=["cover", "incubate", "image_plate"],
                                              shortname="6-flat-tc",
                                              is_tube=False,
                                              col_count=3,
                                              dead_volume_ul=Unit(400, "microliter"),
                                              safe_min_volume_ul=Unit(600, "microliter"))


_CONTAINER_TYPES['96-flat-tc'] = ContainerType(name="96-well tissue cell culture flat-bottom plate",
                                               well_count=96,
                                               well_depth_mm=None,
                                               well_volume_ul=Unit(340.0, "microliter"),
                                               well_coating=None,
                                               sterile=False,
                                               is_tube=False,
                                               cover_types=["standard", "universal", "low_evaporation"],
                                               seal_types=None,
                                               capabilities=["pipette", "spin", "absorbance",
                                                             "fluorescence", "luminescence",
                                                             "incubate", "gel_separate",
                                                             "gel_purify", "cover", "stamp",
                                                             "dispense"],
                                               shortname="96-flat",
                                               col_count=12,
                                               dead_volume_ul=Unit(25, "microliter"),
                                               safe_min_volume_ul=Unit(65, "microliter"))

_CONTAINER_TYPES['screw-cap-1.8'] = ContainerType(name="2mL Microcentrifuge tube",
                                                  well_count=1,
                                                  well_depth_mm=None,
                                                  well_volume_ul=Unit(1800.0, "microliter"),
                                                  well_coating=None,
                                                  sterile=False,
                                                  cover_types=None,
                                                  seal_types=None,
                                                  capabilities=["pipette", "gel_separate",
                                                                "gel_purify", "incubate", "spin"],
                                                  shortname="micro-2.0",
                                                  is_tube=True,
                                                  col_count=1,
                                                  dead_volume_ul=Unit(15, "microliter"),
                                                  safe_min_volume_ul=Unit(40, "microliter")
                                                  )



def set_property(wellorcontainer, property_name, value):
    """
    Sets a property on all wells in a container
    """
    wells = convert_to_wellgroup(wellorcontainer)
    
    if not isinstance(value, str):
        value = str(value)
    
    for well in wells:
        assert isinstance(well, Well)
        well.properties[property_name] = value

def copy_cell_line_name(from_wellorcontainer, to_wellorcontainer):
    set_property(to_wellorcontainer,'cell_line_name',get_cell_line_name(from_wellorcontainer))

def get_cell_line_name(wellorcontainer):
    wells = convert_to_wellgroup(wellorcontainer)
    
    return wells[0].properties['cell_line_name']

def init_inventory_container(container,headers=None, org_name=None):
    
    initialize_config()
    
    headers = headers if headers else TSC_HEADERS
    org_name = org_name if org_name else ORG_NAME
    
    def _container_url(container_id):
            return 'https://secure.transcriptic.com/{}/samples/{}.json'.format(org_name, container_id)

    response = requests.get(_container_url(container.id), headers=headers, verify=False)
    response.raise_for_status()

    container_json = response.json()   
    
    container.cover = container_json['cover']
    
    for well in container.all_wells():
        init_inventory_well(well,container_json=container_json)
    
   
#@TODO: this needs to be mocked in tests since it hits the transcriptic api
def init_inventory_well(well, headers=None, org_name=None,container_json=None):
    """Initialize well (set volume etc) for Transcriptic"""
    
    initialize_config()
        
    headers = headers if headers else TSC_HEADERS
    org_name = org_name if org_name else ORG_NAME    
    
    def _container_url(container_id):
        return 'https://secure.transcriptic.com/{}/samples/{}.json'.format(org_name, container_id)

    #only initialize containers that have already been made
    if not well.container.id:
        well.volume = ul(0)
        return

    if container_json:
        container = container_json
    else:
        response = requests.get(_container_url(well.container.id), headers=headers)
        response.raise_for_status()
    
        container = response.json()

    well_data = list(filter(lambda w: w['well_idx'] == well.index,container['aliquots']))
    
    #correct the cover status on the container
    
    #they don't return info on empty wells
    if not well_data:
        well.volume = ul(0)
        return
    
    well_data = well_data[0]
    well.name = "{}".format(well_data['name']) if well_data['name'] is not None else container["label"]
    well.properties = well_data['properties']
    if well_data.get('resource'):
        well.properties['Resource'] = well_data['resource']['name']
    well.volume = Unit(well_data['volume_ul'], 'microliter')

    if 'ERROR' in well.properties:
        raise ValueError("Well {} has ERROR property: {}".format(well, well.properties["ERROR"]))
    #if well.volume < Unit(20, "microliter"):
    #    logging.warn("Low volume for well {} : {}".format(well.name, well.volume))

    return True


def put_well_data(container_id, well_index, data_obj, headers=None, org_name=None,container_json=None):
    """Update a well with new data"""
    
    initialize_config()
        
    headers = headers if headers else TSC_HEADERS
    org_name = org_name if org_name else ORG_NAME    
    
    def _well_url(container_id, well_index):
        return 'https://secure.transcriptic.com/{}/inventory/samples/{}/{}'.format(org_name, container_id, well_index)

    headers['content-type'] = 'application/json'
   
    response = requests.put(_well_url(container_id, well_index), headers=headers,
                            data=json.dumps(data_obj),
                            verify=False
                            )
    
    response.raise_for_status()


def set_well_name(well_or_wells, name):
    wells = convert_to_wellgroup(well_or_wells)
    for well in wells:
        well.name = name

def uniquify(s):
    """ Converts a string into a unique string by including the timestamp"""
    curr_time = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")
    return s+'_%s'%curr_time
    
    
def total_plate_available_volume(plate, first_well_index=0):

    if not first_well_index:
        wells = plate.all_wells()
    else:
        wells = plate.all_wells()[first_well_index:]
    
    return (sum([get_well_max_volume(well) for well in wells]) -\
           total_plate_volume(plate)).to('microliter')

def total_plate_volume(plate,aspiratable=False):
    """ Deprecated: use get_volume"""
    assert isinstance(plate, Container)
    return get_volume(plate,aspiratable)

def floor_volume(volume):
    """
    Return the math.floor of a volume in microliters
    """
    return ul(math.floor(volume.to('microliter').magnitude))

def get_volume(entity,aspiratable=False):
    """
    Returns the total volume in the well, wellgroup, container, or list containing any of the previous
    
    """
    wells = convert_to_wellgroup(entity)
    
    if aspiratable:
        return sum([max(well.volume - get_well_dead_volume(well),ul(0)) for well in wells]).to('microliter')
    else:
        return sum([well.volume for well in wells]).to('microliter')        

def assert_non_negative_well(well):
    if well.volume<ul(0):
        raise Exception('Well volume can\'t be negative for well %s'%well)

def get_well_dead_volume(wellorcontainer):
    
    if isinstance(wellorcontainer,Container):
        well = wellorcontainer.well(0)
    else:
        well = wellorcontainer
    
    assert_non_negative_well(well)
    return well.container.container_type.dead_volume_ul.to('microliter')

def get_well_safe_volume(wellorcontainer):
    if isinstance(wellorcontainer,Container):
        well = wellorcontainer.well(0)
    else:
        well = wellorcontainer    
    
    assert_non_negative_well(well)
    return well.container.container_type.safe_min_volume_ul.to('microliter')

def get_well_max_volume(wellorcontainer, mammalian_cell_mode=False):
    """
    
    Get the max volume of a set of wells.  If mammalian_cell_mode=False, we don't allow more than 100uL in 
    6-flat plates to prevent adding too much volume
    
    """
    
    if isinstance(wellorcontainer,Container):
        well = wellorcontainer.well(0)
    else:
        well = wellorcontainer    
    
    assert_non_negative_well(well)
    
    if well.container.container_type.shortname == '6-flat':
        return ul(100)
    else:
        return well.container.container_type.well_volume_ul.to('microliter')

def space_available(well, first_well_index=0):
    """
    Volume remaining in the well
    
    """
    if isinstance(well, Container):
        return (total_plate_available_volume(well, first_well_index)).to('microliter')
    
    return (get_well_max_volume(well) - well.volume).to('microliter')
    

def touchdown_pcr(fromC, toC, durations, stepsize=2, meltC=98, extC=72):
    """Touchdown PCR protocol generator
    
    Doesn't include the toC as a step.
    
    """
    assert 0 < stepsize < toC < fromC
    def td(temp, dur): return {"temperature":"{:2g}:celsius".format(temp), "duration":"{:d}:second".format(dur)}

    return [{"cycles": 1, "steps": [td(meltC, durations[0]), td(C, durations[1]), td(extC, durations[2])]}
            for C in numpy.arange(fromC, toC, -stepsize)]

def convert_ug_to_pmol(ug_dsDNA, num_nts):
    """Convert ug dsDNA to pmol"""
    return float(ug_dsDNA)/num_nts * (1e6 / 660.0)

def expid(val,expt_name=None):
    """Generate a unique ID per experiment"""
    global experiment_name
    if not expt_name:
        assert experiment_name, "Must set experiment name"
        expt_name = experiment_name
    return "{}_{}".format(expt_name, val)

def ul(microliters):
    """Unicode function name for creating microliter volumes"""
    if isinstance(microliters,str) and ':' in microliters:
        return Unit(microliters).to('microliter')    
    return Unit(microliters,"microliter")

def hours(hours):
    if isinstance(hours,str) and ':' in hours:
        return Unit(hours).to('hour')
    return Unit(hours,"hour")

def minutes(minutes):
    if isinstance(minutes,str) and ':' in minutes:
        return Unit(minutes).to('minute')
    return Unit(minutes,"minute")

def ug(micrograms):
    """Unicode function name for creating microgram masses"""
    return Unit(micrograms,"microgram")

def ng(nanograms):
    """Unicode function name for creating nanogram masses"""
    return Unit(nanograms,"nanogram")


def ml(milliliters):
    """Unicode function name for creating microliter volumes"""
    return ul(milliliters*1000)

def pmol(picomoles):
    """Unicode function name for creating picomoles"""
    return Unit(picomoles,"picomole")  

def uM(micromolar):
    return Unit(micromolar,"micromolar")

def mM(millimolar):
    return Unit(millimolar,'millimolar')

def ensure_list(potential_item_or_items):
    try:
        some_object_iterator = iter(potential_item_or_items)
    except TypeError:
        return [potential_item_or_items]
    return list(potential_item_or_items)

def set_name(wellsorcontainer,new_name):
    if isinstance(wellsorcontainer, Container):
        wellsorcontainer.name = new_name
        return
    
    wells = convert_to_wellgroup(wellsorcontainer)
    
    for well in wells:
        well.name = new_name
        
    return

def copy_well_names(source_wells_or_container, dest_wells_or_container, pre_fix='',
                    post_fix=''):
    """
    Copy the name from a source container or list of wells to another container or list of wells.
    If the wells don't have names, their human readable well name will be used
    """
    source_wells = convert_to_wellgroup(source_wells_or_container)
    dest_wells = convert_to_wellgroup(dest_wells_or_container)


    #distribute
    if len(source_wells)==1 and len(dest_wells)>1:
        source_wells = list(source_wells)*len(dest_wells)
    
    #consolidate    
    elif len(dest_wells)==1 and len(source_wells)>1:
        dest_wells = list(dest_wells)*len(source_wells)

    else:
        assert len(source_wells)==len(dest_wells), 'source and dest wells must be the same cardinality'
        
    for source_well, dest_well in zip(source_wells,dest_wells):
        
        source_well_name = source_well.name if source_well.name else source_well.humanize()
        
        dest_well.name = "%s%s%s"%(pre_fix, source_well_name, post_fix)
    



def convert_to_wellgroup(entity):
    if isinstance(entity,Container):
        wells = entity.all_wells()
    elif isinstance(entity, list):
        wells = WellGroup([])
        
        #speed this function up for a common case
        if all([isinstance(item,Well) for item in entity]):
            return WellGroup(entity)
        
        #slower mixed entity case
        for item in entity:
            wells += convert_to_wellgroup(item)
            
    elif isinstance(entity,WellGroup):
        #clone the entity to allow us to edit in in functions
        wells = WellGroup(list(entity))
    elif isinstance(entity,Well):
        wells = WellGroup([entity])
    else:
        raise Exception("unknown entity type %s"%entity)
    
    return wells

def assert_valid_volume(wells,exception_info='invalid volume'):
    """For wells that we have aspirated volume from, make sure that we haven't requested more volume than could be aspirated
    """
    wells = ensure_list(wells)
    
    assert all([well.volume >= get_well_dead_volume(well) for well in wells]), exception_info
    assert all([well.volume <= get_well_max_volume(well) for well in wells]), exception_info
    

def get_column_wells(container, column_index_or_indexes):
    
    assert isinstance(container, Container)
    
    if isinstance(column_index_or_indexes,list):
        result = []
        for column_index in column_index_or_indexes:
            result+=get_column_wells(container, column_index)
            
        return WellGroup(result)
    
    column_index = column_index_or_indexes
    
    num_cols = container.container_type.col_count
    num_rows = container.container_type.row_count()   
    
    if column_index >= num_cols:
        raise ValueError('column index %s is too high, only %s cols in this container'%(column_index,num_cols))
    
    start = num_rows*column_index
    
    return WellGroup(container.all_wells(columnwise=True)[start:start+num_rows])
    
def breakup_dispense_column_volumes(column_volumes):
    """

    Ensures that the column/volume pairs passed to dispense are less than 2.5mL (and multiples of 20uL)
    
    """
    
    new_column_volumes = []
    
    for col_volume_pair in column_volumes:
        volume = col_volume_pair['volume'].to('microliter')
        while volume>ml(2.5):
            
            volume_to_breakup_ul = round_up(volume.magnitude/2,20)
            new_column_volumes.append({'column':col_volume_pair['column'], 'volume':ul(volume_to_breakup_ul)})
            volume-=ul(volume_to_breakup_ul)
            
        new_column_volumes.append({'column':col_volume_pair['column'], 'volume':volume})
        
        
    return new_column_volumes
    


def round_volume(volume, ndigits):
    """
    Converts to microliters and performs rounding
    """
    return ul(round(volume.to('microliter').magnitude,ndigits))

def ceil_volume(volume,ndigits=0):
    """
    Converts to microliters and performs ceil
    """
    
    magnitude = volume.to('microliter').magnitude
    power_multiple = math.pow(10,ndigits)
    return ul(math.ceil(magnitude * int(power_multiple)) / power_multiple)
    
def convert_mass_to_volume(mass_to_convert,dna_well):
    if not dna_well.properties:
        init_inventory_well(dna_well)
    
    mass_to_convert_ng = mass_to_convert.to('nanogram')
    
    dna_concentration_ng_per_ul = Unit(dna_well.properties['Concentration (DNA)']).to('nanogram/microliter')
    dna_concentration_ul_per_ng = (1/dna_concentration_ng_per_ul).to('microliter/nanogram')
    #liquid handler has .01 ul precision
    return ceil_volume(mass_to_convert_ng * dna_concentration_ul_per_ng,2)


def convert_moles_to_volume(moles_to_convert,dna_well):
    
    ng_per_pmol_1kb = Unit(649,'nanogram/picomole')
    
    dna_length = int(dna_well.properties['dna_length'])
    
    moles_to_convert_pmol = moles_to_convert.to('picomole')
    
    mass_to_convert_ng = moles_to_convert_pmol * ng_per_pmol_1kb * dna_length / 1000.0
    
    return convert_mass_to_volume(mass_to_convert_ng, dna_well)
    
    


def convert_stamp_shape_to_wells(source_origin, dest_origin, shape=dict(rows=8,
                                                                   columns=12), one_source=False):
    # Support existing transfer syntax by converting a container to all
    # quadrants of that container
    if isinstance(source_origin, Container):
        source_plate = source_origin
        source_plate_type = source_plate.container_type
        if source_plate_type.well_count == 96:
            source_origin = source_plate.well(0)
        elif source_plate_type.well_count == 384:
            source_origin = source_plate.wells([0, 1, 24, 25])
        else:
            raise TypeError("Invalid source_origin type given. If "
                            "source_origin is a container, it must be a "
                            "container with 96 or 384 wells.")
    if isinstance(dest_origin, Container):
        dest_plate = dest_origin
        dest_plate_type = dest_plate.container_type
        if dest_plate_type.well_count == 96:
            dest_origin = dest_plate.well(0)
        elif dest_plate_type.well_count == 384:
            dest_origin = dest_plate.wells([0, 1, 24, 25])
        else:
            raise TypeError("Invalid dest_origin type given. If "
                            "dest_origin is a container, it must be a "
                            "container with 96 or 384 wells.")

    # Initialize input parameters
    source = WellGroup(source_origin)
    dest = WellGroup(dest_origin)
    opts = []  # list of transfers
    oshp = []  # list of shapes
    osta = []  # list of stamp_types
    len_source = len(source.wells)
    len_dest = len(dest.wells)

    # Auto-generate well-group if only 1 well specified for either source
    # or destination if one_source=False
    if not one_source:
        if len_dest > 1 and len_source == 1:
            source = WellGroup(source.wells * len_dest)
            len_source = len(source.wells)
        if len_dest == 1 and len_source > 1:
            dest = WellGroup(dest.wells * len_source)
            len_dest = len(dest.wells)
        if len_source != len_dest:
            raise RuntimeError("To transfer liquid from one origin or "
                               "multiple origins containing the same "
                               "source, set one_source to True. To "
                               "transfer from multiple origins to a "
                               "single destination well, specify only one "
                               "destination well. Otherwise, you must "
                               "specify the same number of source and "
                               "destination wells to do a one-to-one "
                               "transfer.")



    # Auto-generate list from single shape, check if list length matches
    if isinstance(shape, dict):
        if len_dest == 1 and not one_source:
            shape = [shape] * len_source
        else:
            shape = [shape] * len_dest
    elif isinstance(shape, list) and len(shape) == len_dest:
        shape = shape
    else:
        raise RuntimeError("Unless the same shape is being used for all "
                           "transfers, each destination well must have a "
                           "corresponding shape in the form of a list.")

    # Read through shape list and generate stamp_type, rows, and columns
    stamp_type = []
    rows = []
    columns = []

    for s in shape:
        # Check and load rows/columns from given shape
        if "rows" not in s or "columns" not in s:
            raise TypeError("Invalid input shape given. Rows and columns "
                            "of a rectangle has to be defined.")
        r = s["rows"]
        c = s["columns"]
        rows.append(r)
        columns.append(c)

        # Check on complete rows/columns (assumption: tip_layout=96)
        if c == 12 and r == 8:
            stamp_type.append("full")
        elif c == 12:
            stamp_type.append("row")
        elif r == 8:
            stamp_type.append("col")
        else:
            raise ValueError("Only complete rows or columns are allowed.")

    
    
    all_source_wells = []
    all_dest_wells = []
    for w, c, r, st in list(zip(source.wells, columns, rows, stamp_type)):
        columnWise = False
        if st == "col":
            columnWise = True
        if w.container.container_type.col_count == 24:
            if columnWise:
                source_wells = [w.container.wells_from(
                    w, c * r * 4, columnWise)[x] for x in range(c * r * 4) if (x % 2) == (x // 16) % 2 == 0]
            else:
                source_wells = [w.container.wells_from(
                    w, c * r * 4, columnWise)[x] for x in range(c * r * 4) if (x % 2) == (x // 24) % 2 == 0]
        else:
            source_wells = w.container.wells_from(
                w, c * r, columnWise)
            
        all_source_wells += source_wells
        
        
    for w, c, r, st in list(zip(dest.wells, columns, rows, stamp_type)):
        columnWise = False
        if st == "col":
            columnWise = True
        if w.container.container_type.col_count == 24:
            if columnWise:
                dest_wells = [w.container.wells_from(
                    w, c * r * 4, columnWise)[x] for x in range(c * r * 4) if (x % 2) == (x // 16) % 2 == 0]
            else:
                dest_wells = [w.container.wells_from(
                    w, c * r * 4, columnWise)[x] for x in range(c * r * 4) if (x % 2) == (x // 24) % 2 == 0]
        else:
            dest_wells = w.container.wells_from(
                w, c * r, columnWise)
    
        all_dest_wells += dest_wells    
        
    return all_source_wells, all_dest_wells

def calculate_dilution_volume(start_concentration, final_concentration, final_volume):

    start_volume = final_concentration * final_volume / start_concentration
    
    return start_volume.to('microliter') 
    
UNIT_RE = re.compile('^(\d+\.?\d{0,2})([\w\/]+)$')
def convert_string_to_unit(s):
    """Handles malformated strings like 10uM"""
    
    if ":" not in s:
        match  = UNIT_RE.match(s)
        if match:
            s = "%s:%s"%match.groups()
    
    return Unit(s)


def get_diluent_volume(starting_concentration, dilutant_volume, desired_concentration):
    
    if desired_concentration > starting_concentration:
        raise Exception('starting concentration must be higher than desired concentration in a dilution')
    
    dilution_multiple = (starting_concentration.to('uM') / desired_concentration).magnitude
    diluent_volume = round_volume(dilutant_volume / (dilution_multiple - 1),2) 
    return diluent_volume


class InvalidContainerStateException(Exception):
    pass
