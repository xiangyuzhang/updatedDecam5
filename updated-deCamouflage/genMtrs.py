#!/usr/bin/python

import re
import os
import time



'''
The difference between genFirstMtr and genScndMtr is that\
in genScndMtr, PI input verctors together with programming\
bits are assigned, while genFirstMtr only requires assignmets\
for programming bits.
The genThdMtr only has PI input vectors assigned, the p-bits\
are unknown. The goal is to find p-bit pair assignments that\
current PI vectors cannot distinguish.
'''

def is_sequence(arg):
	'''This function judges whether arg is a list or str. List has no .strip() attribute.\
Str has no '__iter__' attribute.'''
	return (not hasattr(arg, "strip") and
		hasattr(arg, "__getitem__") or
		hasattr(arg, "__iter__"))


#################################################
#################################################
#################################################
#################################################


def genFirstMtr(infilePath, p_bits):
	'''Extracts model from camouflaged infile and generates miter with known p-bits.'''	
	
	infile = open(infilePath)
	inputs = [] # stores 2 sets of inputs: PIs and p-bits
	for line in infile:
		if '.model' in line:
			model = line.split()[1:]
		if '.inputs' in line:
			inputs.append(line.split()[1:])
		if '.outputs' in line:
			outputs = line.split()[1:]
		if '.end' in line: #make sure only the first block is extracted
			break
	infile.close()
	origPIs = inputs[0]
	origPbits = inputs[1]
	poNum = len(outputs)

	miterModel = '.model '+model[0]+'_miter'
	miterInputs = '\n.inputs '
	mtrIn = [] #stores the inputs to miter
	inPairs = [] #strores the assignment relationship
	for inp in origPIs: #the set of primary input vectors
		mtrIn.append('mtr_'+inp)
		inPairs.append([inp, 'mtr_'+inp])
	for item in mtrIn:
		miterInputs += item+' '
	miterOut = '\n.outputs miter0 '
	
	mtrOuts = []  #[ [mtr0_m0, ...], [mtr1_m0, ...] ]
	for i in range(2):
		out2xor = []
		for j in range(poNum):
			tmpOut = 'mtr_'+str(i)+'_'+outputs[j]
			#miterOut += tmpOut+' '
			out2xor.append(tmpOut)
		mtrOuts.append(out2xor)

	miterOut += '\n.names ss0\n.names ss1\n1\n'
	timeGend = time.asctime( time.localtime(time.time()) )
	mainModel = '# Geneareted on '+str(timeGend)+'\n'+miterModel+miterInputs+miterOut

	'''
	2. Add subckt part into the miter model  	
	.subckt Multi3a a1=mtr_a1 a0=mtr_a0 a2=mtr_a2 b0=mtr_b0 b1=mtr_b1 b2=mtr_b2 s0=0 s1=1 m0=mtr0m0 m1=mtr0m1 m2=mtr0m2 m3=mtr0m3 m4=mtr0m4 m5=mtr0m5 
	.subckt Multi3a a1=mtr_a1 a0=mtr_a0 a2=mtr_a2 b0=mtr_b0 b1=mtr_b1 b2=mtr_b2 s0=1 s1=0 m0=mtr1m0 m1=mtr1m1 m2=mtr1m2 m3=mtr1m3 m4=mtr1m4 m5=mtr1m5 
	'''
	valDict = {'1':'ss1', '0':'ss0'}
	subckts = [] #stores subcktLines
	subcktLine = '.subckt '+model[0]+' '
	#2.1. PI inputs in subckt
	for pair in inPairs:
		subcktLine += pair[0]+'='+pair[1]+' '
	
	#2.2. p-bits inputs in subckt:
	for ssi in p_bits: #ssi may be string '0 1 0 0' or list ['0', '1', '0', '0']
		subAssign = []
		if not is_sequence(ssi): 
			subp_bits = ssi.split()
		else: 
			subp_bits = ssi[:]
		if len(subp_bits) != len(origPbits): # check error beforehand
			errorMsg = "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\nThe programming bits are not given correctly. You shall assign "+str(len(origPbits))+" programming bits for each set in total.\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
			print errorMsg
			return errorMsg
		for i in range(len(subp_bits)):
			subAssign.append(origPbits[i]+'='+valDict[subp_bits[i]]) #assign values to p-bits
		subckts.append(subcktLine+(' ').join(subAssign))
	#2.3. PO outputs in subckt
	mtrOutAssign = [] #[ 'm0=mtr0_m0, ...', 'm0=mtr1_m0, ...' ]
	for i in range(len(subckts)):
		subMtrOut = ' '
		for j in range(poNum):
			subMtrOut += outputs[j]+'='+mtrOuts[i][j]+' '			
		mtrOutAssign.append(subMtrOut)
		subckts[i] = subckts[i]+mtrOutAssign[i]
		
		
	for sc in subckts:
		mainModel += sc+'\n'

	'''
	3. Add the miter circuit part
	'''
	xorLines = ''
	xorOuts = '' #used in next big OR gate
	#3.1. XOR PO outputs
	for i in range(len(mtrOuts[0])):
		xorOuts += 'miter0'+str(i)+' '
		xorLines += '.names '+mtrOuts[0][i]+' '+mtrOuts[1][i]+' miter0'+str(i)+'\n'
		xorLines += '10 1\n01 1\n' 	
	#3.2. OR xor outputs
	orLines = '.names '+xorOuts+'miter0\n'
	#for i in range(len(mtrOuts[0])):
		#orLines += i*'-'+'1'+(len(mtrOuts[0])-i-1)*'-'+' 1\n'
	orLines += '0'*len(mtrOuts[0])+' 0\n'
	mainModel += xorLines
	mainModel += orLines
	mainModel += '.end\n\n'

	intxt = open(infilePath).read()
	mainModel += intxt
	tail = xorLines + orLines +'.end\n\n'+intxt #tail returned for later use
	#outfileName = infilePath.split('/')[-1]
	outfileName = re.search(r'(.*)(?<=\.)', infilePath).group().strip('.')
	outfileName += '-miter.blif'
	outfile = open(outfileName, 'w')
	outfile.write(mainModel)
	outfile.close()
	#print 'A miter to differentiate 2 sets of programming bits is constructed and stored in "',
	firstMtrPath = os.path.abspath(outfileName)
	#print firstMtrPath,'"'
	return (firstMtrPath, len(origPIs), len(origPbits))


#################################################
#################################################
#################################################
#################################################


def genScndMtr(infilePath, tail, inpVecList, p_bits):
	'''Generates the second miter that intends to see if PI verctor can detect the\
difference of 2 input pbit sets S1 and S2. Both PI vector and programming bits are\
known.'''

	infile = open(infilePath)
	inputs = [] # stores 2 sets of inputs: PIs and p-bits
	for line in infile:
		if '.model' in line:
			model = line.split()[1:]
		if '.inputs' in line:
			inputs.append(line.split()[1:])
		if '.outputs' in line:
			outputs = line.split()[1:]
		if '.end' in line: #make sure only the first block is extracted
			break
	infile.close()
	origPIs = inputs[0]
	origPbits = inputs[1]

	miterModel = '.model '+model[0]+'_miter'
	miterInputs = '\n.inputs dummyIn'
	mtrIn = [] #stores the inputs to miter
	inPairs = [] #strores the assignment relationship
	for inp in origPIs: #the set of PI vectors
		mtrIn.append('mtr_'+inp)
		inPairs.append([inp, 'mtr_'+inp])
	PIassign = ''
	for i in range(len(mtrIn)):
		item = mtrIn[i]
		#miterInputs += item+' '
		if inpVecList[i] == '0':
			PIassign += '.names '+item+'\n'
		elif inpVecList[i] == '1':
			PIassign += '.names '+item+'\n1\n'
		else: 
			print "Unknown value assignment for", item, 	
			return None
	#print '\n\npisaasign\n', PIassign		
	miterOut = '\n.outputs miter0\n.names ss0\n.names ss1\n1\n'+PIassign
	timeGend = time.asctime( time.localtime(time.time()) )
	mainModel = '# Geneareted on '+str(timeGend)+'\n'+miterModel+miterInputs+miterOut

	valDict = {'1':'ss1', '0':'ss0'}
	subckts = [] #stores subcktLines
	subcktLine = '.subckt '+model[0]+' '
	#2.1. PI inputs in subckt
	for pair in inPairs:
		subcktLine += pair[0]+'='+pair[1]+' '

	#2.2. p-bits inputs in subckt:
	for ssi in p_bits:
		subAssign = []
		if not is_sequence(ssi): subp_bits = ssi.split()
		else: subp_bits = ssi[:]
		if len(subp_bits) != len(origPbits): # check error beforehand
			errorMsg = "The programming bits are not given correctly. You shall assign "+str(len(origPbits))+" programming bits for each set in total."
			print errorMsg
			return errorMsg
		for i in range(len(subp_bits)):
			subAssign.append(origPbits[i]+'='+valDict[subp_bits[i]]) #assign values to p-bits
		subckts.append(subcktLine+(' ').join(subAssign))

	mtrOutAssign = [] #[ 'm0=mtr0_m0, ...', 'm0=mtr1_m0, ...' ]
	for i in range(len(subckts)):
		out2xor = []
		subMtrOut = ' '
		for out in outputs:
			subMtrOut += out+'=mtr'+str(i)+out+' '
			out2xor.append('mtr'+str(i)+out)
		mtrOutAssign.append(subMtrOut)
		subckts[i] = subckts[i]+mtrOutAssign[i]

	for sc in subckts:
		mainModel += sc+'\n'

	mainModel += tail

	outfileName = infilePath.split('/')[-1]
	outfileName = re.search(r'(.*)(?<=\.)', outfileName).group().strip('.')
	outfileName += '-miter2.blif'
	outfile = open(outfileName, 'w')
	outfile.write(mainModel)
	outfile.close()
	#print 'A miter to differentiate 2 sets of programming bits is constructed and stored in "',
	firstMtrPath = os.path.abspath(outfileName)
	#print firstMtrPath,'"'
	return firstMtrPath


#################################################
#################################################
#################################################
#################################################


def genThdMtr(infilePath, I, outputfilePath):
	'''
	This function creates 2*len(I) copies of the original camouflaged gates, then make\
a miter of all the outputs to create a SAT problem. PI vectors are known.
             				  S0             
                               |----------------->|
                               |                       |
				|-----------|---------|           | 
				|    	-----------     |           |
			    |I0->	|	lev1	|-----> |       |
				|   	|			|-----> |       |
				|	    -----------	  |   |       |
				|  Lev2     |           |   |      |
				|   	-----------     |   |       |
			    |I1->	|	lev1	|-----> |       |
				|   	|			|-----> |       |
				|   	-----------	  |   |       |			 		
                |---------------------|   |------------------------->MITER(XOR then NOR)
--Lev3--------------------------------|
     						  S1             |
						      |               |
						-----------         |
			     I0->	|	lev1	|-----> |
						|			|-----> |
						-----------	      |
						      |               |
						-----------         |
			     I1->	|	lev1	|-----> |
						|			|-----> |
						-----------		
	'''

	infile1 = open(infilePath) # infile is lev1
	lev1 = infile1.read()
	infile1.close()	
	infile = lev1.splitlines()
	lev1inputs = [] # stores 2 sets of inputs: PIs and p-bits
	for line in infile:
		if '.model' in line:
			lev1model = line.split()[1:]
		if '.inputs' in line:
			lev1inputs.append(line.split()[1:])
		if '.outputs' in line:
			lev1outputs = line.split()[1:]
		if '.end' in line: #make sure only the first block is extracted
			break
	lev1pinputs = lev1inputs[0]
	lev1pbits = lev1inputs[1]

	##################################################
	#LEVEL 2 MODEL: MULTIPLE LEV1 CKTS W/ KNOWN PIS AND UNKNOWN P-BITS#
	##################################################
	#1. level2 model name, inputs, outputs
	lev2name = lev1model[0]+'_lev2'
	lev2modelName = '.model '+lev2name
	lev2modelInputs = '\n.inputs '
	lev2pbits = []
	#1.1 rename level2 control bits (inputs for level2 model):
	for inp in lev1pbits:
		lev2pbits.append('lev2_'+inp)
	lev2modelInputs += (' ').join(lev2pbits)
	#1.2 rename level2 outputs
	lev2modelOuts = []
	for i in range(len(I)):
		subModelOut = []
		subOutPrefix = 'lev2_'+str(i)
		for j in range(len(lev1outputs)):
			subModelOut.append(subOutPrefix+str(j))
			#meaning of 'lev2_ij': the j-th output bit of i-th lev1 model in lev2 model
		lev2modelOuts.append( subModelOut )
	lev2modelOutputs = '\n.outputs '
	for lst in lev2modelOuts:
		lev2modelOutputs += (' ').join(lst)+ ' '
	#print 'lev2modelOutputs', lev2modelOutputs
	#2. constants
	contants = '\n.names cons0\n.names cons1\n1'

	#3. subckts
	valDict = {'1':'cons1', '0':'cons0'}
	lev2subcktList = []
	for i in range(len(I)):
		subckt = '\n.subckt '+lev1model[0]
		#3.1 assign the known PI verctor to lev1
		for j in range(len(lev1pinputs)):
			PIval = I[i][j]
			if PIval == '1':
				subckt += ' '+lev1pinputs[j]+'='+valDict['1']
			elif PIval == '0':
				subckt += ' '+lev1pinputs[j]+'='+valDict['0']
			else:
				print "Unknown value assignment for", PInputs[j]
				return None
		#3.2 assign the lev2 p-bits to lev1:
		for m in range(len(lev2pbits)):
			subckt += ' '+lev1pbits[m]+'='+lev2pbits[m]
		#3.3 assign lev2 outs to lev1:
		for n in range(len(lev2modelOuts[i])):
			subckt += ' '+lev1outputs[n]+'='+lev2modelOuts[i][n]		
		lev2subcktList.append(subckt)
	lev2subckts =('').join(lev2subcktList)
	
	#4. Complete level 2 model:
	level2model = lev2modelName+lev2modelInputs+lev2modelOutputs+contants
	level2model += lev2subckts+'\n.end\n'
									
	##################################################
	#LEVEL 3 MODEL: A MITER OF 2 LEVEL 2 MODELS W/ DIF P-BITS ASSIGNMENTS#
	##################################################
	#1. pre-generate all needed programming bits of the top level:
	topPbits = [] #stores 2 sets of p-bits assignments for the sub-lev2-ckts
	for i in range(2):
		subTopIn = []
		for j in range(len(lev1pbits)):
			tmpTopIn = 'top_s'+str(i)+'_'+str(j)
			subTopIn.append(tmpTopIn)
		topPbits.append(subTopIn)

	#2. model name, inputs and output:
	topModName = '.model TOP_MITER'
	topModIn ='\n.inputs '
	for subTopIn in topPbits:
		topModIn += (' ').join(subTopIn)+' '
		
	topModOut = '\n.outputs topMtrOut'	

	#3. top model subckts:
	topscList = []
	#list of list of list: [ [ [...], [...] ], [ [...], [...] ] ]
	#outer: outs of inter top signals; middle: outs of lev2 outs; inner: outs of lev1 outs
	topInterOut = [] 
	for m in range(2):		
		tmpInterOut1 = [] # stores all outputs of single lev2-sub-model
		topsc = '\n.subckt '+lev2name+' '
		#3.1. assign inputs to sub-lev2-model
		for n in range(len(lev1pbits)):
			topsc += lev2pbits[n]+'='+topPbits[m][n]+' '	
		#3.2. assign outputs to sub-lev2-modelOuts
		for o in range(len(lev2modelOuts)): # o determined on # of known PI vectors
			tmpInterOut2 = [] #stores outputs of single lev1-sub-sub-model
			tmpOutLst = lev2modelOuts[o]
			for p in range(len(tmpOutLst)): # p determined on # of output bits of lev1
				tmpLev2out=lev2modelOuts[o][p]
				tmpTopOut = 'top'+str(m)+'_'+re.search(r'(?<=lev2_)(.*)$', tmpLev2out).group()
				tmpInterOut2.append(tmpTopOut)
				topsc += tmpLev2out+'='+tmpTopOut+' '
			tmpInterOut1.append(tmpInterOut2)
		topInterOut.append(tmpInterOut1)
		topscList.append(topsc)
	topscs = ''
	for sc in topscList:
		topscs += sc

	#4. Miter module:
	#4.1 Build a miter for programming bit pair to make sure they are different
	pbitXORlines = ''
	pbitNORlines = '\n.names '
	pbitNum = len(topPbits[0])
	for i in range(pbitNum):
		pbitXORlines += '\n.names '+topPbits[0][i]+' '+topPbits[1][i]+' '
		pNorIn = 'pxor'+str(i)
		pbitXORlines += pNorIn+'\n10 1' + '\n01 1'
		pbitNORlines += pNorIn + ' ' 
	pbitNORlines += 'p_mtrOut\n'+'0'*pbitNum+' 1'
	#4.2 Rule out the illegal p-bit assignments (11 currently):
	ruleLines = ''
	and2outerNor = '' #part of inputs to the final NOR gate
	for i in range(len(topPbits)):
		SI = topPbits[i]
		singlePBITset = len(SI)
		andCnt = 1
		for n in xrange(0, singlePBITset, 2): #notice, we choose stepsize=2 b/c a MUX has 2 p-bits
			tmpPlist = SI[n:n+2]
			tmpAND = 'topAND'+str(i)+str(andCnt)
			and2outerNor += tmpAND+' '
			ruleLines += '\n.names '+tmpPlist[0]+' '+tmpPlist[1]+' '+tmpAND
			ruleLines += '\n11 1'
			andCnt += 1
	#4.3 Build a miter of outputs from lev1s and from p-bit miter and the AND gates:	
	topXorLines = ''
	topNorLines = '\n.names '
	tmpInterSig1 = topInterOut[0]
	tmpInterSig2 = topInterOut[1]
	lev1Num = len(tmpInterSig1)
	lev1outNum = len(lev1outputs)
	for i in range(lev1Num):
		for j in range(lev1outNum):
			topXorLines += '\n.names '+topInterOut[0][i][j]+' '+topInterOut[1][i][j]+' '
			tmpNorIn = 'miter'+str(i)+str(j)		
			topXorLines += tmpNorIn + '\n10 1' + '\n01 1'
			topNorLines += tmpNorIn + ' ' 
	topNorLines += and2outerNor+'p_mtrOut topMtrOut'
	topNorLines += '\n'+'0'*(lev1Num*lev1outNum+1+len(and2outerNor.split()))+' 1\n.end\n'
	
	#6. complete top level
	topModel = topModName+topModIn+topModOut+topscs+pbitXORlines+pbitNORlines+ruleLines+topXorLines+topNorLines
		
	#######################################
	# Combine all levels of models together
	#######################################
	outxt = topModel +'\n'+ level2model +'\n'+ lev1

	with open(outputfilePath, 'w') as outfile:
		outfile.write(outxt)
		#print "\nTop miter is generated and stored in '", outputfilePath, "'"
	return None
	

#################################################
#################################################
#################################################
#################################################


def genPO4Orac(OracBlif, PIvec, assignOracBlif):
	'''generates a oralce blif file w/ known PIs'''
	
	with open(OracBlif, 'r') as infile:
		subParts = infile.read().split('.names ', 1)
	subPart1 = subParts[0].split('\n')
	inputs = []
	for line in subPart1:
		if '.inputs' in line:			
			inputs.append(line.split()[1:])
			break
	PInum = len(inputs)
	# assign numeric values in PIvec to inputs in Oracle file:
	if PInum != len(PIvec):
		print 'Unmatched primary input values detected.'
		return None
	else:
		assignPIlines = ''
		for i in range(PInum):
			if PIvec[i] == '0': assignPIlines += '.names '+inputs[i]+'\n'
			elif PIvec[i] == '1': assignPIlines += '.names '+inputs[i]+'\n1\n'
	# write out:
	outxt = subPart[0]+assignPIlines+'.names '+subPart[1]
	with open(assignOracBlif, 'w') as outfile:
		outfile.write(outxt)
	return None


#################################################
#################################################
#################################################
#################################################


def genCompCkt(infilePath, lev2subCktNum, compCktPath):
	'''generate a circuit that integrate sevaral circuits together with a miter. The goal
is to find both 2 different programming bit assignments and a PI vector that can
distinguish them.
                  ---------------------S1-------------------------------
                  |                                                               |
   PI1 ----> lev1 -----> PO11                                     -->lev1->
                  |                                                         |          |
   PI2 ----> lev1 -----> PO12                                     |          |
                  |                                                         |          |
   PI3 ----> lev1 -----> PO13                                     |          |
                                                                            |          |
                                              PI_disting ------------>|       miter--->
                                                                             |         |
   PI1 ----> lev1 -----> PO21                                      |         |
                  |                                                          |         |
   PI2 ----> lev1 -----> PO22                                      |         |
                  |                                                          |         |
   PI3 ----> lev1 -----> PO23                                      ->lev1->
                  |                                                               |
                  ---------------------S2-------------------------------
NOTE: S1 != S2; S1 and S2 must be legal inputs (no 11 case)
PIs, S1, S2 and PI_disting are all inputs,  POs and miter out are all outputs. 
After the circuit is cnoverted to Tseitin form, PIs and POs will be assigned values.
The miter shall evaluate to True.'''

	infile1 = open(infilePath) # infile is lev1
	lev1 = infile1.read()
	infile1.close()	
	infile = lev1.splitlines()
	lev1inputs = [] # stores 2 sets of inputs: PIs and p-bits
	for line in infile:
		if '.model' in line:
			lev1model = line.split()[1:]
		if '.inputs' in line:
			lev1inputs.append(line.split()[1:])
		if '.outputs' in line:
			lev1outputs = line.split()[1:]
		if '.end' in line: #make sure only the first block is extracted
			break
	lev1pinputs = lev1inputs[0]
	lev1pbits = lev1inputs[1]

	##################################################
	#LEVEL 2 MODEL: MULTIPLE LEV1 CKTS                                                      #
	##################################################
	#1. level2 model name, inputs, outputs
	
	#1.1 rename inputs for level2 model:
	lev2name = lev1model[0]+'_lev2'
	lev2modelName = '.model '+lev2name
	lev2modelInputs = '\n.inputs '
	lev2modelpis = []
	lev2pbits = []
	#1.1.1 rename level2 PI vec bits (inputs for level2 model):
	#for piin in :
	for i in range(lev2subCktNum):
		subModelpi = []
		subPiPrefix = 'lev2_'+str(i)+'_'
		for j in range(len(lev1pinputs)):
			subModelpi.append(subPiPrefix+lev1pinputs[j])
		lev2modelpis.append( subModelpi )
	for pils in lev2modelpis:
		lev2modelInputs += (' ').join(pils)+' '
	#1.1.2 rename level2 programming bits (inputs for level2 model):
	lev2modelInputs += '\n.inputs '
	for pb in lev1pbits:
		lev2pbits.append('lev2_'+pb)
	lev2modelInputs += (' ').join(lev2pbits)

	#1.2 rename level2 outputs
	lev2modPOls = []
	for i in range(lev2subCktNum):
		subModelOut = []
		subOutPrefix = 'lev2_'+str(i)+'_'
		for j in range(len(lev1outputs)):
			subModelOut.append(subOutPrefix+lev1outputs[j])
			#meaning of 'lev2po_ij': the j-th output bit of i-th lev1 model in lev2 model
		lev2modPOls.append( subModelOut )
	lev2modelOutputs = '\n.outputs '
	for lst in lev2modPOls:
		lev2modelOutputs += (' ').join(lst)+ ' '
	#print 'lev2modelOutputs', lev2modelOutputs
	#2. constants
	#contants = '\n.names cons0\n.names cons1\n1'

	#3. subckts
	#valDict = {'1':'cons1', '0':'cons0'}
	lev2subcktList = []
	for i in range(lev2subCktNum):
		subckt = '\n.subckt '+lev1model[0]
		#3.1 assign the lev2 PI verctor to lev1
		for j in range(len(lev1pinputs)):	
			subckt += ' '+lev1pinputs[j]+'='+lev2modelpis[i][j]
		#3.2 assign the lev2 p-bits to lev1:
		for m in range(len(lev2pbits)):
			subckt += ' '+lev1pbits[m]+'='+lev2pbits[m]
		#3.3 assign lev2 outs to lev1:
		for n in range(len(lev1outputs)):
			subckt += ' '+lev1outputs[n]+'='+lev2modPOls[i][n]		
		lev2subcktList.append(subckt)
	lev2subckts =('').join(lev2subcktList)
	
	#4. Complete level 2 model:
	level2model = lev2modelName+lev2modelInputs+lev2modelOutputs
	level2model += lev2subckts+'\n.end\n'
									
	##################################################
	#LEVEL 3 MODEL: A MITER OF 2 LEVEL 2 MODELS W/ DIF P-BITS ASSIGNMENTS#
	##################################################

	topModName = '.model TOP_CKT'

	#1. pre-generate all needed inputs  of the top level:
	#1.1 generate distinguishing PI vector:
	distingPI = []
	for i in range(len(lev1pinputs)):
		distingPI.append('unkn_'+lev1pinputs[i])
	#1.2 generate 2 sets of programming bits:
	topPbits = [] #stores 2 sets of p-bits assignments for the sub-lev2-ckts
	for i in range(2):
		subTopIn = []
		for j in range(len(lev1pbits)):
			tmpTopIn = 'top_s'+str(i)+'_'+str(j)
			subTopIn.append(tmpTopIn)
		topPbits.append(subTopIn)
	#1.3 generate lev2subCktNum sets of PI vectors:
	topPIs = []
	for i in range(lev2subCktNum):
		subTopPIs = []
		for j in range(len(lev1pinputs)):	
			subTopPIs.append('top_'+str(i)+'_'+lev1pinputs[j]) #j-th input of i-th lev1model in lev2
		topPIs.append(subTopPIs)
	#1.4 assemble them together: .inputs PIunkn, S1, S2, ..., PI1, PI2, ...
	topModIn ='\n.inputs '
	topModIn += (' ').join(distingPI)+' '
	for subls in topPbits:
		topModIn += (' ').join(subls)+' '
	for subls in topPIs:
		topModIn += (' ').join(subls)+' '


	#2. generate the outputs for the top module:
	#notice the number of PO vectors is twice of that of PI vectors
	topModOut = '\n.outputs mtrOut '	
	topPos = []
	for i in range(2): # 2 sets of PO vectors
		subLev2Pos = []
		for j in range(lev2subCktNum):
			subsubLev1pos = []
			for k in range(len(lev1outputs)):
				subsubLev1pos.append('top_'+str(i)+'_'+str(j)+'_'+lev1outputs[k])
			subLev2Pos.append(subsubLev1pos)
		topPos.append(subLev2Pos)
	for subls in topPos:
		for subsubls in subls:
			topModOut += (' ').join(subsubls)+' '

	#3. top model subckts:
	topscList = []
	#list of list of list: [ [ [...], [...] ], [ [...], [...] ] ]
	#outer: outs of top model; middle: outs of lev2 outs; inner: outs of lev1 outs
	topInterOut = [] 
	for m in range(2):		
		tmpInterOut1 = [] # stores all outputs of single lev2-sub-model
		topsc = '\n.subckt '+lev2name+' '
		#3.1. assign control bit inputs to sub-lev2-model
		for n in range(len(lev1pbits)):
			topsc += lev2pbits[n]+'='+topPbits[m][n]+' '	
		#3.2 assign PI inputs to sub-lev2-model:
		for i in range(lev2subCktNum):
			for x in range(len(lev1pinputs)):
				topsc += lev2modelpis[i][x]+'='+topPIs[i][x]+' '	
		#3.3. assign outputs to sub-lev2-modelOuts
		for o in range(lev2subCktNum): # o determined on # of known PI vectors
			for p in range(len(lev1outputs)): # p determined on # of output bits of lev1
				topsc += lev2modPOls[o][p]+'='+topPos[m][o][p]+' '
		topscList.append(topsc)
	topscs = ''
	for sc in topscList:
		topscs += sc
	topscs += '\n'

	#4. Miter module:
	#4.1 Build a miter for programming bit pair to make sure they are different
	"""
	pbitXORlines = ''
	pbitORlines = '\n.names '
	pbitNum = len(topPbits[0])
	for i in range(pbitNum):
		pbitXORlines += '\n.names '+topPbits[0][i]+' '+topPbits[1][i]+' '
		pORin = 'pxor'+str(i)
		pbitXORlines += pORin+'\n10 1' + '\n01 1'
		pbitORlines += pORin + ' ' 
	pbitORlines += 'pb_mtrOut\n' #the output of the miter to distinguish Si w/ Sj
	for i in range(len(lev1pbits)):
		pbitORlines += i*'-'+'1'+(len(lev1pbits)-i-1)*'-'+' 1\n'
	subMtrDistPbits = pbitXORlines+pbitORlines
	"""
	"""
	#4.2 Rule out the illegal p-bit assignments (11 currently):
	nandRuleLines = ''
	nand2outerAND = [] #part of inputs to the final AND gate
	for i in range(len(topPbits)):
		SI = topPbits[i]
		singlePBITset = len(SI)
		andCnt = 1
		for n in xrange(0, singlePBITset, 2): #choose stepsize=2 b/c MUX has 2 p-bits
			tmpPlist = SI[n:n+2]
			tmpNAND = 'topNAND'+str(i)+'_'+str(andCnt)
			nand2outerAND.append(tmpNAND)
			nandRuleLines += '.names '+tmpPlist[0]+' '+tmpPlist[1]+' '+tmpNAND
			nandRuleLines += '\n0- 1\n-0 1\n'
			andCnt += 1
	"""
	#4.3 build a miter that generate a PI vector that distinguishes new found pbit pair:
	miterMods = []
	miterPOs = []
	for num in range(2):
		subMiterPO = []
		miterSubckt = '.subckt '+lev1model[0]+' '
		for i in range(len(lev1pinputs)):
			miterSubckt += lev1pinputs[i]+'='+distingPI[i]+' '
		for j in range(len(lev1pbits)):
			miterSubckt += lev1pbits[j]+'='+topPbits[num][j]+' '
		for k in range(len(lev1outputs)):
			miterSubckt += lev1outputs[k]+'=miter'+str(num)+'_'+str(k)+' '
			subMiterPO.append('miter'+str(num)+'_'+str(k))
		miterMods.append(miterSubckt)
		miterPOs.append(subMiterPO)	
	genPImtrXORs = ''
	genPImtrORin = []
	#XORs:
	for i in range(len(lev1outputs)):
		subORin = 'mtrORin_'+str(i)
		genPImtrORin.append(subORin)
		subMtrXOR = '.names '+miterPOs[0][i]+' '+miterPOs[1][i]+' '+subORin
		subMtrXOR += '\n10 1\n01 1\n'
		genPImtrXORs += subMtrXOR	
	#ORs:
	genPImtrOR ='.names '+(' ').join(genPImtrORin)+' mtrOut\n'
	for i in range(len(lev1outputs)):
		genPImtrOR += i*'-'+'1'+(len(lev1outputs)-i-1)*'-'+' 1\n'
	#roll the lines together:
	genPImtr = ''
	for subc in miterMods:
		genPImtr += subc+'\n'
	genPImtr += genPImtrXORs
	genPImtr += genPImtrOR

	#4.4 Build the final AND miter:
	#signals ANDed together: nand2outerAND, pb_mtrOut, out of miter which gens PI.
	#finalAND = '.names '
	#4.4.1 add NANDs which rule out the illegal pbit assignments:
	#finalAND += (' ').join(nand2outerAND)
	#4.4.2 add sub miter which rules out same Pbit assignments:
	#finalAND += ' pb_mtrOut '
	#4.4.3 add genPImtrOut:
	#finalAND += ' genPImtrOut finalMtrOut\n'
	#finalAND += '1'*(len(nand2outerAND)+2)+' 1\n'
	#finalAND += '1'*(len(nand2outerAND)+1)+' 1\n'

	#5. complete top level
	#topModel = topModName+topModIn+topModOut+topscs+subMtrDistPbits+nandRuleLines+genPImtr+finalAND+'.end\n'
	topModel = topModName+topModIn+topModOut+topscs+genPImtr+'.end\n'	
	#######################################
	# Combine all levels of models together
	#######################################
	outxt = topModel +'\n'+ level2model +'\n'+ lev1

	with open(compCktPath, 'w') as outfile:
		outfile.write(outxt)
		#print "\nTop miter is generated and stored in '", outputfilePath, "'"
	return None



#################################################
#################################################
#################################################
#################################################



def gateType(line):
	'''determines gate type according to the behavioral description in Verilog'''
	'''Just applys to INV, BUF, AND2, OR2, XOR2.'''


	return



'''
def transINV( lineIn, lineOut ):
	inV = str(lineIn[0])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append(inV+' '+outV+' 0\n')
	cnfLines.append('-'+inV+' -'+outV+' 0\n')
	return cnfLines
	
def transAND( lineIn, lineOut ):
	inV1 = str(lineIn[0])
	inV2 = str(lineIn[1])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append('-'+inV1+' -'+inV2+' '+outV+' 0\n')
	cnfLines.append(inV1+' -'+outV+' 0\n')
	cnfLines.append(inV2+' -'+outV+' 0\n')
	return cnfLines

def transOR( lineIn, lineOut ):
	inV1 = str(lineIn[0])
	inV2 = str(lineIn[1])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append(inV1+' '+inV2+' -'+outV+' 0\n')
	cnfLines.append('-'+inV1+' '+outV+' 0\n')
	cnfLines.append('-'+inV2+' '+outV+' 0\n')
	return cnfLines

def transXOR( lineIn, lineOut ):
	inV1 = str(lineIn[0])
	inV2 = str(lineIn[1])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append('-'+inV1+' -'+inV2+' -'+outV+' 0\n')
	cnfLines.append(inV1+' '+inV2+' -'+outV+' 0\n')
	cnfLines.append(inV1+' -'+inV2+' '+outV+' 0\n')
	cnfLines.append('-'+inV1+' '+inV2+' '+outV+' 0\n')
	return cnfLines

def transNOR( lineIn, lineOut ):
	inV1 = str(lineIn[0])
	inV2 = str(lineIn[1])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append(inV1+' '+inV2+' '+outV+' 0\n')
	cnfLines.append('-'+inV1+' -'+outV+' 0\n')
	cnfLines.append('-'+inV2+' -'+outV+' 0\n')
	return cnfLines

def transNAND( lineIn, lineOut ):
	inV1 = str(lineIn[0])
	inV2 = str(lineIn[1])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append('-'+inV1+' -'+inV2+' -'+outV+' 0\n')
	cnfLines.append(inV1+' '+outV+' 0\n')
	cnfLines.append(inV2+' '+outV+' 0\n')
	return cnfLines

def transBUF( lineIn, lineOut ):
	inV = str(lineIn[0])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append(inV+' -'+outV+' 0\n')
	cnfLines.append('-'+inV+' '+outV+' 0\n')
	return cnfLines

def transZERO( lineIn, lineOut ):
	cnfLines = []
	cnfLines.append('-'+str(lineOut)+' 0\n')
	return cnfLines

def transONE( lineIn, lineOut ):
	cnfLines = []
	cnfLines.append(str(lineOut)+' 0\n')
	return cnfLines
'''


def transINV( lineIn, lineOut ):
	inV = str(lineIn[0])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append(inV+' '+outV+' 0\n')
	cnfLines.append('-'+inV+' -'+outV+' 0\n')
	return cnfLines
	
def transAND( lineIn, lineOut ):
	cnfLines = []
	outV = str(lineOut)
	firstLine = ''
	for inV in lineIn:
		inVstr = str(inV)
		firstLine += '-'+inVstr+' '
		cnfLines.append(inVstr+' -'+outV+' 0\n')
	firstLine += outV+' 0\n'
	cnfLines.insert(0, firstLine)
	return cnfLines

def transOR( lineIn, lineOut ):
	cnfLines = []
	outV = str(lineOut)
	firstLine = ''
	for inV in lineIn:
		inVstr = str(inV)
		firstLine += inVstr+' '
		cnfLines.append('-'+inVstr+' '+outV+' 0\n')
	firstLine += '-'+outV+' 0\n'
	cnfLines.insert(0, firstLine)
	return cnfLines

def transXOR( lineIn, lineOut ):
	inV1 = str(lineIn[0])
	inV2 = str(lineIn[1])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append('-'+inV1+' -'+inV2+' -'+outV+' 0\n')
	cnfLines.append(inV1+' '+inV2+' -'+outV+' 0\n')
	cnfLines.append(inV1+' -'+inV2+' '+outV+' 0\n')
	cnfLines.append('-'+inV1+' '+inV2+' '+outV+' 0\n')
	return cnfLines

def transNOR( lineIn, lineOut ):
	cnfLines = []
	outV = str(lineOut)
	firstLine = ''
	for inV in lineIn:
		inVstr = str(inV)
		firstLine += inVstr+' '
		cnfLines.append('-'+inVstr+' -'+outV+' 0\n')
	firstLine += outV+' 0\n'
	cnfLines.insert(0, firstLine)
	return cnfLines

def transNAND( lineIn, lineOut ):
	cnfLines = []
	outV = str(lineOut)
	firstLine = ''
	for inV in lineIn:
		inVstr = str(inV)
		firstLine += '-'+inVstr+' '
		cnfLines.append(inVstr+' '+outV+' 0\n')
	firstLine += '-'+outV+' 0\n'
	cnfLines.insert(0, firstLine)
	return cnfLines

def transBUF( lineIn, lineOut ):
	inV = str(lineIn[0])
	outV = str(lineOut)
	cnfLines = []
	cnfLines.append(inV+' -'+outV+' 0\n')
	cnfLines.append('-'+inV+' '+outV+' 0\n')
	return cnfLines

def transZERO( lineIn, lineOut ):
	cnfLines = []
	cnfLines.append('-'+str(lineOut)+' 0\n')
	return cnfLines

def transONE( lineIn, lineOut ):
	cnfLines = []
	cnfLines.append(str(lineOut)+' 0\n')
	return cnfLines

#################################################
#################################################
#################################################
#################################################


def oracV2cnf(OracInV, piNum):
	'''Convert oracle input Verilog file to cnf file.'''
	'''The number of variables and the number of clauses are increased to allow assignments to PI vector.'''

	cnfLines = []
	gateTypeDict = {'and':1, 'or':2, 'xor':3, 'inv':4, 'buf':5, 'nand':6, 'nor':7, 'one':8, 'zero':9}
	options = {1:transAND, 2:transOR, 3:transXOR, 4:transINV, 5:transBUF, 6:transNAND, 7:transNOR, 8:transONE, 9:transZERO}

	with open(OracInV, 'r') as infile:
		inV = infile.read()
		Vlines = inV.split(';\n')

	#1.1 Convert the original circuit to CNF format:	
	inputs = [] # stores 2 sets of inputs: PIs and p-bits
	varIndexDict = {}
	intVarDict = {}
	varIndex = 1
	cnFile = []
	#pisIndex = [] #store integer indexes of pis to return
	#piVars = []
	posIndex = []	#store integer indexes of pos to return
	poVars = []
	gateCnt = 0	
	# order of integers: PI vars, programming bit vars, PO vars, internal wire vars;
	for line in Vlines:
		line = line.replace('\n', '')
		if 'input' in line and not '//' in line:
			#print line
			PIs=re.search(r'(?<=input )(.*)(?=$)', line).group().replace(' ','').split(',')
			tmpPis = []
			for pi in PIs:
				pi = pi.replace('\\','').replace('[','').replace(']','')
				varIndexDict[pi] = varIndex
				#intVarDict[varIndex] = pi
				#pisIndex.append(varIndex)
				tmpPis.append(varIndex)
				varIndex += 1
			inputs.append(tmpPis)
		elif 'output' in line and not '//' in line:
			POs=re.search(r'(?<=output )(.*)(?=$)', line).group().replace(' ','').split(',')
			for po in POs:
				po = po.replace('\\','').replace('[','').replace(']','')
				varIndexDict[po] = varIndex
				#intVarDict[varIndex] = po
				posIndex.append(varIndex)
				#poVars.append(po)
				varIndex += 1
		elif 'wire' in line and not '//' in line:
			wires=re.search(r'(?<=wire )(.*)(?=$)', line).group().replace(' ','').split(',')
			for w in wires:
				varIndexDict[w] = varIndex
				#intVarDict[varIndex] = w
				varIndex += 1			
		elif line!='' and line[0]!='/' and not 'module' in line:
			line = line.replace(' ','')
			if '.' in line and '(' in line: #means it is a mapped Verilog
				gate = re.search(r'^(.*)(?=g\S+\(\.)', line).group().strip('1234567890')
			else: #means it is a behavioral Verilog
				gate = gateType(line)
			#convert vars to standard form:
			buf_split = [term.replace('\\','').replace('[','').replace(']','') for term in line.split('.')]
			buf_processed = []
			for i in range(1,len(buf_split)):
				buf_processed.append(re.search(r'\((.*)\)', buf_split[i]).group().strip('( )'))
			#convert standard vars to integer indexes in cnf file:
			lineOut = varIndexDict[buf_processed[-1]]
			lineIn = []
			for i in range(len(buf_processed)-1):
				lineIn.append(varIndexDict[buf_processed[i]])
			#convert logic gate to CNF format:
			caseNo = gateTypeDict[gate]
			cnfLines = options[caseNo](lineIn, lineOut)
			for line in cnfLines:
				cnFile.append(line)
			gateCnt += 1

	timeGend = time.asctime( time.localtime(time.time()) )
	varNum = varIndex-1
	clauseNum = len(cnFile)
	cmmtLine1 = 'c This file is generated by oracV2cnf\n'
	cmmtLine2 = 'c Generated on '+str(timeGend)+'\n'
	clauseNum += piNum #for later expansion with PI assignments
	firstLine = 'p cnf '+str(varNum)+' '+str(clauseNum)+'\n'
	cnFile.insert(0, firstLine)
	cnFile.insert(0, cmmtLine2)
	cnFile.insert(0, cmmtLine1)
	'''
	outxt = ''.join(cnFile)	
	with open(outCNF, 'w') as outfile:
		 outfile.write(outxt)
	'''
	return (inputs[0], posIndex, cnFile)

#################################################
#################################################
#################################################
#################################################
def v2cnfMtr2(camInV):
	'''Converts plain camouflaged verilog file to a cnf miter. Variable number = 2*VarInV + SingleCktOutBitsNum + 1'''

	cnfLines = []
	gateTypeDict = {'and':1, 'or':2, 'xor':3, 'inv':4, 'buf':5, 'nand':6, 'nor':7, 'one':8, 'zero':9}
	options = {1:transAND, 2:transOR, 3:transXOR, 4:transINV, 5:transBUF, 6:transNAND, 7:transNOR, 8:transONE, 9:transZERO}

	with open(camInV, 'r') as infile:
		inV = infile.read()
		Vlines = inV.split(';\n')

	#1.1 Convert the original circuit to CNF format:
	inputs = [] # stores 2 sets of inputs: PIs and p-bits
	varIndexDict = {}
	intVarDict = {}
	varIndex = 1
	cnFile = []
	#pisIndex = [] #store integer indexes of pis to return
	#piVars = []
	posIndex = []	#store integer indexes of pos to return
	poVars = []
	gateCnt = 0
	# order of integers: PI vars, programming bit vars, PO vars, internal wire vars;
	for line in Vlines:
		line = line.replace('\n', '')
		if 'input' in line:
			PIs=re.search(r'(?<=input )(.*)(?=$)', line).group().replace(' ','').split(',')
			tmpPis = []
			for pi in PIs:
				pi = pi.replace('\\','').replace('[','').replace(']','')
				varIndexDict[pi] = varIndex
				#intVarDict[varIndex] = pi
				#pisIndex.append(varIndex)
				tmpPis.append(varIndex)
				varIndex += 1
			inputs.append(tmpPis)
		elif 'output' in line:
			POs=re.search(r'(?<=output )(.*)(?=$)', line).group().replace(' ','').split(',')
			for po in POs:
				po = po.replace('\\','').replace('[','').replace(']','')
				varIndexDict[po] = varIndex
				#intVarDict[varIndex] = po
				posIndex.append(varIndex)
				#poVars.append(po)
				varIndex += 1
		elif 'wire' in line:
			wires=re.search(r'(?<=wire )(.*)(?=$)', line).group().replace(' ','').split(',')
			for w in wires:
				varIndexDict[w] = varIndex
				#intVarDict[varIndex] = w
				varIndex += 1
		elif line!='' and line[0]!='/' and not 'module' in line:
			#print line
			line = line.replace(' ','')
			gate = re.search(r'^(.*)(?=g\S+\(\.)', line).group().strip('1234567890')
			#convert vars to standard form:
			buf_split = [term.replace('\\','').replace('[','').replace(']','') for term in line.split('.')]
			buf_processed = []
			for i in range(1,len(buf_split)):
				buf_processed.append(re.search(r'\((.*)\)', buf_split[i]).group().strip('( )'))
			#convert standard vars to integer indexes in cnf file:
			lineOut = varIndexDict[buf_processed[-1]]
			lineIn = []
			for i in range(len(buf_processed)-1):
				lineIn.append(varIndexDict[buf_processed[i]])
			#convert logic gate to CNF format:
			caseNo = gateTypeDict[gate]
			cnfLines = options[caseNo](lineIn, lineOut)
			for line in cnfLines:
				cnFile.append(line)
			gateCnt += 1
	camVarNum = varIndex-1 #total number of nodes in original ckt
	camCNFile = cnFile[:]

	#1.2 Duplicate the original circuit with different node notations:
	cnFile.append('c The second circuit:\n')
	cnFile2 = []
	for i in xrange(len(cnFile)-1):
		tmpClause = cnFile[i]
		intIndexLs = [tmpInt for tmpInt in tmpClause.split() if tmpInt!=''][:-1]
		newTmpCls = ''
		for j in range(len(intIndexLs)):
			tmpInt = intIndexLs[j]
			if '-' in tmpInt:
				newTmpCls+='-'+str(int(tmpInt.strip('-'))+camVarNum)+' '
			else:
				newTmpCls+=str(int(tmpInt)+camVarNum)+' '
		cnFile2.append(newTmpCls+'0\n')
	#dupCamCktCnf = cnFile+cnFile2
	cnFile = cnFile+cnFile2
	#print cnFile

	# 2. Add constraints:
	#2.1 primary inputs are the same:
	cnFile.append('c Force PIs of 2 ckts to be the same:\n')
	piVec = inputs[0]
	for i in piVec:
		piConsLine1 = str(i)+' -'+str(i+camVarNum)+' 0\n'
		cnFile.append(piConsLine1)
		piConsLine2 = '-'+str(i)+' '+str(i+camVarNum)+' 0\n'
		cnFile.append(piConsLine2)

	#2.2 rule out  illegal assignments (11s):
	cnFile.append('c add constraints for programming bits\n')
	pbitSttInt = len(piVec)+1
	pbitEndInt = pbitSttInt+len(inputs[1])
	for i in range(pbitSttInt, pbitEndInt, 2):
		pbitsConsLine = '-'+str(i)+' -'+str(i+1)+' 0\n'
		cnFile.append(pbitsConsLine)
	for i in range(pbitSttInt+camVarNum, pbitEndInt+camVarNum, 2):
		pbitsConsLine = '-'+str(i)+' -'+str(i+1)+' 0\n'
		cnFile.append(pbitsConsLine)

	#2.3 XOR outputs:
	cnFile.append('c XOR outputs of 2 ckts:\n')
	xorInt = camVarNum*2
	for po in posIndex:
		xorInt += 1
		sig1 = po
		sig2 = po + camVarNum
		poConsLine1='-'+str(sig1)+' -'+str(sig2)+' -'+str(xorInt)+' 0\n'
		cnFile.append(poConsLine1)
		poConsLine2=str(sig1)+' '+str(sig2)+' -'+str(xorInt)+' 0\n'
		cnFile.append(poConsLine2)
		poConsLine3=str(sig1)+' -'+str(sig2)+' '+str(xorInt)+' 0\n'
		cnFile.append(poConsLine3)
		poConsLine4='-'+str(sig1)+' '+str(sig2)+' '+str(xorInt)+' 0\n'
		cnFile.append(poConsLine4)

	#2.4 the last OR:
	cnFile.append('c The last OR gate of the miter:\n')
	#numOfXor = xorNum-1
	orIndex = xorInt+1
	orLine = ''
	for xorInt in range(camVarNum*2+1, orIndex):
		orLine += str(xorInt)+' '
	orLine += '-'+str(orIndex)+' 0\n'
	cnFile.append(orLine)
	orLine1 = ''
	for xorInt in range(camVarNum*2+1, orIndex):
		orLine1 = '-'+str(xorInt)+' '+str(orIndex)+' 0\n'
		cnFile.append(orLine1)
	cnFile.append(str(orIndex)+' 0\n')

	timeGend = time.asctime( time.localtime(time.time()) )
	varNum = orIndex
	clauseNum = len(cnFile)-5 # 5 comments (besides first 3)
	cmmtLine1 = 'c This file is generated by v2cnfMtr\n'
	cmmtLine2 = 'c Generated on '+str(timeGend)+'\n'
	firstLine = 'p cnf '+str(varNum)+' '+str(clauseNum)+'\n'
	cnFile.insert(0, firstLine)
	cnFile.insert(0, cmmtLine2)
	cnFile.insert(0, cmmtLine1)

	# cnFile: the complete miter w/o PI, PO and CB assignments;
	# inputs: [ [PIvec integer indexes], [CBvec integer indexes] ]
	# posIndex: [PO integer indexes]
	# camVarNum: total number of nodes in the original cam ckt
	# camCNFile: the CNF line list of the original cam ckt
	return (cnFile, inputs, posIndex, camVarNum, camCNFile)



def v2cnfMtr4(camInV):
	'''Converts plain camouflaged verilog file to a cnf miter. Variable number = 2*VarInV + SingleCktOutBitsNum + 1'''

	cnfLines = []
	gateTypeDict = {'and':1, 'or':2, 'xor':3, 'inv':4, 'buf':5, 'nand':6, 'nor':7, 'one':8, 'zero':9}
	options = {1:transAND, 2:transOR, 3:transXOR, 4:transINV, 5:transBUF, 6:transNAND, 7:transNOR, 8:transONE, 9:transZERO}

	with open(camInV, 'r') as infile:
		inV = infile.read()
		Vlines = inV.split(';\n')
		
	#1.1 Convert the original circuit to CNF format:	
	inputs = [] # stores 2 sets of inputs: PIs and p-bits
	varIndexDict = {}
	intVarDict = {}
	varIndex = 1
	cnFile = []
	#pisIndex = [] #store integer indexes of pis to return
	#piVars = []
	posIndex = []	#store integer indexes of pos to return
	poVars = []
	gateCnt = 0	
	# order of integers: PI vars, programming bit vars, PO vars, internal wire vars;
	for line in Vlines:
		line = line.replace('\n', '')
		if 'input' in line:
			PIs=re.search(r'(?<=input )(.*)(?=$)', line).group().replace(' ','').split(',')
			tmpPis = []
			for pi in PIs:
				pi = pi.replace('\\','').replace('[','').replace(']','')
				varIndexDict[pi] = varIndex
				#intVarDict[varIndex] = pi
				#pisIndex.append(varIndex)
				tmpPis.append(varIndex)
				varIndex += 1
			inputs.append(tmpPis)
		elif 'output' in line:
			POs=re.search(r'(?<=output )(.*)(?=$)', line).group().replace(' ','').split(',')
			for po in POs:
				po = po.replace('\\','').replace('[','').replace(']','')
				varIndexDict[po] = varIndex
				#intVarDict[varIndex] = po
				posIndex.append(varIndex)
				#poVars.append(po)
				varIndex += 1
		elif 'wire' in line:
			wires=re.search(r'(?<=wire )(.*)(?=$)', line).group().replace(' ','').split(',')
			for w in wires:
				varIndexDict[w] = varIndex
				#intVarDict[varIndex] = w
				varIndex += 1			
		elif line!='' and line[0]!='/' and not 'module' in line:
			#print line
			line = line.replace(' ','')
			gate = re.search(r'^(.*)(?=g\S+\(\.)', line).group().strip('1234567890')
			#convert vars to standard form:
			buf_split = [term.replace('\\','').replace('[','').replace(']','') for term in line.split('.')]
			buf_processed = []
			for i in range(1,len(buf_split)):
				buf_processed.append(re.search(r'\((.*)\)', buf_split[i]).group().strip('( )'))
			#convert standard vars to integer indexes in cnf file:
			lineOut = varIndexDict[buf_processed[-1]]
			lineIn = []
			for i in range(len(buf_processed)-1):
				lineIn.append(varIndexDict[buf_processed[i]])
			#convert logic gate to CNF format:
			caseNo = gateTypeDict[gate]
			cnfLines = options[caseNo](lineIn, lineOut)
			for line in cnfLines:
				cnFile.append(line)
			gateCnt += 1
	camVarNum = varIndex-1 #total number of nodes in original ckt
	camCNFile = cnFile[:]

	#1.2 Duplicate the original circuit with different node notations:
	cnFile.append('c The second circuit:\n')
	cnFile2 = []
	for i in xrange(len(cnFile)-1):
		tmpClause = cnFile[i]
		intIndexLs = [tmpInt for tmpInt in tmpClause.split() if tmpInt!=''][:-1]
		newTmpCls = ''
		for j in range(len(intIndexLs)):
			tmpInt = intIndexLs[j]
			if '-' in tmpInt:
				newTmpCls+='-'+str(int(tmpInt.strip('-'))+camVarNum)+' '
			else:
				newTmpCls+=str(int(tmpInt)+camVarNum)+' '
		cnFile2.append(newTmpCls+'0\n')
	#dupCamCktCnf = cnFile+cnFile2
	cnFile = cnFile+cnFile2
	#print cnFile

	# 2. Add constraints:
	#2.1 primary inputs are the same:
	cnFile.append('c Force PIs of 2 ckts to be the same:\n')
	piVec = inputs[0]
	for i in piVec:
		piConsLine1 = str(i)+' -'+str(i+camVarNum)+' 0\n'
		cnFile.append(piConsLine1)
		piConsLine2 = '-'+str(i)+' '+str(i+camVarNum)+' 0\n'
		cnFile.append(piConsLine2)


	#2.3 XOR outputs:
	cnFile.append('c XOR outputs of 2 ckts:\n')
	xorInt = camVarNum*2
	for po in posIndex:
		xorInt += 1
		sig1 = po
		sig2 = po + camVarNum
		poConsLine1='-'+str(sig1)+' -'+str(sig2)+' -'+str(xorInt)+' 0\n'
		cnFile.append(poConsLine1)
		poConsLine2=str(sig1)+' '+str(sig2)+' -'+str(xorInt)+' 0\n'
		cnFile.append(poConsLine2)
		poConsLine3=str(sig1)+' -'+str(sig2)+' '+str(xorInt)+' 0\n'
		cnFile.append(poConsLine3)
		poConsLine4='-'+str(sig1)+' '+str(sig2)+' '+str(xorInt)+' 0\n'
		cnFile.append(poConsLine4)	

	#2.4 the last OR:
	cnFile.append('c The last OR gate of the miter:\n')
	#numOfXor = xorNum-1
	orIndex = xorInt+1
	orLine = ''
	for xorInt in range(camVarNum*2+1, orIndex):
		orLine += str(xorInt)+' '
	orLine += '-'+str(orIndex)+' 0\n'
	cnFile.append(orLine)
	orLine1 = ''
	for xorInt in range(camVarNum*2+1, orIndex):
		orLine1 = '-'+str(xorInt)+' '+str(orIndex)+' 0\n'
		cnFile.append(orLine1)
	cnFile.append(str(orIndex)+' 0\n')
		
	timeGend = time.asctime( time.localtime(time.time()) )
	varNum = orIndex
	clauseNum = len(cnFile)-5 # 5 comments (besides first 3)
	cmmtLine1 = 'c This file is generated by v2cnfMtr\n'
	cmmtLine2 = 'c Generated on '+str(timeGend)+'\n'
	firstLine = 'p cnf '+str(varNum)+' '+str(clauseNum)+'\n'
	cnFile.insert(0, firstLine)
	cnFile.insert(0, cmmtLine2)
	cnFile.insert(0, cmmtLine1)

	# cnFile: the complete miter w/o PI, PO and CB assignments;
	# inputs: [ [PIvec integer indexes], [CBvec integer indexes] ]
	# posIndex: [PO integer indexes]
	# camVarNum: total number of nodes in the original cam ckt
	# camCNFile: the CNF line list of the original cam ckt
	return (cnFile, inputs, posIndex, camVarNum, camCNFile)




#################################################
#################################################
#################################################
#################################################

#the first oldDupCkt is the baseMtrCnf
def dupCompCkt( camCnf, oldDupCkt, PItemp, POtemp, camVarNum, camPIndex, camCBindex, camPOindex ):
	'''Duplicate the camouflaged ckt and add the duplicated ckts\
	to base miter cnf, then evaluates the pair of new control bits\
	and a PI vector that can distinguish them. '''

	#1. duplicate the camouflaged circuit twice:
	#1.1 get the first int index for duplicated circuits:

		# camCNF is the most basic cam, directly transliation
		# self.newDupCkt is the original cam, directly translation, then it is the last dupCkt
		# Pitemp is current I (from last)
		# POtemp is current O (from last)
		# camVarNum is the number of I+O+CB+W
		# camPIndex is PI's index
		# camCBindex is CB's index
		# camPOindex is PO's index


	prevNodeNum = int(oldDupCkt[2].split()[2])	
	dupCkt1 = []
	dupCkt2 = []
	correction1 = prevNodeNum
	correction2 = correction1+camVarNum
	####1.2 create 2 duplicated circuits
	for i in range(len(camCnf)):
		tmpClause = camCnf[i]
		intIndexLs = [tmpInt for tmpInt in tmpClause.split() if tmpInt!=''][:-1]
		newTmpCls1 = ''
		newTmpCls2 = ''
		for j in range(len(intIndexLs)):
			tmpInt = intIndexLs[j]
			if '-' in tmpInt:
				newTmpCls1+='-'+str(int(tmpInt.strip('-'))+correction1)+' '
				newTmpCls2+='-'+str(int(tmpInt.strip('-'))+correction2)+' '
			else:
				newTmpCls1+=str(int(tmpInt)+correction1)+' '
				newTmpCls2+=str(int(tmpInt)+correction2)+' '
		dupCkt1.append(newTmpCls1+'0\n')		
		dupCkt2.append(newTmpCls2+'0\n')
	####1.3 connect the p-bits of new duplicated ckts with those of the miter:
	firstCBints = camCBindex[:]
	secondCBints = []
	dupCkt1CBints = []
	dupCkt2CBints = []
	for i in range(len(firstCBints)):
		baseCBInt = firstCBints[i]
		secondCBints.append(baseCBInt+camVarNum)
		dupCkt1CBints.append(baseCBInt+correction1)
		dupCkt2CBints.append(baseCBInt+correction2)
	dupCkt1CBset = []
	dupCkt2CBset = []
	for j in range(len(firstCBints)):
		#connect the first set of programming bits:
		line1=str(firstCBints[j])+' -'+str(dupCkt1CBints[j])+' 0\n'
		dupCkt1CBset.append(line1)
		line2='-'+str(firstCBints[j])+' '+str(dupCkt1CBints[j])+' 0\n'
		dupCkt1CBset.append(line2)		
		#connect the second set of programming bits:
		line3=str(secondCBints[j])+' -'+str(dupCkt2CBints[j])+' 0\n'
		dupCkt2CBset.append(line3)
		line4='-'+str(secondCBints[j])+' '+str(dupCkt2CBints[j])+' 0\n'
		dupCkt2CBset.append(line4)	
	####1.4 assign new temp PI vectors to new duplicated circuits:	
	dupCkt1PI = []
	dupCkt2PI = []
	for m in range(len(camPIndex)):
		basePInt = camPIndex[m]
		if PItemp[m] == '1':
			dupCkt1PI.append(str(basePInt+correction1)+' 0\n')
			dupCkt2PI.append(str(basePInt+correction2)+' 0\n')
		elif PItemp[m] == '0':
			dupCkt1PI.append('-'+str(basePInt+correction1)+' 0\n')
			dupCkt2PI.append('-'+str(basePInt+correction2)+' 0\n')	
	####1.5 assign new temp PO vectors to new duplicated circuits:
	dupCkt1PO = []
	dupCkt2PO = []	 		
	for n in range(len(camPOindex)):
		basePOint = camPOindex[n]
		if POtemp[n] == '1':
			dupCkt1PO.append(str(basePOint+correction1)+' 0\n')
			dupCkt2PO.append(str(basePOint+correction2)+' 0\n')
		elif POtemp[n] == '0':
			dupCkt1PO.append('-'+str(basePOint+correction1)+' 0\n')
			dupCkt2PO.append('-'+str(basePOint+correction2)+' 0\n')
	####1.6 merge all new cnf lines together:
	totDupCkt1 = dupCkt1 + dupCkt1CBset + dupCkt1PI + dupCkt1PO
	#print totDupCkt1
	totDupCkt2 = dupCkt2 + dupCkt2CBset + dupCkt2PI + dupCkt2PO
	#print totDupCkt2
	# modify the first working line in CNF:
	firstLine = oldDupCkt[2]
	firstLnLs = firstLine.split()
	firstLnLs[2] = str(prevNodeNum+2*camVarNum)
	firstLnLs[3] = str( int(firstLnLs[3])+2*len(totDupCkt1) )
	oldDupCkt[2] = (' ').join(firstLnLs)+'\n'
	# add new lines to old one:
	newDupCkt = oldDupCkt + ['c New ckt:\n'] + totDupCkt1 + ['c New ckt:\n'] + totDupCkt2

	return newDupCkt




'''

if __name__=='__main__':
	v2cnfMtr('/home/umass/Documents/Rearch-w-Prof-H/ReverseEngineeringProj/benchmarks/iscas-c7552-orac-cam-10-simple.v',10)
	#if nonMiter==False: #means this is a 1-output miter problem		
	#	cnFile.append(str(varIndexDict[POs[0]])+' 0\n')

'''






















