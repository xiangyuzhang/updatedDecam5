__author__ = 'xiangyu'

import re
# import os
from gatedic import*


def v2cnf(camInV, startIndex):

    gateTypeDict = {'and':1, 'or':2, 'xor':3, 'inv':4, 'buf':5, 'nand':6, 'nor':7, 'one':8, 'zero':9}
    options = {1:transAND, 2:transOR, 3:transXOR, 4:transINV, 5:transBUF, 6:transNAND, 7:transNOR, 8:transONE, 9:transZERO}

    with open(camInV, 'r') as infile:
        inV = infile.read()
        Vlines = inV.split(';\n')


    inputs = []
    varIndexDict = {}
    varIndex = startIndex
    cnFile = []
    posIndex = []
    gateCnt = 0

    for line in Vlines:

        if 'input' in line and not '//' in line:
            line = line.replace('\n', '')
            # print 'This is the line: ', line
            # print 'This is the fucker: ', re.search(r'(?<=input )(.*)(?=$)', line)
            PIs=re.search(r'(?<=input)(.*)(?=$)', line).group().replace(' ','').split(',')
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
            line = line.replace('\n', '')
            POs=re.search(r'(?<=output )(.*)(?=$)', line).group().replace(' ','').split(',')
            for po in POs:
                po = po.replace('\\','').replace('[','').replace(']','')
                varIndexDict[po] = varIndex
                #intVarDict[varIndex] = po
                posIndex.append(varIndex)
                #poVars.append(po)
                varIndex += 1
            print ''
        elif 'wire' in line and not '//' in line:
            line = line.replace('\n', '')
            wires=re.search(r'(?<=wire )(.*)(?=$)', line).group().replace(' ','').split(',')
            for w in wires:
                varIndexDict[w] = varIndex
                #intVarDict[varIndex] = w
                varIndex += 1
        elif line!='' and line[0]!='/' and not 'module' in line:
            line = line.replace('\n', '')
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
    # line1 = 'This is generation for ' + camInV +'\n'
    # cnFile.append(line1)
    camVarNum = varIndex-1
    camCNFile = cnFile[:]
    # print 'This is PI: ', inputs[0]  # input[0] is a list with int elements
    return camCNFile, inputs, posIndex, camVarNum
