__author__ = 'xiangyu'


def assign(value, index):
    # value is list with element string
    # index is list with element number
    res = []
    for m in range(len(index)):
        baseCBint = index[m]
        if value[m] == '1':
            res.append(str(baseCBint) + ' 0\n')
        elif value[m] == '0':
            res.append('-' + str(baseCBint) + ' 0\n')
    # lineCB = 'This is generated for CB assign\n'
    # res.append(lineCB)
    return res  # a list with string element