#!/bin/bash
#
# 2014-06-23 Version for hoo experiments
#
# bash prepare.sh FILE ID
#  0) Window file l2r2 into "FILE.l2r2"
#  1) Take LINES random lines into "FILE.ID.WP"
#  2) Make instance base ("-a1 +D") into "FILE.ID.WP_-a1+D.ibase"
#
WOPR=wopr
LINES=50000000
FILE=$1
ID=$2
#
LC=2
RC=2
CTX=l${LC}r${RC}
TIMBL="-a1 +D"
#TSTR=l${LC}${T}r${RC}_"${TIMBL// /}"
TSTR="${TIMBL// /}"
#
echo "WINDOWING"
${WOPR} -l -r window_lr -p lc:${LC},rc:${RC},filename:${FILE}
echo "SAMPLEN.PY"
python samplen.py ${LINES} ${FILE}.${CTX} > ${FILE}.${ID}.WP
#
echo "MAKE_IBASE"
${WOPR} -l -r make_ibase -p timbl:"${TIMBL}",filename:${FILE}.${ID}.WP
#
echo "For tserver.ini: ${FILE}.${ID}.WP_${TSTR}.ibase"