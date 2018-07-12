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
# N processes are launched, each of which reads the tiles for which it is responsible from one of the N files. 
# The processes issue requests to the iipsrv.fcgi service on the local host. The emptyCaches() routine
# (re)starts the quip-distro docker container which, in turn, runs the iipsrv.fcgi service. The quip-distro git 
# must be cloned to the login directory for this purpose. 
#
# By default, quip-distro accesses SVS diagnostic images from gs://imaging-west-dzis. In order to test against 
# an svs file on a disk mounted at /mnt/disks, we need to modify the quip-distro hierarchy such that it doesn't 
# look for a file in gs://imaging-west-dzis and just uses the docker -v switch to map the disk onto the 
# containers internal /data/images                                                                 
# 
# https://localhost:5001/fcgi-bin/iipsrv.fcgi?DeepZoom=/data/images/imaging-west/09074f6d-932b-43db-b086-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs_files/0/0_0.jpeg
# https://localhost:5001/fcgi-bin/iipsrv.fcgi?DeepZoom=/data/images/filestore/09074f6d-932b-43db-b086-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs_files/0/0_0.jpeg
# https://storage.googleapis.com/imaging-west-dzis/00036070-24af-40c2-9d29-5f67355e7b7b/TCGA-49-AARO-01Z-00-DX1.FB8C82DC-F823-43CF-A8EA-1208C767AF54_files/0/0_0.jpeg
# https://storage.googleapis.com/imaging-west-dzis/00036070-24af-40c2-9d29-5f67355e7b7b/TCGA-49-AARO-01Z-00-DX1.FB8C82DC-F823-43CF-A8EA-1208C767AF54_files/17/217_162.jpeg

GCSFUSE=0
FP=1
DZI=2

def emptyCaches():
    # The following presumes that quip-distro is installed locally.
    os.system('/etc/rc.local')

def readTiles(args, proc, sema):
    subprocess.call(['/usr/bin/curl', '-k', '-K', '/home/cvproc/gcsfuse-perf/urls0'])
#    subprocess.call(['/usr/bin/curl', '-k', '-H','Cache-Control: max-age=1','-K', '/home/cvproc/gcsfuse-perf/urls0'])
    sema.release()

def genBody(args):
    if args.mode == 'gf':
        body = '"https://localhost:5001/fcgi-bin/iipsrv.fcgi?DeepZoom=/data/images/imaging-west/' + args.slide + '.svs_files/'
    elif args.mode == 'fs':
        body = '"https://localhost:5001/fcgi-bin/iipsrv.fcgi?DeepZoom=/data/images/filestore/' + args.slide + '.svs_files/'
    else :
        body = '"https://storage.googleapis.com/imaging-west-dzis/' + args.slide + '_files/'
    return body

def genUrls(args, body):
    inputf = file(args.tiles,'r')
    outputf = []
    # Open a url out file for each process
    for proc in range(args.procs) :
        outputf.append(file("urls"+str(proc),'w'))
    proc = 0;
    
#    # Create a unique string that will prevent the web server from finding previous data in its cache
#    uniq= "?" + str(time.time())
    uniq=''

    for line in inputf:
        # Instead of sending all of stdout to /dev/null, we have curl write received data to a file.
        # This requires a -o parameter for each --url parameter
#        o = '-o "/dev/null" ' 
        o = '-o "sink" ' 
        outputf[proc].write(o+'\n')
#        s = '--url "https://'+args.ip_addr+'/fcgi-bin/iipsrv.fcgi?DeepZoom='+args.slide+line.rstrip()+'"'

        tile = line.rstrip().rsplit('.',1)[0]
        if args.mode == 'dz':
#            s = '--url ' + body + line.rstrip().rsplit('.',1)[0] + '.jpeg' + '"'
            s = '--url ' + body + tile + '.jpeg' + uniq + '"'

        else:
            s = '--url ' + body + tile + '.jpg' + uniq + '"'

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
    parser.add_argument ( "-m", "--mode", choices=['gf','fs','dz'], default='gf', help="One of gf,fs,dz" )
#    parser.add_argument ( "-s", "--slide", type=str, help="Slide ID", default='/data/images/imaging-west/09074f6d-932b-43db-b0#86-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs')
    parser.add_argument ( "-s", "--slide", type=str, help="Slide ID", default='09074f6d-932b-43db-b086-601533ba40a0/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6')
    parser.add_argument ( "-t", "--tiles", type=str, help="List of tile x,y offsets", default='rand_tiles.txt')
    # Actually, as currently structured, curl requests must be to the local host because the emptyCaches()
    # function assumes that the iipsrv server is running locally
    parser.add_argument ( "-i", "--ip_addr", type=str, help="IP address of VM to test", default='localhost:5001')
    parser.add_argument ( "-p", "--procs", type=int, help="Number of processes", default=1)
    parser.add_argument ( "-r", "--reps", type=int, help="Number of repetitions to perform", default=1)
    parser.add_argument ( "-f", "--flush", type=int, help="Flush cache before running", default=1)

    return(parser.parse_args())

if __name__ == '__main__':
    args=parseargs()
    print(args)

    body = genBody(args)
    
    genUrls(args, body)
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
