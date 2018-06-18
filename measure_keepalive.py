from __future__ import print_function
from multiprocessing import Process,BoundedSemaphore
import os,sys
import argparse
import time
import pycurl
from StringIO import StringIO
import subprocess
from time import sleep

# This app reads tiles from an SVS file. The tiles to be read are first divided up among N files. Then, 
# N processes are launched, each of which reads the tiles for which it is responsible. 
# The processes issue requests to the iipsrv.fcgi service on the local host, where iipsrv is presumably
# running.                                                                    

def emptyCaches():
    # The following presumes that quip-distro is installed locally.
    os.system('/etc/rc.local')

def readTiles(args, proc, sema):
    subprocess.call(['/usr/bin/curl', '-k', '-K', '/home/cvproc/gcsfuse-perf/urls0'])
    sema.release()

def genUrls(args):
    inputf = file(args.tiles,'r')
    outputf = []
    # Open a url out file for each process
    for proc in range(args.procs) :
        outputf.append(file("urls"+str(proc),'w'))
    proc = 0;

    for line in inputf:
        # Instead of sending all of stdout to /dev/null, we have curl write received data to a file.
        # This requires a -o parameter for each --url parameter
        o = '-o "foo" ' 
        outputf[proc].write(o+'\n')
        s = '--url "https://'+args.ip_addr+'/fcgi-bin/iipsrv.fcgi?DeepZoom='+args.slide+line.rstrip()+'"'
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
    parser.add_argument ( "-s", "--slide", type=str, help="File path", default='/data/images/imaging-west/09074f6d-932b-43db-b086-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs')
    parser.add_argument ( "-t", "--tiles", type=str, help="File path", default='rand_tiles.txt')
    # Actually, as currently structured, curl requests must be to the local host because the emptyCaches()
    # function assumes that the iipsrv server is running locally
    parser.add_argument ( "-i", "--ip_addr", type=str, help="IP address of VM to test", default='localhost:5001')
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

        # Give the server a little time to get going. If we don't, the first bunch of requests
        # are rejected.
        sleep(10)

        t0 = time.time()
        measure(args)
        t1 = time.time()
        print("{} seconds".format(t1-t0),file=sys.stdout)
        totalTime += (t1-t0)

    print("Avg {} seconds".format(totalTime/args.reps),file=sys.stdout)
