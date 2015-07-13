__author__ = 'xiangyu'


def PIgenerator(PIndex, iteration):
    # iteration is the current decimal number, we need to convert in to binary and assign to each input index
    # we need to generate list with string element as input

    '''convert iteration into binary'''
    binary = []

    while iteration > 0:
        binary.append(str(iteration % 2))
        iteration /= 2

    for i in range(len(binary), len(PIndex)):
        binary.append('0')

    binary = binary[::-1]

    return binary









