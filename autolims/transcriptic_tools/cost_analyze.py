from __future__ import print_function
import json
import sys
import operator
from collections import defaultdict
from transcriptic_tools.custom_connection import CustomConnection as Connection

protocol_json = json.loads(open(sys.argv[1],'rb').read())

api = Connection.from_file(".transcriptic")
api.analyze_only = True


info = api.analyze_run(protocol_json,
            test_mode='--test' in sys.argv,
            bsl=1)


if '--verbose' in sys.argv:
    print(json.dumps(info, indent=4))
    sys.exit()



instructions = [item for item in info['quote']['breakdown']['children'] if item['name']=='Instructions'][0]['children']



total = 0.0

totals_by_operation = defaultdict(int)

for item in instructions:
    
    item['total'] = float(item['total'])
    total+=item['total']
    totals_by_operation[item['name'].split(' ')[-1]]+=item['total']
    





sorted_x = sorted(instructions, key=operator.itemgetter('total'),reverse=True)

print(json.dumps(sorted_x[:20],indent=4))

print(totals_by_operation)