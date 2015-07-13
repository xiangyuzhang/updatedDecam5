__author__ = 'xiangyu'

def transINV(lineIn,lineOut):
    inV = str(lineIn[0])
    outV = str(lineOut)
    cnfLines = []
    cnfLines.append(inV+' '+outV+' 0\n')
    cnfLines.append('-'+inV+' -'+outV+' 0\n')
    return cnfLines

def transAND(lineIn,lineOut):
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

def transOR(lineIn,lineOut ):
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

def transXOR(lineIn,lineOut ):
    inV1 = str(lineIn[0])
    inV2 = str(lineIn[1])
    outV = str(lineOut)
    cnfLines = []
    cnfLines.append('-'+inV1+' -'+inV2+' -'+outV+' 0\n')
    cnfLines.append(inV1+' '+inV2+' -'+outV+' 0\n')
    cnfLines.append(inV1+' -'+inV2+' '+outV+' 0\n')
    cnfLines.append('-'+inV1+' '+inV2+' '+outV+' 0\n')
    return cnfLines

def transNOR(lineIn,lineOut ):
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

def transNAND(lineIn,lineOut ):
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

def transBUF(lineIn,lineOut ):
    inV = str(lineIn[0])
    outV = str(lineOut)
    cnfLines = []
    cnfLines.append(inV+' -'+outV+' 0\n')
    cnfLines.append('-'+inV+' '+outV+' 0\n')
    return cnfLines

def transZERO(lineIn,lineOut ):
    cnfLines = []
    cnfLines.append('-'+str(lineOut)+' 0\n')
    return cnfLines

def transONE(lineIn,lineOut ):
    cnfLines = []
    cnfLines.append(str(lineOut)+' 0\n')
    return cnfLines

