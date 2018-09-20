import numpy

data = numpy.genfromtxt('passwords.txt',delimiter="\n",dtype=None)

with open('batch.csv','w') as f:
    for i in range(len(data)/2):
        f.write(data[2*i])
        f.write(',')
        f.write(data[2*i+1])
        f.write('\n')
