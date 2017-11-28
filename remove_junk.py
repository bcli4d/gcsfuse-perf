
inputf = file('raw_requests.txt','r')
outputf = file('tiles.txt','w')

for line in inputf:
    if line.find("curl 'http://35.203.177.233/fcgi-bin/iipsrv.fcgi?DeepZoom=" )>=0:
        if line.find('dzi') < 0:
            line = line[0:line.find('jpg')] + 'jpg'
            line = line[line.find('_files'):]
            outputf.write(line+'\n')
outputf.close()
inputf.close() 
