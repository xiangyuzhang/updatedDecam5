#!/usr/bin/python

'''This version is independent of ABC and still relys on external\
 SAT sovler'''

import os
import readline
import glob
import sys
import time
from subprocess import call, Popen, PIPE, STDOUT
import argparse
from EC_lib import EC

from genMtrs import *
#from abcProc import *
from grabNodes import *
#from abcMapV2CNF import *


def cmmd_and_path_complete(text, state):
	'''automatically complete path'''
	return (glob.glob(text+'*')+[None])[state]+'/'

		
#################################################
#################################################
#################################################
#################################################


class DissectCkt:
	'''This class is used to dissect circuit and find the correct internal components.'''

	def __init__(self, OracIn, CamIn, MuxStyle):

		self.CamInPath = CamIn
		self.OracInPath = OracIn
		#self.ObfGateNum = obfGateNum

		self.OracPIls = [] #PI vectors to Oracle circuit
		self.OracPOls = [] #PO vectors to Oracle circuit	

		self.PItemp = [] #temp found PI vector
		self.POtemp = [] #temp corresponding PO vector
		self.CBPtemp = [[], []] #temp Control Bit Pair

		self.OracPIndex = [] #int indexes for PI bits of Oracle ckt
		self.OracPOindex = [] #int indexes for PO bits of Oracle ckt

		self.pbitsNum = 0 #num of p-bits for an camouflaged ckt
		self.PInum2grab = 0 #num of PI bits of an camouflaged ckt
		self.camPIndex = [] #integer indexes for PI bits of cam ckt
		self.camCBindex = [] #integer indexes for p-bits of cam ckt
		self.camPOindex = [] #integer indexes for PO bits of cam ckt

		self.SATtime = 0
		self.ABCtime = 0

		self.OraCNFile = [] #stores basic Oracle cnf lines
		#there are commnet lines in self.OraCNFile
		self.camCNFile = [] #stores basic camouflaged circuit
		#there is no commnet line in self.camCNFile
		self.baseCnfMtrLs = [] #stores basic miter cnf w/o assignments
		#there are commnet lines in self.baseCnfMtrLs
		self.camVarNum = 0 #total # of vars in orignal cam ckt

		self.newDupCkt = []
		self.MuxStyle = MuxStyle
		#readline.set_completer_delims(' \t\n;')
		#readline.parse_and_bind("tab: complete")	
		#readline.set_completer(cmmd_and_path_complete)


	def _initDissect(self):
		'''generates an initial pair of programming bit assignments, then generates an primary input vector that can distinguish them.'''
		
		print '\n--------------------------------------------------------'
		#print "Generating the first pair of programming bits ... ..."

		
		print"Evaluating the first PI verctor using SAT solver... ..."
		origCkt = re.search(r'(.*)(?=\.)', self.CamInPath).group()
		#baseMtrCnf = origCkt+'-baseMtr.cnf'

		#1. generate the basic miter cnf
		if self.MuxStyle == 4:
			cnfTup = v2cnfMtr4(self.CamInPath)
		elif self.MuxStyle == 2:
			cnfTup = v2cnfMtr2(self.CamInPath)

		self.baseCnfMtrLs = cnfTup[0]
		inputsInt = cnfTup[1]
		self.camPIndex = inputsInt[0]
		self.camCBindex = inputsInt[1]
		self.pbitsNum = len(self.camCBindex)
		self.ObfGateNum = self.pbitsNum/2
		self.camPOindex = cnfTup[2]
		self.camVarNum = cnfTup[3]
		self.camCNFile = cnfTup[4]
		self.PInum2grab = len(self.camPIndex)

		firstMtrCnfLs = self.baseCnfMtrLs[:]
		#firstMtrCnfLs += pbitsCons
		firstMtrTxt = ('').join(firstMtrCnfLs)
		

		firstMtrCnf = origCkt+'-1stMtr.cnf'
		with open(firstMtrCnf, 'w') as outfile: 
			outfile.write(firstMtrTxt)
		initSatLog = origCkt+'-1stMtr.log'
		#satCmmd = 'minisat ' + firstMtrCnf + ' ' + initSatLog
		#if more details about SAT needed, uncomment above line and comment next line
		satCmmd='minisat '+firstMtrCnf+' '+initSatLog+' >> tmpSAT.log'
		print '\n',satCmmd,'\n'
		satTime1=time.time()
		satProc = call(satCmmd, shell=True)
		satTime2=time.time()
		tmpTime = round((satTime2 - satTime1), 4)
		print tmpTime, 'seconds are used for this iteration.'
		self.SATtime += tmpTime

		nodes2grab = (self.camPIndex+self.camCBindex)[:]
		for pbitIndex in self.camCBindex:
			nodes2grab.append(pbitIndex+self.camVarNum)


		#nodes2grab = grabMSnodes(initSatLog, self.PInum2grab+2*self.pbitsNum, True)
		#grab PI_unkn and pbits generated:
		nodes2grab= grabMSnodes2(initSatLog, nodes2grab, True)
		#call('rm '+firstMtrCnf, shell=True)
		#call('rm '+initVfile, shell=True)
		if nodes2grab[0] == True: #means problem is satisfiable:
			del nodes2grab[0]
			self.PItemp = nodes2grab[ :self.PInum2grab ][:]
			self.CBPtemp[0] = nodes2grab[self.PInum2grab:(self.PInum2grab+self.pbitsNum)][:]
			self.CBPtemp[1] = nodes2grab[ (self.PInum2grab+self.pbitsNum): ][:]
			print "\nThe first vector that differentiate (", self.CBPtemp, ") is:\n" 
			print self.PItemp
			return 1
			#print "New input vector added to I."	
		else:
			print "No solution PI found for the first set of programming bits."	
			return 0


	#################################################
	#################################################
	#################################################
	#################################################


	def _findNewPInewCB(self):
		'''find new p-bit pair and a new PI vector that distinguishes them'''

		print '\n---------------------------------------------------------'
		print '1. Look for new programming bit pairs that current PI set can\'t distinguish'
		print '2. If such pair found, look for another PI verctor that can distinguish them' 

		# !!! input order of generated CompCkt: unkPI, S0, S1, PI1, PI2, ...
		# !!! output order: finalMtrOut, PO1, PO2, ...
		#### 1. Build the composite circuit : ####
		compCkt = re.search(r'(.*)(?=\.)', self.CamInPath).group()+'-comp'
		consCNFile = compCkt+'-cons.cnf'
		# duplicate the camouflaged ckt twice and assign with temp PI and temp PO:
		self.newDupCkt = dupCompCkt( self.camCNFile, self.newDupCkt, self.PItemp, self.POtemp, self.camVarNum, self.camPIndex, self.camCBindex, self.camPOindex )
		outxt = ('').join(self.newDupCkt)
		with open(consCNFile, 'w') as outfile:
			outfile.write(outxt)		
		#### 2.    use SAT to solve    #####		
		if os.path.isfile(consCNFile):
			conSatLog = compCkt+'-cons.log'					
			#satCmmd = 'minisat ' + cnFile + ' ' + satLog
			#uncomment above line and comment next line to get more info on SAT
			satCmmd = '\nminisat ' + consCNFile + ' ' + conSatLog + ' >> tmpSAT.log'
			print satCmmd
			satTime3 = time.time()
			satProc = call(satCmmd, shell=True)
			satTime4 = time.time()
			self.SATtime += round((satTime4 - satTime3), 4)

			nodes2grab = (self.camPIndex+self.camCBindex)[:]
			for pbitIndex in self.camCBindex:
				nodes2grab.append(pbitIndex+self.camVarNum)
			#grab I_unkn and pbits generated:
			newPICB= grabMSnodes2(conSatLog, nodes2grab, True)
		if newPICB[0] == True: #means problem is satisfiable:
			del newPICB[0]
			self.PItemp = newPICB[ :self.PInum2grab ][:]
			self.CBPtemp[0] = newPICB[self.PInum2grab:(self.PInum2grab+self.pbitsNum)][:]
			self.CBPtemp[1] = newPICB[ (self.PInum2grab+self.pbitsNum): ][:]
			print '\nNewly found programming bit pair:'
			print self.CBPtemp
			print 'Newly found input vector that distinguishes the above pair:'
			print self.PItemp
			return 1
		else:
			print "Can't find another programming bit pair that makes the out-"
			print "-puts of the 2 components in miter completely the same un-"
			print "-der current PI verctor set"
			return 0


	#################################################
	#################################################
	#################################################
	#################################################


	def _genOracCNF(self):
		'''convert Oracle blif 2 cnf, used for evaluating POs.'''

		#OracPath = re.search(r'(.*)(?=\.)', self.OracInPath).group()
		#OracNFile = OracPath+'.cnf'
		genOraCnfRes = oracV2cnf( self.OracInPath, len(self.PItemp) )
		#if os.path.isfile(OracNFile):
		self.OracPIndex = genOraCnfRes[0]
		self.OracPOindex = genOraCnfRes[1]
		self.OraCNFile = genOraCnfRes[2]	
		return 1	


	def _addIOpair(self):
		'''generates PO for PI-known Oracle ckt and record PI, PO pairs. Then add them into repository.'''

		OracPath = re.search(r'(.*)(?=\.)', self.OracInPath).group()
		consCNFile = OracPath+'-wPI.cnf'

		#1. add PI constraints to cnf file:
		cnfConsLines = ''
		consOracCnfLs = self.OraCNFile[:]
		consOracCnfLs.append('c assign values for PIs:\n')
		numPI=len(self.OracPIndex)
		for i in range(numPI):
			if self.PItemp[i]=='1': 
				cnfConsLines = str(self.OracPIndex[i])+' 0\n'
				consOracCnfLs.append(cnfConsLines)
			elif self.PItemp[i]=='0': 
				cnfConsLines = '-'+str(self.OracPIndex[i])+' 0\n'
				consOracCnfLs.append(cnfConsLines)
		outxt = ('').join(consOracCnfLs)
		with open(consCNFile, 'w') as outfile:
			outfile.write(outxt)

		#2. use SAT to solve constrained Oracle file to get tempOracPO:
		if os.path.isfile(consCNFile):
			conSatLog = OracPath+'-wPI.log'
			#satCmmd = 'minisat ' + OracNFile + ' ' + satLog
			#if more details about SAT needed, uncomment above line and comment next line
			satCmmd = '\nminisat ' + consCNFile + ' ' + conSatLog + ' >> tmpSAT.log'
			print satCmmd,'\n'
			satTime5 = time.time()
			satProc = call(satCmmd, shell=True)
			satTime6 = time.time()
			self.SATtime += round((satTime6 - satTime5), 4)
			tempOracPO = grabMSnodes2(conSatLog, self.OracPOindex, True)			
		#pioCnt = len(self.OracPIls)
		if tempOracPO[0]==True:
			self.OracPIls.append(self.PItemp)
			self.POtemp = tempOracPO[1:][:]
			self.OracPOls.append(self.POtemp)
			print '\nnew PI-PO pair'
			print self.PItemp
			print self.POtemp		
			print 'is added to repository.'
		else:
			print 'No solution found.'
		


	#################################################
	#################################################
	#################################################
	#################################################

	def _findSolu2(self):
		''' find the programming bit assignment solution for the cam ckt.'''

		print '\n---------------------------------------------------------'
		print 'All necessary vectors are collected, now generating solution...'

		### 1. duplicate camouflaged circuits:
		num2dup = len(self.OracPIls)
		totVarNum = num2dup * self.camVarNum

		if num2dup-1 > 0:

			#initialte the # of empty lists as (#-1) of found PI vecs:
			tmpCnfLs = [[] for ls in range((num2dup-1))]

			#1. duplicate
			for i in range(len(self.camCNFile)):
				tmpClause = self.camCNFile[i]
				intIndexLs = [tmpInt for tmpInt in tmpClause.split() if tmpInt!=''][:-1]
				for j in range(num2dup-1):
					newTmpCls = ''
					for k in range(len(intIndexLs)):
						tmpInt = intIndexLs[k]
						if '-' in tmpInt:
							newTmpCls+='-'+str(int(tmpInt.strip('-'))+(j+1)*self.camVarNum)+' '
						else:
							newTmpCls+=str(int(tmpInt)+(j+1)*self.camVarNum)+' '
					tmpCnfLs[j].append(newTmpCls+'0\n')

			#2. p-bit constraints (all connected together):
			firstCBints = self.camCBindex[:]
			for i in range(len(firstCBints)):
				baseCBInt=firstCBints[i]
				for j in range(num2dup-1):
					line1=str(baseCBInt)+' -'+str(baseCBInt+(j+1)*self.camVarNum)+' 0\n'
					tmpCnfLs[j].append(line1)
					line2='-'+str(baseCBInt)+' '+str(baseCBInt+(j+1)*self.camVarNum)+' 0\n'
					tmpCnfLs[j].append(line2)

			#insert original cam cnf as the head of total cnf file:
			tmpCnfLs.insert(0, self.camCNFile)




			for i in range(num2dup): #i-th ckt in tmpCnfLs
				PI2assign = self.OracPIls[i][:] #i-th PI vec
				PO2assign = self.OracPOls[i][:] #i-th PO vec
				#3. assign PIs:
				for j in range(len(self.camPIndex)): #j-th PI bit.
					if PI2assign[j]=='1':
						tmpCnfLs[i].append(str(self.camPIndex[j]+i*self.camVarNum)+' 0\n')
					elif PI2assign[j]=='0':
						tmpCnfLs[i].append('-'+str(self.camPIndex[j]+i*self.camVarNum)+' 0\n')
				#4. assign POs:
				for k in range(len(self.camPOindex)): #k-th PO bit.
					if PO2assign[k]=='1':
						tmpCnfLs[i].append(str(self.camPOindex[k]+i*self.camVarNum)+' 0\n')
					elif PO2assign[k]=='0':
						tmpCnfLs[i].append('-'+str(self.camPOindex[k]+i*self.camVarNum)+' 0\n')


			clauseNum = 0
			finalCNF = []
			for tmpCnf in tmpCnfLs:
				clauseNum += len(tmpCnf)
				finalCNF += tmpCnf
				finalCNF.append('c New duplicated circuit:\n')
			finalCNF.pop()

		else:
			finalCNF = self.camCNFile[:]
			# rule rule out illegal p-bit assignments (11s), add them to the first ckt module:
			for pbit in range(self.camCBindex[0], self.camCBindex[-1], 2):
				soluCBline = '-'+str(pbit)+' -'+str(pbit+1)+' 0\n'
				finalCNF.append(soluCBline)

			# assign PIs:
			PI2assign = self.OracPIls[0]
			for i in range(len(PI2assign)):
				if PI2assign[i]=='1':
					finalCNF.append(str(self.camPIndex[i])+' 0\n')
				elif PI2assign[i]=='0':
					finalCNF.append('-'+str(self.camPIndex[i])+' 0\n')
			PO2assign = self.OracPOls[0]
			for i in range(len(PO2assign)):
				if PO2assign[i]=='1':
					finalCNF.append(str(self.camPOindex[i])+' 0\n')
				elif PO2assign[i]=='0':
					finalCNF.append('-'+str(self.camPOindex[i])+' 0\n')
			clauseNum = len(finalCNF)

		timeGend = time.asctime( time.localtime(time.time()) )
		cmmtLine1 = 'c This file is generated by _findSolu\n'
		cmmtLine2 = 'c Generated on '+str(timeGend)+'\n'
		firstLine = 'p cnf '+str(totVarNum)+' '+str(clauseNum)+'\n'
		finalCNF.insert(0, firstLine)
		finalCNF.insert(0, cmmtLine2)
		finalCNF.insert(0, cmmtLine1)
		outxt = ('').join(finalCNF)

		findSoluFile = re.search(r'(.*)(?=\.)', self.CamInPath).group()+'-_findSolu'
		findSoluCnf = findSoluFile+'.cnf'
		with open(findSoluCnf, 'w') as outfile:
			outfile.write(outxt)

		###### 2.3.    use SAT to solve    #####
		if os.path.isfile(findSoluCnf):
			conSatLog = findSoluFile+'.log'
			#satCmmd = 'minisat ' + cnFile + ' ' + satLog
			#uncomment above line and comment next line to get more info on SAT
			satCmmd = '\nminisat ' + findSoluCnf + ' ' + conSatLog + ' >> tmpSAT.log'
			print satCmmd, '\n'
			satTime7 = time.time()
			satProc = call(satCmmd, shell=True)
			satTime8 = time.time()
			self.SATtime += round((satTime8 - satTime7), 4)
			#grab pbits generated:
			solu= grabMSnodes2(conSatLog, self.camCBindex, True)
		if solu[0]==True:
			print "\nThe final solution for the programming bits is:"
			print solu[1:]
			print 'Number of PI vectors need:', len(self.OracPIls)
			print 'Number of bits in one PI vector:', len(self.OracPIls[0])
			print 'Number of bits in solution CB:', len(self.camCBindex)
			print 'Number of bits in one PO vector:', len(self.OracPOls[0])

			print '\n---------------------------------------------------------'
			line1 =  str(len(self.OracPIls)) + ' Vectors are needed.'
			line2 = 'Total time used in MINISAT (including calling time):'
			line3 = str(self.SATtime) + ' seconds.'
			return line1+'\n'+line2+'\n'+line3+'\n'
		else:
			print 'No solution found!!!!'
			return 'None\n'


	def _findSolu4(self):
		''' find the programming bit assignment solution for the cam ckt.'''

		print '\n---------------------------------------------------------'
		print 'All necessary vectors are collected, now generating solution...'

		### 1. duplicate camouflaged circuits:		
		num2dup = len(self.OracPIls)
		totVarNum = num2dup * self.camVarNum

		if num2dup-1 > 0:

			#initialte the # of empty lists as (#-1) of found PI vecs:
			tmpCnfLs = [[] for ls in range((num2dup-1))]

			#1. duplicate
			for i in range(len(self.camCNFile)):
				tmpClause = self.camCNFile[i]
				intIndexLs = [tmpInt for tmpInt in tmpClause.split() if tmpInt!=''][:-1]
				for j in range(num2dup-1):				
					newTmpCls = ''
					for k in range(len(intIndexLs)):
						tmpInt = intIndexLs[k]
						if '-' in tmpInt:
							newTmpCls+='-'+str(int(tmpInt.strip('-'))+(j+1)*self.camVarNum)+' '
						else:
							newTmpCls+=str(int(tmpInt)+(j+1)*self.camVarNum)+' '
					tmpCnfLs[j].append(newTmpCls+'0\n')

			#2. p-bit constraints (all connected together):
			firstCBints = self.camCBindex[:]
			for i in range(len(firstCBints)):
				baseCBInt=firstCBints[i]
				for j in range(num2dup-1):
					line1=str(baseCBInt)+' -'+str(baseCBInt+(j+1)*self.camVarNum)+' 0\n'
					tmpCnfLs[j].append(line1)
					line2='-'+str(baseCBInt)+' '+str(baseCBInt+(j+1)*self.camVarNum)+' 0\n'					
					tmpCnfLs[j].append(line2)
			
			#insert original cam cnf as the head of total cnf file:
			tmpCnfLs.insert(0, self.camCNFile)



	
			for i in range(num2dup): #i-th ckt in tmpCnfLs
				PI2assign = self.OracPIls[i][:] #i-th PI vec
				PO2assign = self.OracPOls[i][:] #i-th PO vec
				#3. assign PIs:
				for j in range(len(self.camPIndex)): #j-th PI bit.
					if PI2assign[j]=='1':
						tmpCnfLs[i].append(str(self.camPIndex[j]+i*self.camVarNum)+' 0\n')
					elif PI2assign[j]=='0':
						tmpCnfLs[i].append('-'+str(self.camPIndex[j]+i*self.camVarNum)+' 0\n')
				#4. assign POs:
				for k in range(len(self.camPOindex)): #k-th PO bit. 
					if PO2assign[k]=='1':
						tmpCnfLs[i].append(str(self.camPOindex[k]+i*self.camVarNum)+' 0\n')
					elif PO2assign[k]=='0':
						tmpCnfLs[i].append('-'+str(self.camPOindex[k]+i*self.camVarNum)+' 0\n')		


			clauseNum = 0
			finalCNF = []
			for tmpCnf in tmpCnfLs:
				clauseNum += len(tmpCnf)
				finalCNF += tmpCnf		
				finalCNF.append('c New duplicated circuit:\n')
			finalCNF.pop()

		else:
			finalCNF = self.camCNFile[:]

			
			# assign PIs:
			PI2assign = self.OracPIls[0]
			for i in range(len(PI2assign)):
				if PI2assign[i]=='1':
					finalCNF.append(str(self.camPIndex[i])+' 0\n')
				elif PI2assign[i]=='0':
					finalCNF.append('-'+str(self.camPIndex[i])+' 0\n')
			PO2assign = self.OracPOls[0]
			for i in range(len(PO2assign)):
				if PO2assign[i]=='1':
					finalCNF.append(str(self.camPOindex[i])+' 0\n')
				elif PO2assign[i]=='0':
					finalCNF.append('-'+str(self.camPOindex[i])+' 0\n')			
			clauseNum = len(finalCNF)

		timeGend = time.asctime( time.localtime(time.time()) )
		cmmtLine1 = 'c This file is generated by _findSolu\n'
		cmmtLine2 = 'c Generated on '+str(timeGend)+'\n'
		firstLine = 'p cnf '+str(totVarNum)+' '+str(clauseNum)+'\n'
		finalCNF.insert(0, firstLine)
		finalCNF.insert(0, cmmtLine2)
		finalCNF.insert(0, cmmtLine1)		
		outxt = ('').join(finalCNF)

		findSoluFile = re.search(r'(.*)(?=\.)', self.CamInPath).group()+'-_findSolu'
		findSoluCnf = findSoluFile+'.cnf'
		with open(findSoluCnf, 'w') as outfile:
			outfile.write(outxt)

		###### 2.3.    use SAT to solve    #####		
		if os.path.isfile(findSoluCnf):
			conSatLog = findSoluFile+'.log'					
			#satCmmd = 'minisat ' + cnFile + ' ' + satLog
			#uncomment above line and comment next line to get more info on SAT
			satCmmd = '\nminisat ' + findSoluCnf + ' ' + conSatLog + ' >> tmpSAT.log'
			print satCmmd, '\n'
			satTime7 = time.time()
			satProc = call(satCmmd, shell=True)
			satTime8 = time.time()
			self.SATtime += round((satTime8 - satTime7), 4)
			#grab pbits generated:
			solu= grabMSnodes2(conSatLog, self.camCBindex, True)
		if solu[0]==True:
			print "\nThe final solution for the programming bits is:"
			print solu[1:]	
			print 'Number of PI vectors need:', len(self.OracPIls)
			print 'Number of bits in one PI vector:', len(self.OracPIls[0])
			print 'Number of bits in solution CB:', len(self.camCBindex)
			print 'Number of bits in one PO vector:', len(self.OracPOls[0])

			print '\n---------------------------------------------------------'
			line1 =  str(len(self.OracPIls)) + ' Vectors are needed.'
			line2 = 'Total time used in MINISAT (including calling time):'
			line3 = str(self.SATtime) + ' seconds.'		
			return line1+'\n'+line2+'\n'+line3+'\n'	
		else:
			print 'No solution found!!!!'
			return 'None\n'
	

	#################################################
	#################################################
	#################################################
	#################################################


	def _main(self):
		'''Integrates functions.'''

		iterCnt = 1
		iterTimeRec = {}
		#1. _initDissect: gen initial PI and PO:
		time1=time.time()
		initRes = self._initDissect()
		time2=time.time()
		if initRes==1:
			print '\n---------------------------------------------------------'
			print 'Evaluating the PO of Oracle circuit given newly found PI ... ...'
			self._genOracCNF()
			#2. generate PO w.r.t new PI for Oracle ckt:
			time3=time.time()
			self._addIOpair()
			time4=time.time()
			iterTimeRec[iterCnt] = round(time4-time3+time2-time1, 4)
			iterCnt += 1
			#3. iteratively look for new p-bit pairs and PI:
			iterate = 1
			#the first newDupCkt is the baseMtrCnf:
			self.newDupCkt = self.baseCnfMtrLs[:]
			while iterate==1:
				#self.newDupCkt is updated internally:
				time1=time.time()
				iterate=self._findNewPInewCB()
				time2=time.time()
				if iterate == 1:
					time3=time.time()
					self._addIOpair()
					time4=time.time()
					iterTimeRec[iterCnt]=round(time4-time3+time2-time1, 4)
				else:
					iterTimeRec[iterCnt]=round(time2-time1, 4)
				iterCnt += 1
				print '\n---------------------------------------------------------'
				#print 'Current collected PI-PO pairs of the oracle circuit:'
				#print 'Primary input vectors:'
				#print self.OracPIls	
				#print 'Primary output vectors:'
				#print self.OracPOls
			#4. find final solution:
			if self.MuxStyle == 4:
				res = self._findSolu4()
			elif self.MuxStyle == 2:
				res = self._findSolu2()
			res = '\n\n'+self.CamInPath+'\n'+res
			res += "iteration\ttime (s)\n"
			for i in iterTimeRec:
				res += str(i)+'\t:\t'+str(iterTimeRec[i])+'\n'
			return res
		else:
			return 'No solution found.\n'



#################################################
#################################################
#################################################
#################################################


def rundecam():

	readline.set_completer_delims(' \t\n;')
	readline.parse_and_bind("tab: complete")	
	readline.set_completer(cmmd_and_path_complete)

	print "\n\t########## Welcome to SAT SLOVER system. ##########"
	print "\t#This system is used to solve the camouflaged ckt #"
	print "\t#reverse engineering problem.                     #"
	print "\t###################################################"
	print "\n\tThis program dissects circuit and finds the correct" 
	print "\tinternal components. User needs to inform the number"
	print "\tof obfuscated gates in the circuit. The program now c-"
	print "\t-onsiders 3 choices for each obfuscated gate by default.\n"	
	

	parser = argparse.ArgumentParser(usage='python decam-v4-cmmdline.py [-h] <orac.v> <cam.v> [-o <res_file>]', description='This program will use orac.v and cam.v to generate a programming bit vector (if exists)\
	that can make the cam.v has the same function as orac.v. The results and solution are presented in the\
	  output file.',)
	parser.add_argument('<orac.v>', help='input oracle Verilog file that defines the function of the circuit')
	parser.add_argument('<cam.v>', help='the camouflaged circuit that we want to solve.')
	parser.add_argument('-o', "--res_file", nargs='?', type=argparse.FileType('a'), help='output file')
	args = parser.parse_args()
	outfile = args.res_file


	MuxStyle = int (input("Please define Mux Style: \n" \
		  					"4 for MUX4\n" \
		  					"2 for MUX2\n"))

	orcIn = sys.argv[1]
	OracInPath = os.path.abspath(orcIn)

	if not os.path.isfile(OracInPath):
		print 'Invalid oracle circuit file!!!!\n'
		return	
	camIn = sys.argv[2]
	CamInPath = os.path.abspath(camIn)

	if not os.path.isfile(CamInPath):
		print 'Invalid camouflaged circuit file!!!!\n'
		return
	#obfGateNum = raw_input('>>> ')
	#obfGateNum = int(obfGateNum)


#	MuxStyle = 2
	if MuxStyle is not 4 and MuxStyle is not 2:
		print "MuxStyle can not accept!!!"
		return

	totTime1 = time.time()
	mainClass = DissectCkt(OracInPath, CamInPath, MuxStyle)
	res = mainClass._main()
	totTime2 = time.time()
	totTime = round(totTime2-totTime1, 4)
	line4 = 'The total time used (including file parse time) is\n'
	line5 = str(totTime)+' s\n'
	res += line4
	res += line5
	if outfile != None:
		outfile.write(res)
		outfile.close()
		print 'Result is written in', os.path.abspath(outfile.name) #b/c 'outfile' is a file object
	else:
		print res


	print 'Thank you!\n'
	#outfilepath = os.path.abspath(outfile)
	


if __name__=='__main__':
	rundecam()










