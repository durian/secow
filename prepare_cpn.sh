#!/bin/bash
#
#awk -F"," '{print $2}' test_v2.txt | awk '{print substr($0, 2, length($0) - 2)}'
#
# 2014-06-23 Version for hoo experiments
#
# bash prepare_pn.sh FILE ID
#  0) Window file l2t1r2 into "FILE.l2t1r2", create +ve and -ve examples
#  1) Take LINES random lines from both +ve and -ve
#  2) Combine, and make instance base ("-a1 +D") into "FILE.ID.WP_-a1+D.ibase"
#
# For one category (PREP), add the filter_instances.py? Or just use pf00 data as input?
#  python filter_instances.py -f combined.cf000.l2t1r2 -e -l2 -r2 -h0
#  Output file: combined.cf000.l2t1r2.pf00
#  -h0 = DETS
#  -h1 = PREPS
#
#WOPR=/home/pberck/uvt/wopr_nt/src/wopr
WOPR=wopr
#LINESP=50000000
#LINESN=50000000
FILE=$1
ID=$2
CAT=$3
LINESP=$4
LINESN=$5
#
LC=2
RC=2
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
echo "POSITIVE EXAMPLES, WINDOWING"
CTXP=l${LC}r${RC}
${WOPR} -l -r window_lr -p lc:${LC},rc:${RC},filename:${FILE} #gives ${FILE}.${CTX}
#
echo "FILTER INSTANCES ON CAT"
python filter_instances.py -f${FILE}.${CTXP} -l${LC} -r${RC} -${CAT} -i ${CID}   #gives ${FILE}.${CTX}.pf${CID}
echo "RANDOM SELECTION, SAMPLEN.PY"  #          gives ${FILE}.${CTXP}.${ID}.pf${CID}
if [ ! -e "${FILE}.${CTXP}.${ID}.pf${CID}" ]
then
    python samplen.py ${LINESP} ${FILE}.${CTXP}.pf${CID} > ${FILE}.${CTXP}.${ID}.pf${CID}
else
    echo "EXISTS: ${FILE}.${CTXP}.${ID}.pf${CID}"
fi
#
echo "AWK 1,2,3,4,+"
if [ ! -e "${FILE}.${CTXP}.${ID}.pf${CID}.pnP" ]
then
    awk '{print $1,$2,$3,$4,"+"}' < ${FILE}.${CTXP}.${ID}.pf${CID} > ${FILE}.${CTXP}.${ID}.pf${CID}.pnP
else
    echo "EXISTS: ${FILE}.${CTXP}.${ID}.pf${CID}.pnP"
fi
#
#
echo "NEGATIVE EXAMPLES, WINDOWING"
CTXN=l${LC}t1r${RC}
${WOPR} -l -r window_lr -p lc:${LC},rc:${RC},filename:${FILE},it:1 #gives ${FILE}.${CTX}
#
echo "FILTER (INVERSE) INSTANCES ON CAT"
python filter_instances.py -f${FILE}.${CTXN} -e -l${LC} -r${RC} -${CAT} -i ${CID}    #gives ${FILE}.${CTX}.pf${CID}i
#
echo "RANDOM SELECTION, SAMPLEN.PY"              # v--> inverse file has "i" appended
if [ ! -e "${FILE}.${CTXN}.${ID}.pf${CID}" ]
then
    python samplen.py ${LINESN} ${FILE}.${CTXN}.pf${CID}i > ${FILE}.${CTXN}.${ID}.pf${CID}
else
    echo "EXISTS: ${FILE}.${CTXN}.${ID}.pf${CID}"
fi
#
echo "AWK 1,2,3,4,-"
if [ ! -e "${FILE}.${CTXN}.${ID}.pf${CID}.pnN" ]
then
    awk '{print $1,$2,$3,$4,"-"}' <  ${FILE}.${CTXN}.${ID}.pf${CID} > ${FILE}.${CTXN}.${ID}.pf${CID}.pnN
else
    echo "EXISTS:  ${FILE}.${CTXN}.${ID}.pf${CID}.pnN"
fi
#
echo "COMBINE POS/NEG AND MAKE INSTANCE BASE"
if [ ! -e " ${FILE}.${CTXP}.${ID}.pf${CID}.PN" ]
then
    cat ${FILE}.${CTXP}.${ID}.pf${CID}.pnP ${FILE}.${CTXN}.${ID}.pf${CID}.pnN > ${FILE}.${CTXP}.${ID}.pf${CID}.PN
else
    echo "EXISTS:  ${FILE}.${CTXP}.${ID}.pf${CID}.PN"
fi
${WOPR} -l -r make_ibase -p timbl:"${TIMBL}",filename:${FILE}.${CTXP}.${ID}.pf${CID}.PN
#
echo "For tserver.ini: ${FILE}.${CTXP}.${ID}.pf${CID}.PN_${TSTR}.ibase"
