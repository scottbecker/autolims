from __future__ import print_function
import os
import sys
from FlowCytometryTools import ThresholdGate, FCMeasurement, PolyGate

cell_type_gates = {
    'sample_cells':[
        ThresholdGate(1.573e+04, ('SSC-A'), region='above', name='gate1'),
        ThresholdGate(2.698e+05, ('SSC-A'), region='below', name='gate2'),
        ThresholdGate(2.130e+05, ('FSC-A'), region='above', name='gate3'),
        ThresholdGate(1.034e+06, ('FSC-A'), region='below', name='gate7')],
    'vero_cells':[


        #ThresholdGate(0, ('SSC-A'), region='above', name='gate1'),

        #ThresholdGate(5.703e+05, ('SSC-A'), region='below', name='gate3'),
        #ThresholdGate(0, ('FSC-A'), region='above', name='gate2'),
        #ThresholdGate(1.036e+06, ('FSC-A'), region='below', name='gate4')       

         ThresholdGate(3.893e+04, ('FSC-H'), region='above', name='gate1'),
         ThresholdGate(3.639e+05, ('FSC-H'), region='below', name='gate2'),
        ThresholdGate(4.031e+03, ('SSC-A'), region='above', name='gate3'),
        ThresholdGate(9.700e+05, ('SSC-A'), region='below', name='gate4')
        ],    
    'cfpac-1_cells':[
        
        ThresholdGate(3.468e+04, ('SSC-A'), region='above', name='gate5'),
        ThresholdGate(7.695e+05, ('SSC-A'), region='below', name='gate6'),
        ThresholdGate(5.991e+04, ('FSC-A'), region='above', name='gate7'),
        ThresholdGate(1.032e+06, ('FSC-A'), region='below', name='gate8')
  
    ]
    
}

#for testing
cell_type_gates['pc_cells'] = cell_type_gates['cfpac-1_cells']


def get_cell_count(flow_data_file_path, cell_type):
    
    
    sample = FCMeasurement(ID='Test Sample', datafile=flow_data_file_path)

    gated_sample = sample

    for gate in cell_type_gates[cell_type]:
        gated_sample = gated_sample.gate(gate)
        
        


    return gated_sample.counts


def view_data(flow_data_file_path):
    
    sample = FCMeasurement(ID='Test Sample', datafile=flow_data_file_path)
    sample.view_interactively()

if __name__=='__main__':
    
    
    if sys.argv[1] not in cell_type_gates:
        data_file_path = os.path.join(os.path.dirname(__file__), sys.argv[1])
        view_data(data_file_path)
    else:
        data_file_path = os.path.join(os.path.dirname(__file__), sys.argv[2])
        
        cells_per_500_ul = get_cell_count(data_file_path,sys.argv[1])
        
        cells_per_ul = cells_per_500_ul / 500
    
        print('There are %s cells in the sample. This is %s per ul'%(cells_per_500_ul,cells_per_ul))    