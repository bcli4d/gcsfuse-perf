#!/bin/bash

PROCS=$1
REPS=$2

python measure_keepalive.py -p $PROCS -r $REPS -s /data/images/svs-images/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs

python measure_keepalive.py -p $PROCS -r $REPS -s /data/images/svs-images-mr/TCGA-3X-AAVA-01Z-00-DX1.A04F5D5B-5D2B-478E-90BE-572DC5E3FAE6.svs

