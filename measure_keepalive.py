from __future__ import print_function
from multiprocessing import Process,BoundedSemaphore
import os,sys
import argparse
import time

def emptyCaches():
    os.system('./stop_viewer.sh')
    os.system('./restart_gcsfuse.sh')
    os.system('./start_viewer.sh')

def readTiles(args, proc, sema):
    os.system("curl -s -K "+ "urls"+str(proc) + '> /dev/null')
    sema.release()

def genUrls(args):
    inputf = file(args.tiles,'r')
    outputf = []
    # Open a url out file for each process
    for proc in range(args.procs) :
        outputf.append(file("urls"+str(proc),'w'))
    proc = 0;
    for line in inputf:
        s = 'url="http://35.203.177.233/fcgi-bin/iipsrv.fcgi?DeepZoom='+args.slide+line.rstrip()+'"'
        outputf[proc].write(s+'\n')
        proc = (proc+1) % args.procs
    for proc in range(args.procs):
        outputf[proc].close
    inputf.close()

def measure(args):
    procs=[]
    sema=BoundedSemaphore(int(args.procs))

    for proc in range(args.procs):
                 
        sema.acquire()
        p = Process(target = readTiles, args = (args,proc,sema))
        p.start()
        procs.append((p,dir))
        if args.verbosity >1:
            print ("start {}".format(proc),file=sys.stdout)

    for p in procs:
        p[0].join()
        if args.verbosity >1:
            print ("join {}".format(p),file=sys.stdout)

def parseargs():
    parser = argparse.ArgumentParser(description="Build svs image metadata table")
    parser.add_argument ( "-v", "--verbosity", action="count",default=1,help="increase output verbosity" )
    parser.add_argument ( "-s", "--slide", type=str, help="File path", default='/data/images/isb-cgc-open/NCI-GDC/legacy/TCGA/TCGA-CHOL/Other/Diagnostic_image/09074f6d-932b-43db-b086-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs')
    parser.add_argument ( "-t", "--tiles", type=str, help="File path", default='tiles.txt')
#    parser.add_argument ( "-u", "--urls", type=str, help="File to collect urls", default='urls.txt')
    parser.add_argument ( "-p", "--procs", type=int, help="Processes", default=1)
    parser.add_argument ( "-r", "--reps", type=int, help="Repetitions", default=1)
    parser.add_argument ( "-f", "--flush", type=int, help="Flush cache", default=1)
    return(parser.parse_args())

if __name__ == '__main__':
    args=parseargs()
    print(args)

    genUrls(args)
    print("{}".format(args.slide),file=sys.stdout)
    totalTime = 0
    for rep in range(args.reps):

        if args.flush:
            emptyCaches()

        t0 = time.time()
        measure(args)
        t1 = time.time()
        print("{} seconds".format(t1-t0),file=sys.stdout)
        totalTime += (t1-t0)

    print("Avg {} seconds".format(totalTime/args.reps),file=sys.stdout)
