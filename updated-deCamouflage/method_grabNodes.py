


def grabMSnodes2(inputfile, nodeIndexLs, grab=False):
	'''This file extracts nodes in nodeIndexLs from the solution given by MINISAT.'''	

	nodes2grab = []
	sat = False
	with open(inputfile, 'r') as infile:
		lines = infile.read().split('\n')
	if lines[0] == 'SAT': 
		sat = True
	#nodes2grab.append(sat) #nodes2grab[0] indicates whether the problem is sat.
	if sat == True:
		if grab == True:
			nodeVals = lines[1].split()
			#print "SAT returned values:", nodeVals 
			for node in nodeIndexLs:
				if '-' in nodeVals[node-1]:nodes2grab.append('0')
				else: nodes2grab.append('1') 	
			print "Node\t",
			for i in nodeIndexLs:
				print '\t',i,
			print "\nValue\t",
			for j in nodes2grab:
				print '\t'+j,
	nodes2grab.insert(0,sat)
	print '\n'
	#print nodes2grab
	return nodes2grab	



