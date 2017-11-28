
inputf = file('gcsfuse.log','r')
outputf = file('offsetByte','w')

for line in inputf:
    o = line.find("offset")
    if o >= 0:
        s = line[o:]
        t = s.split()
        n1 = t[1].split(',')[0]
        n2 = t[2]
        outputf.write(n1+' '+n2+'\n')
outputf.close()
inputf.close() 
