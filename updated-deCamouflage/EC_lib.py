

from method_v2cnf import*
from method_XOROR import*
from method_connectPIindex import connectPIndex
from method_grabNodes import grabMSnodes2
from method_CBassign import assign
from method_PIgenerator import PIgenerator
from subprocess import call, Popen, PIPE, STDOUT
import sys
import os
import argparse
import readline

def EC(Orac, Cam, CBfile):
    OraCNF = []  # used to store Orac CNF
    CamCNF = []  # used to store Cam CNF
    CB = []  # used to store CB value list grabbed from solu.log
    CBassign = []  # used to store CB assignment cnf to CB index
    index1 = 0  # used to store index1 after v2cnf
    index2 = 0  # used to store index2 after v2cnf
    milter = []  # used to store milter cnf
    OracInput = []  # used to store orac circuit input index1 list
    OracOutput = []  # used to store orac circuit output index1 list
    CamInput = []  # used to store cam circuit input index1 list, two elements list
    CamOutput = []  # used to store cam circuit output index1 list

    InputConstrain = []  # used to store cnf to connect PI index1
    OutputConstrain = []   # used to store cnf to connect PO with XOR and OR
    PIassign = []  # used to store temp PI assignment
    milterRES = ''
    varNum = 0
    clauseNum = 0


    CamCNF = v2cnf(Cam, 1)[0]
    CamInput = v2cnf(Cam, 1)[1]
    # print 'This is cam input index', CamInput[0][:]
    # print 'This is can CB index', CamInput[1][:]
    CamOutput = v2cnf(Cam, 1)[2]
    # print 'This is cam out index', CamOutput[:]
    index1 = v2cnf(Cam, 1)[3]
    # print 'This is start index for oracl ', index1
    OraCNF = v2cnf(Orac, index1+1)[0]
    OracInput = v2cnf(Orac, index1+1)[1]
    # print 'This is ora input index', OracInput[0][:]
    OracOutput = v2cnf(Orac, index1+1)[2]
    # print 'This is ora output index', OracOutput[:]
    index2 = v2cnf(Orac, index1+1)[3]
    # print 'This is ora last index', index2

    '''now we need to combine the two circuits'''
    milter = CamCNF + OraCNF
    #for line in milter:
    #    with open('milter_check.cnf', 'a') as outfile:
    #        outfile.write(line)
    #print 'The milter_check is stored at: ', os.path.abspath(outfile.name)

    '''Now we append constrain to connect both input index1'''
    lineInCons= 'This is PI connection\n'
    InputConstrain = connectPIndex(CamInput[0], index1+1)
    milter = milter + InputConstrain
    #for line in InputConstrain:
    #    with open('InputConstrain_check.cnf', 'a') as outfile:
    #        outfile.write(line)
    #print 'The InputConstrain_check is stored at: ', os.path.abspath(outfile.name)

    '''Now we need to add XOR and AND for each Output'''
    lineXORAND = 'This is XORAND\n'
    OutputConstrain = addXOROR(CamOutput, OracOutput, index1, index2)[0]
    milter = milter + OutputConstrain
    #for line in OutputConstrain:
    #    with open('OutputConstrain_check.cnf', 'a') as outfile:
    #        outfile.write(line)
    #print 'The OutputConstrain_check is stored at: ', os.path.abspath(outfile.name)

    '''Now we need to grab CB from findSolu.log'''
    CB = grabMSnodes2(CBfile, CamInput[1], True)[1:]

    '''Now we need to assign CB to corresponding index'''
    lineCB = 'This is CB assign\n'
    CBassign = assign(CB, CamInput[1])
    milter = milter + CBassign
    #for line in CBassign:
    #    with open('CBassign_check', 'a') as outfile:
    #        outfile.write(line)
    #print 'The CNassign_check.cnf is stored at: ', os.path.abspath(outfile.name)

    '''finalize milter'''
    varNum = addXOROR(CamOutput, OracOutput, index1, index2)[1]
    clauseNum = len(milter)
    cmmtLine1 = 'c This file is generated by v2cnf\n'
    firstLine = 'p cnf '+str(varNum)+' '+str(clauseNum)+'\n'
    milter.insert(0, firstLine)
    milter.insert(0, cmmtLine1)
    milterRES = ('') .join(milter[:])

    for line in milter:
        with open('milter_result.cnf','a') as outfile:
            outfile.write(line)

    satCmmd = 'minisat ' + 'milter_result.cnf' + ' ' + 'iniSatLog' + ' >> tmpSAT.log'
    satProc = call(satCmmd, shell=True)
    os.remove('milter_result.cnf')  # used to consistently testing, delete when finish debugging
    with open('iniSatLog', 'r') as infile:
        lines = infile.read().split('\n')
    if lines[0] == 'UNSAT':
        return 1  # means correct
    elif line[0] == 'SAT':
        return 0  #means not correct
    else:
        return  'BUG!'







