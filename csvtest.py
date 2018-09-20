import numpy

origin = numpy.genfromtxt('test.csv', delimiter=",",dtype=None)

dest = []
for cell in origin:
    str = cell.strip()
    first_space = str.find(' ')
    dest.append([str[0:first_space],str[first_space:len(str)].strip()])




