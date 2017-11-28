from __future__ import print_function
from multiprocessing import Process,BoundedSemaphore
import os,sys
import argparse
import time

def emptyCaches(bucket):
#    os.system('./stop_viewer.sh')
    s = './restart_gcsfuse.sh ' +  bucket
    os.system(s)
#    os.system('./start_viewer.sh')

def readRanges(args, ranges, next, counts, sema):
    slide = file(args.slide,'r')

    for count in range(counts):
        slide.seek(ranges[next][0])
        bytes = slide.read(ranges[next][1])
        next += 1

    slide.close()
    sema.release()

def buildRanges(args,ranges):
    lines = file("offsetByte",'r')
    r = 0
    for line in lines:
        srange = line.split()
        n0 = int(srange[0])
        n1 = int(srange[1])
        arange = (n0,n1)
        ranges.append(arange);
        if args.verbosity > 1:
            print("{} {}".format(r,arange))
            r += 1
    if args.verbosity >= 2:
        print("{}".format(ranges))
                  
def measure(args,ranges):
    procs=[]
    sema=BoundedSemaphore(int(args.procs))
    
    next = 0;
    left = len(ranges)
    batch = (left/args.procs)+1

    for proc in range(args.procs):

        sema.acquire()
        counts = max(min(left,batch),0)
        if args.verbosity >1:
            print("{} {} {}".format(proc, next, counts))
        p = Process(target = readRanges, args = (args, ranges, next, counts, sema))
        p.start()
        procs.append((p,dir))
        next += batch
        left -= batch

    for p in procs:
        p[0].join()
        if args.verbosity >1:
            print ("join {}".format(p),file=sys.stdout)

def parseargs():
    parser = argparse.ArgumentParser(description="Build svs image metadata table")
    parser.add_argument ( "-v", "--verbosity", action="count",default=1,help="increase output verbosity" )
    parser.add_argument ( "-s", "--slide", type=str, help="File path", default='/home/bcliffor/git-home/quip_distro/data/img/isb-cgc-open/NCI-GDC/legacy/TCGA/TCGA-CHOL/Other/Diagnostic_image/09074f6d-932b-43db-b086-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs')
#    parser.add_argument ( "-t", "--tiles", type=str, help="File path", default='tiles.txt')
#    parser.add_argument ( "-u", "--urls", type=str, help="File to collect urls", default='urls.txt')
    parser.add_argument ( "-p", "--procs", type=int, help="Processes", default=1)
    parser.add_argument ( "-r", "--reps", type=int, help="Repetitions", default=1)
    parser.add_argument ( "-f", "--flush", type=int, help="Flush cache", default=1)
    return(parser.parse_args())

if __name__ == '__main__':
    args=parseargs()
    print(args)
    ranges = []
    buildRanges(args, ranges)
#    print("{}".format(args.slide),file=sys.stdout)
    totalTime = 0

    bucket = args.slide.split('/')[7]
    for rep in range(args.reps):

        if args.flush:
            emptyCaches(bucket)

        t0 = time.time()
        measure(args,ranges)
        t1 = time.time()
        if args.verbosity > 1:
            print("{} seconds".format(t1-t0),file=sys.stderr)
        totalTime += (t1-t0)

    print("Avg {} seconds".format(totalTime/args.reps),file=sys.stdout)
