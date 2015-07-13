__author__ = 'xiangyu'


def addXOROR(camOut, oraOut, startIndex1, startindex2):
    xorInt = startindex2
    cnFile = []
    i = 0
    for po in camOut:
        xorInt += 1
        sig1 = po
        sig2 = oraOut[i]
        i+=1
        poConsLine1 = '-'+str(sig1)+' -'+str(sig2)+' -'+str(xorInt)+' 0\n'
        cnFile.append(poConsLine1)
        poConsLine2 = str(sig1)+' '+str(sig2)+' -'+str(xorInt)+' 0\n'
        cnFile.append(poConsLine2)
        poConsLine3 = str(sig1)+' -'+str(sig2)+' '+str(xorInt)+' 0\n'
        cnFile.append(poConsLine3)
        poConsLine4 = '-'+str(sig1)+' '+str(sig2)+' '+str(xorInt)+' 0\n'
        cnFile.append(poConsLine4)

    orIndex = xorInt+1
    orLine = ''
    for xorInt in range(startindex2+1, orIndex):
        orLine += str(xorInt)+' '
    orLine += '-' + str(orIndex)+' 0\n'
    cnFile.append(orLine)
    orLine1 = ''
    for xorInt in range(startindex2+1, orIndex):
        orLine1= '-'+str(xorInt)+' ' + str(orIndex)+' 0\n'
        cnFile.append(orLine1)
    cnFile.append(str(orIndex) + ' 0\n')
    # line = 'This is generated for XORAND\n'
    # cnFile.append((line))

    return cnFile, orIndex
