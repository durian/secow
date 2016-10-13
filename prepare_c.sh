#!/bin/bash
#
# 2014-06-23 Version for hoo experiments
#
# bash prepare.sh FILE ID
#  0) Window file l2r2 into "FILE.l2r2"
#  1) Take LINES random lines into "FILE.ID.WP"
#  2) Make instance base ("-a1 +D") into "FILE.ID.WP_-a1+D.ibase"
#
# Example:
# bash prepare_c.sh utexas.10e6.dt3.ucto TEXAS1 h0 100000000
#
WOPR=wopr
#WOPR=/home/pberck/uvt/wopr_nt/src/wopr
#LINES=50000000
FILE=$1
ID=$2
CAT=$3
LINES=$4
#
LC=2
RC=2
CTX=l${LC}r${RC}
TIMBL="-a1 +D"
#TSTR=l${LC}${T}r${RC}_"${TIMBL// /}"
TSTR="${TIMBL// /}"
#CAT="h0" #"h0" is DETS, "h1" is PREPS
CID="DETS"
if [[ $CAT == "h1" ]]
then
    CID="PREPS"
fi
#
echo "WINDOWING"
${WOPR} -l -r window_lr -p lc:${LC},rc:${RC},filename:${FILE}  #gives ${FILE}.${CTX}
echo "FILTER (INVERSE) INSTANCES ON CAT"
python filter_instances.py -f${FILE}.${CTX} -l${LC} -r${RC} -${CAT} -i ${CID}
echo "RANDOM SELECTION, SAMPLEN.PY"  #gives ${FILE}.${CTX}.${ID}.pf${CID}.P
if [ ! -e "${FILE}.${CTX}.${ID}.pf${CID}.P" ]
then
    python samplen.py ${LINES} ${FILE}.${CTX}.pf${CID} > ${FILE}.${CTX}.${ID}.pf${CID}.P
else
    echo "EXISTS: ${FILE}.${CTX}.${ID}.pf${CID}.P"
fi
#
echo "MAKE_IBASE"
${WOPR} -l -r make_ibase -p timbl:"${TIMBL}",filename:${FILE}.${CTX}.${ID}.pf${CID}.P
#
echo "For tserver.ini: ${FILE}.${CTX}.${ID}.pf${CID}.P_${TSTR}.ibase"