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
WOPR=wopr
LINESP=50000000
LINESN=50000000
FILE=$1
ID=$2
#
LC=2
RC=2
TIMBL="-a1 +D"
#TSTR=l${LC}${T}r${RC}_"${TIMBL// /}"
TSTR="${TIMBL// /}"
#
echo "POSITIVE EXAMPLES"
CTX=l${LC}r${RC}
${WOPR} -l -r window_lr -p lc:${LC},rc:${RC},filename:${FILE}
echo "SAMPLEN.PY"
python samplen.py ${LINESP} ${FILE}.${CTX} > ${FILE}.${ID}.${CTX}.${LINESP}
echo "AWK"
awk '{print $1,$2,$3,$4,"+"}' < ${FILE}.${ID}.${CTX}.${LINESP} > ${FILE}.${ID}.pnP

#
echo "NEGATIVE EXAMPLES"
CTX=l${LC}t1r${RC}
${WOPR} -l -r window_lr -p lc:${LC},rc:${RC},filename:${FILE},it:1
echo "SAMPLEN.PY"
python samplen.py ${LINESN} ${FILE}.${CTX} > ${FILE}.${ID}.${CTX}.${LINESN}
echo "AWK"
awk '{print $1,$2,$3,$4,"-"}' < ${FILE}.${ID}.${CTX}.${LINESN} > ${FILE}.${ID}.pnN
#
echo "COMBINE AND MAKE INSTANCE BASE"
cat ${FILE}.${ID}.pnP ${FILE}.${ID}.pnN > ${FILE}.${ID}.PN
${WOPR} -l -r make_ibase -p timbl:"${TIMBL}",filename:${FILE}.${ID}.PN
#
echo "For tserver.ini: ${FILE}.${ID}.PN_${TSTR}.ibase"
