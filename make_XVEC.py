import fileinput

for line in fileinput.input('vectors/trials.txt', inplace=True):
    line = line.replace('[', '')
    print(line)

for line in fileinput.input('vectors/trials.txt', inplace=True):
    line = line.replace(']','\n')
    print(line)

    
