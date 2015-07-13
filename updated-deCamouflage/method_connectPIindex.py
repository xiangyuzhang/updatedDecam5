__author__ = 'xiangyu'


def connectPIndex(camInput, startIndex):
    '''This method is to use cnf to force cam's input index to be same with orac's input index'''
    inputConstrain = []

    for i in camInput:
        #  print 'i is: ', i
        #  print 'the str(i+startIndex-1) is', str(i)
        piConsLine1 = str(i) + ' -' + str(i+startIndex-1) + ' 0\n'
        inputConstrain.append(piConsLine1)
        piConsLine2= '-'+str(i)+' '+str(i+startIndex-1) + ' 0\n'
        inputConstrain.append(piConsLine2)
    # line = 'This is generated for connecting PI\n'
    # inputConstrain.append(line)

    return inputConstrain