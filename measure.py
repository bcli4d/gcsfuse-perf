from __future__ import print_function
from multiprocessing import Process,BoundedSemaphore
import os,sys
import argparse
import time

def emptyCaches():
    os.system('./restart_gcsfuse.sh')
    os.system('./restart_viewer.sh')

def readTile(s,sema):
    os.system(s)
    sema.release()

def measure(args):

    procs=[]
    sema=BoundedSemaphore(int(args.procs))

    inputf = file(args.tiles,'r')
    for line in inputf:
        s = "curl -s 'http://35.203.177.233/fcgi-bin/iipsrv.fcgi?DeepZoom='"+args.slide+line.rstrip()+">/dev/null"
#        print (line.rstrip())
#        os.system(s)
        sema.acquire()
        p = Process(target = readTile, args = (s,sema))
        p.start()
        procs.append((p,dir))
            
    for p in procs:
        p[0].join()

    inputf.close()

def parseargs():
    parser = argparse.ArgumentParser(description="Build svs image metadata table")
    parser.add_argument ( "-v", "--verbosity", action="count",default=1,help="increase output verbosity" )
    parser.add_argument ( "-s", "--slide", type=str, help="File path", default='/data/images/isb-cgc-open/NCI-GDC/legacy/TCGA/TCGA-CHOL/Other/Diagnostic_image/09074f6d-932b-43db-b086-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs')
    parser.add_argument ( "-t", "--tiles", type=str, help="File path", default='tiles.txt')
    parser.add_argument ( "-p", "--procs", type=str, help="Number of concurrent processes to run", 
                          default='8')
    parser.add_argument ( "-r", "--reps", type=int, help="Repetitions", default=1)
    return(parser.parse_args())

if __name__ == '__main__':
    args=parseargs()

    print("{}".format(args.slide),file=sys.stdout)
    print("{} threads".format(args.procs),file=sys.stdout)
    totalTime = 0
    for rep in range(args.reps):

        emptyCaches()

        t0 = time.time()
        measure(args)
        t1 = time.time()
        print("{} seconds".format(t1-t0),file=sys.stdout)
        totalTime += (t1-t0)

    print("Avg {} seconds".format(totalTime/args.reps),file=sys.stdout)
