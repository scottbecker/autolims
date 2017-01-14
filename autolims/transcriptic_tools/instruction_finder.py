from __future__ import print_function
import json
import sys
contents = open(sys.argv[1],'rb').read().decode('utf8')
protocol = json.loads(contents)

print(json.dumps(protocol['instructions'][int(sys.argv[2])],indent=4))