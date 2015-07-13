# This file extracts the input vectors from the given solution.

import re

def grabGLPKnodes(infile, num2grab):
	'''This file extracts the input vectors from the solution given by GLPK.'''

	lines2grab = []
	nodes2grab = []
	with open(infile) as infile:
		lines = infile.read().split('\n')
		for i in range(len(lines)):
			lineBuf = lines[i]
			if ' Column ' in lineBuf and ' Activity ' in lineBuf:
				lines2grab.append(lineBuf)
				for j in range(num2grab+2):
					lines2grab.append(lines[i+j+1])
				break
	for line in lines2grab:
		print line
		if line != '':
			linefrag = line.split()
			nodes2grab.append(linefrag[2])
	print nodes2grab
	return nodes2grab

#################################################
#################################################
#################################################
#################################################


def grabMSnodes(infile, num2grab, grab=False):
	'''This file extracts the input vectors from the BEGINNING Of the solution given by MINISAT.'''	

	nodes2grab = []
	sat = False
	with open(infile) as infile:
		lines = infile.read().split('\n')
		#print lines
		if lines[0] == 'SAT': 
			sat = True
		nodes2grab.append(sat)
		if sat == True:
			if grab == True:
				nodeVals = lines[1].split()
				#print "SAT returned values:", nodeVals 
				if num2grab < len(nodeVals):
					for i in range(num2grab):
						if '-' in nodeVals[i]: nodes2grab.append('0')
						else: nodes2grab.append('1') 	
					print "Node\t",
					for i in range(1, len(nodes2grab)):
						print '\t',i,
					print "\nValue\t",
					for i in range(1, len(nodes2grab)):
						print '\t'+nodes2grab[i],
				else:
					###PROBLEM HERE! (WRITE_CNF writes cnf file even if it is unsat!!!)
					print "Too few node values. Recognized as UNSAT!" 
					nodes2grab[0] = 'False'
	print '\n'
	#print nodes2grab
	return nodes2grab	

#################################################
#################################################
#################################################
#################################################


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
				if '-' in nodeVals[node-1]: nodes2grab.append('0')
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



