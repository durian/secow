#!/bin/bash
#
# 2014-06-23 Version for hoo experiments
# 2014-07-13 Added -v option
#
# bash prepare.sh FILE ID CF LINES
#  0) Window file l2r2 into "FILE.l2r2"
#  1) Take LINES random lines into "FILE.ID.WP"
#  2) Make instance base ("-a1 +D") into "FILE.ID.WP_-a1+D.ibase"
#
# Example:
# bash prepare_c.sh utexas.10e6.dt3.ucto TEXAS1 h0 100000000
#
WOPR="/home/pberck/uvt/wopr_nt/src/wopr"
#LINES=50000000
FILE=$1
ID=$2
CAT=$3  #now a file
LINES=$4
#
LC=2
RC=2
CTX=l${LC}r${RC}
TIMBL="-a1 +D"
#TSTR=l${LC}${T}r${RC}_"${TIMBL// /}"
TSTR="${TIMBL// /}"
PF="010"
#
echo "WINDOWING"
${WOPR} -l -r window_lr -p lc:${LC},rc:${RC},filename:${FILE}  #gives ${FILE}.${CTX}
echo "FILTER INSTANCES ON CAT"
python filter_instances.py -f${FILE}.${CTX} -l${LC} -r${RC} -${CAT} -i ${PF} -c ${CAT}
echo "RANDOM SELECTION, SAMPLEN.PY"  #gives ${FILE}.${CTX}.${ID}.pf${PF}.P
if [ ! -e "${FILE}.${CTX}.${ID}.pf${PF}.P" ]
then
    python samplen.py ${LINES} ${FILE}.${CTX}.pf${PF} > ${FILE}.${CTX}.${ID}.pf${PF}.P
else
    echo "EXISTS: ${FILE}.${CTX}.${ID}.pf${PF}.P"
fi
#
echo "MAKE_IBASE"
${WOPR} -l -r make_ibase -p timbl:"${TIMBL}",filename:${FILE}.${CTX}.${ID}.pf${PF}.P
#
echo "For tserver.ini: ${FILE}.${CTX}.${ID}.pf${PF}.P_${TSTR}.ibase"

TS="tserver_$$.ini"
echo "tserver.ini in ${TS}"
echo "CREATING TSERVER.INI"
echo "port=2000" > ${TS}
echo "maxconn=32" >> ${TS}
echo "IBASE=\"-i ${FILE}.${CTX}.${ID}.pf${PF}.P_${TSTR}.ibase -a1 +D +vdb+di\"" >> ${TS}
echo "EXECUTE: timblserver --config=${TS} --daemonize=no"

TS="tserver_$$.def"
echo "tserver.def in ${TS}"
echo "IBASE WORDPRED ${LC} ${RC} 0" > ${TS}
