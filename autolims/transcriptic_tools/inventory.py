from .enums import Reagent, Temperature



def get_transcriptic_inventory(include_lowercase=True):
    inventory = {
        Reagent.dmem_fbs_ps: 'rs197gzgq2fufr',
        Reagent.mem: 'rs196bbjnnayuk',
        Reagent.methanol: 'rs196bbr78dppk',
        Reagent.fbs: 'rs196baqxcecxs',
        Reagent.pennstrep: 'rs196bavhs85mh',
        Reagent.trypsin_edta: 'rs196bb2deuhsy',
        Reagent.lipofectamine: 'rs196bb7qetqmr',
        Reagent.optiMem: 'rs196bbe9yqma8',
        Reagent.dmso: 'rs186hr8m38ntw',
        Reagent.pbs: 'rs194na2u3hfam',
        Reagent.te: 'rs17pwyc754v9t',
        Reagent.water       : 'rs17gmh5wafm5p', # catalog; Autoclaved MilliQ H2O; ambient
        Reagent.zymo_dh5a        : 'rs16pbj944fnny', # catalog; Zymo DH5a; cold_80
        'gibson_mix'  : 'rs16pfatkggmk5', # catalog; Gibson Mix (2X); cold_20
        Reagent.nebuilder_master_mix: 'rs18pc86ykcep6', # catalog; NEBuilder MasterMix
        Reagent.lb_miller   : 'rs17bafcbmyrmh', # catalog; LB Broth Miller; cold_4
        Reagent.amp : 'rs17msfk8ujkca', # catalog; Ampicillin 100mg/ml; cold_20
        Reagent.spc: 'rs17pm6deqjep7',
        Reagent.kan: 'rs17msfpgpbqyv',
        Reagent.tss: 'rs19gme9ycpux6',
        Reagent.cam: 'rs17p6t8ty2ny4',
        Reagent.lb_amp: 'rs18s8x4qbsvjz',
        Reagent.lb_kan: 'rs18s8x88zz9ee',
        Reagent.fastap: 'rs16pc9925vae3',
        Reagent.antarctic_phosphatase: 'rs17sh65xxym4k',
        Reagent.antarctic_phosphatase_buffer_10x: 'rs17sh6bqyawz3',
        #doesn't exist anymore
        #Reagent.tb_amp: 'rs18xr22jq7vtz',
        Reagent.m9_minimal_media: 'rs18tmbm3am3ab',
        Reagent.soc_medium: 'rs17tpdy56hfar',

        Reagent.t4_ligase_kit_ligase_buffer_10x: 'rs17sh5rzz79ct',
        Reagent.t4_ligase_kit_ligase: 'rs16pc8krr6ag7',
        Reagent.nebuffer_2_1_10x: 'rs17sh6krrzjqu',
        Reagent.q5_buffer_5x:'rs16pcce8rmke3',
        Reagent.q5_hf_polymerase:'rs16pcce8rdytv',
        Reagent.q5_high_gc_enhancer:'rs16pcce8rva4a',
        Reagent.dntp_10mM:'rs186wj7fvknsr',
        Reagent.cutsmart_buffer_10x: 'rs17ta93g3y85t',
        Reagent.hindiii: 'rs18nw6kpnp44v',
        Reagent.sali: 'rs18y5qx47z4v2',
        Reagent.t4_polynucleotide_kinase:'rs16pc9rd5hsf6', #thermo
        Reagent.t4_polynucleotide_kinase_buffer_a_10x:'rs16pc9rd5sg5d', #thermo
        Reagent.atp_100mM: 'rs16pccshb6cb4',
        
        Reagent.pUC19_1ug_per_ul       : 'rs17tcqmncjfsh', # catalog; pUC19; cold_20    
        Reagent.pHSG298_500ng_per_ul     : 'rs18rx5pyh6fku',
        Reagent.pUC19_100pg_per_ul: 'rs18rx59spw2t8',
        Reagent.pHSG298_100pg_per_ul: 'rs18rx6a44qss7',
        
        Reagent.peg_6000_24percent: 'rs16pc9rd68sdt', #thermo
        
        
        
        Reagent.iptg          : 'rs18vwgfgxq597', # catalog: 100mM
        'm13_f'                       : 'rs17tcpqwqcaxe', # catalog; M13 Forward (-41); cold_20 (1ul = 100pmol)
        'm13_r'                       : 'rs17tcph6e2qzh', # catalog; M13 Reverse (-48); cold_20 (1ul = 100pmol)
        'sensifast_sybr_no-rox'       : 'rs17knkh7526ha', # catalog; SensiFAST SYBR for qPCR      
        Reagent.glycerol: 'rs17rrhqpsxyh2',
        # kits (must be used differently)
        'lb-broth-100ug-ml-amp_6-flat' : 'ki17sbb845ssx9', # catalog; ampicillin plates
        'noab-amp_6-flat' : 'ki17reefwqq3sq' # catalog; no antibiotic plates        
    }
    
        

    #convert reagent keys into string keys for backward compatibility
    reagent_keys = [key for key in inventory.keys() if isinstance(key,Reagent)]

    for key in reagent_keys:
        inventory[key.name] = inventory[key]
        if include_lowercase:
            inventory[key.name.lower()] = inventory[key]    
        
    return inventory



def get_our_inventory(is_test_mode):
    
    #import refill function (need to find a way to do this at the top of the file but these 
    #require CustomProtocol while CustomProtocol requires this file)
    from protocols.prepare_stock_culture_medium.protocol import refill_culture_medium
    from protocols.prepare_stock_freeze_medium.protocol import refill_freeze_medium
    
    #production
    inventory = {
        Reagent.culture_medium: {
            'cont_type':'96-deep',
            'refill_function':refill_culture_medium
            },
        Reagent.freeze_medium: {
            'id':'ct198d3zqvuz5j',
            'cont_type':'24-deep',
            'refill_function':refill_freeze_medium
            },
        Reagent.crystal_violet: {
            'id':'ct1994989gyqmm',
            'cont_type':'24-deep',
            'storage':'ambient',
            'requires_mixing':False
            },
        Reagent.strep: {
            'id':'ct19gd87wu9wkx',
            'cont_type':'96-deep',
        },
        Reagent.copycontrol_induction_solution:{
            'id':'ct19hc49an636q',
            'cont_type':'96-deep',
        },
        Reagent.pGPS2_100pg_per_ul:{
            'id':'not made yet',
            'cont_type':'96-pcr',   
            'storage':Temperature.cold_20.name,
        }
                
        
    }      
    
    #default storage=cold_4, requires_mixing=True, cont_type=micro-1.5
    for reagent_info in inventory.values():
        if not reagent_info.get('storage'):
            reagent_info['storage'] = Temperature.cold_4.name
        if not reagent_info.get('cont_type'):
            reagent_info['cont_type'] = 'micro-1.5'
        if reagent_info.get('requires_mixing') == None:
            reagent_info['requires_mixing'] = True   
        
    
    if is_test_mode:
        #REAL INVENTORY
        inventory[Reagent.freeze_medium]['id'] = 'ct196xu2eqr5hn'
        inventory[Reagent.strep]['id'] = 'ct19gqqx26wk7r'
        inventory[Reagent.copycontrol_induction_solution]['id'] = 'ct19hctrbwdbwd'
        inventory[Reagent.pGPS2_100pg_per_ul]['id'] = 'ct19mzjcf99pfu'

    #convert reagent keys into string keys for backward compatibility
    reagent_keys = [key for key in inventory.keys() if isinstance(key,Reagent)]

    for key in reagent_keys:
        inventory[key.name] = inventory[key]
        inventory[key.name.lower()] = inventory[key]         
    
    return inventory
    
