from odbAccess import *
from abaqusConstants import *

from odbMaterial import *
from odbSection import *

import sys


odbname = sys.argv[-1]
outputDataFile = odbname[:-4] + '_output.txt'

odb = openOdb(odbname)

instance = odb.rootAssembly.instances['CLOTH-1']

finalShape = odb.steps['Step-2'].frames[-1]
xyz = finalShape.fieldOutputs['COORD'].values

numNodesTotal = len( xyz )

f = open(outputDataFile, 'w')

for i in range( numNodesTotal ):
	for j in range(3):
		curNode = xyz[i].data
		f.write("{:e}".format(curNode[j]) + " ")  # use final
	f.write("\n")
f.close()

odb.close()