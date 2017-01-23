from enum import Enum
from autoprotocol import Unit

class CustomEnum(Enum):
    @classmethod
    def from_string(cls, str):
        return getattr(cls, str.lower(), None)    
    
    @classmethod
    def get_names(cls):
        return cls._member_map_.keys()

class Reagent(CustomEnum):
    dmem_fbs_ps =  1
    mem = 2
    methanol = 3
    fbs = 4
    pennstrep = 5
    trypsin_edta = 6
    lipofectamine = 7
    optiMem = 8
    dmso = 9
    pbs = 10
    te = 11
    water = 12
    culture_medium = 13
    freeze_medium = 14
    crystal_violet = 15
    glycerol = 16
    lb_miller = 17
    amp = 18
    kan = 19
    cam = 20
    strep = 21
    spc = 22 
    glycerol = 23
    #no longer available
    #tb_amp = 24
    #tb_kan = 25
    #tb_spc = 26
    #tb_cam = 27
    lb_amp = 46
    lb_kan = 47
    iptg = 28
    t4_ligase_kit_ligase_buffer_10x = 30
    t4_ligase_kit_ligase = 31    
    nebuffer_2_1_10x = 32
    tss = 33
    q5_buffer_5x = 35
    q5_hf_polymerase = 36
    q5_high_gc_enhancer = 37
    dntp_10mM = 38
    copycontrol_induction_solution = 39
    cutsmart_buffer_10x = 40
    hindiii = 41
    sali = 42
    t4_polynucleotide_kinase = 43
    t4_polynucleotide_kinase_buffer_a_10x = 44
    atp_100mM = 45
    fastap = 48
    antarctic_phosphatase =  49
    antarctic_phosphatase_buffer_10x =  50
    nebuilder_master_mix = 51
    m9_minimal_media = 52
    pUC19_1ug_per_ul = 53 #1ug/ul
    pUC19_100pg_per_ul = 55
    pHSG298_500ng_per_ul = 54 #0.5ug/ul
    pHSG298_100pg_per_ul = 56
    pGPS2_100pg_per_ul = 59
    
    #antibiotic positive control plasmids (aliases)
    kan_resistant_plasmid = 56
    amp_resistant_plasmid = 55
    cam_resistant_plasmid = 59

    
    zymo_dh5a = 57
    soc_medium = 58
    
    peg_6000_24percent = 60
    
    t3_primer_100_micromolar = 61
    
    
    
    @property
    def is_dispensable(self):
        return self in DISPENSABLE_REAGENTS

DISPENSABLE_REAGENTS = {
    Reagent.water: True,
    Reagent.pbs: True,
    Reagent.te: True,
    Reagent.fbs: True,
    Reagent.mem: True,
    Reagent.methanol: True,
    Reagent.dmem_fbs_ps: True,
    Reagent.lb_miller: True,
    Reagent.lb_amp: True,
    Reagent.lb_kan: True,
    Reagent.m9_minimal_media: True,
    Reagent.soc_medium: True
    #no longer available            
    #Reagent.tb_amp: True,
    #Reagent.tb_kan: True,
    #Reagent.tb_cam: True,
    #Reagent.tb_spc: True
}


class Antibiotic(CustomEnum):
    amp = 1
    kan = 2
    cam = 3
    strep = 4
    spc = 5
    
    #special case to make dealing with LB only easier
    no_antibiotic = 6
    
    _goal_concentrations = {
       1: 100
    }
    
    @property
    def effective_concentration(self):
        return EFFECTIVE_ANTIBIOTIC_CONCeNTRATIONS[self]
    
    @property
    def reagent_concentration(self):
        return ANTIBIOTIC_REAGENT_CONCeNTRATIONS[self]    
    
    @property
    def broth(self):
        
        if self.name == 'no_antibiotic':
            return Reagent.lb_miller
        
        return Reagent.from_string('lb_%s'%self.name)
    
    @property
    def positive_control_plasmid(self):
        
        if self.name == 'no_antibiotic':
            return Reagent.amp_resistant_plasmid        
        
        return Reagent.from_string('%s_resistant_plasmid'%self.name)    
    
    @property
    def reagent(self):
        return Reagent.from_string(self.name)
        
        
#all units below use microliters to prevent precision errors when converting to microliter        
        
EFFECTIVE_ANTIBIOTIC_CONCeNTRATIONS = {
    #1 microgram/milliliter = 1 nanogram/microliter
    Antibiotic.amp: Unit(100,'nanogram/microliter'),
    Antibiotic.kan: Unit(50,'nanogram/microliter'),
    Antibiotic.cam: Unit(12.5,'nanogram/microliter'),
    Antibiotic.strep: Unit(100,'nanogram/microliter'),
    Antibiotic.spc: Unit(50,'nanogram/microliter'),
}

ANTIBIOTIC_REAGENT_CONCeNTRATIONS = {
    #1 milligram/milliliter = 1 microgram / microliter
    Antibiotic.amp: Unit(100,'microgram/microliter'),
    Antibiotic.kan: Unit(50,'microgram/microliter'),
    Antibiotic.cam: Unit(34,'microgram/microliter'),
    Antibiotic.strep: Unit(100,'microgram/microliter'),
    Antibiotic.spc: Unit(100,'microgram/microliter'),
}

class Temperature(CustomEnum):
    cold_4 = 1
    cold_20 = 2
    cold_80 = 3
    warm_37 = 4
    ambient = 5
    