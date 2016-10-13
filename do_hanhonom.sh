#!/bin/bash
#
#WOPR="/Users/pberck/uvt/wopr/wopr"
WOPR="/home/pberck/uvt/wopr_nt/src/wopr"
FI="filter_instances.py"
MI="make_instance_errors.py"
IC="insert_confusibles_m2.py"

TRAIN="SECOW2012-00XS_TEXT.out.txt.10e6"
#TRAIN="SECOW2012-00XS_TEXT.utf8.1000.txt"

TEST="SECOW2012-01XS_TEXT.out.txt.1e3"

LC=2
RC=2
E="-e"     #next two needed also
T="t1"     #added to context string
IT=",it:1" #added to wopr parameters
#
PF="010"               #index number in filename (pos filtered)
IE="010"               #index number in filename (instance errors)
CFSET="cf_hanhonom.txt"
ERRPER=0.05            #errors in training data
TIMBL="-a1 +D"
#
# Test data settings
TCFSET="hanhonom.txt" 
TERRPER=0.1            #errors in test data
CC="010"               #index number in filename

#SANITY CHECK
if [ ! -e "${WOPR}" ]
then
    echo "ERROR: wopr not found."
    exit 1
fi
if [ ! -e "${FI}" ]
then
    echo "ERROR: ${FI} not found."
    exit 1
fi
if [ ! -e "${MI}" ]
then
    echo "ERROR: ${MI} not found."
    exit 1
fi
if [ ! -e "${IC}" ]
then
    echo "ERROR: ${IC} not found."
    exit 1
fi
if [ ! -e "${TRAIN}" ]
then
    echo "ERROR: Training file not found."
    exit 1
fi
if [ ! -e "${TEST}" ]
then
    echo "ERROR: Test file not found."
    exit 1
fi

OUT="OUTPUT_$$.txt"
echo "Output in ${OUT}"

#TRAINING DATA:
echo "WINDOWING"
#creates   ${TRAIN}.l${LC}${T}r${RC}
echo "${WOPR} -r window_lr -p lc:${LC},rc:${RC}${IT},filename:${TRAIN}"
echo "${WOPR} -r window_lr -p lc:${LC},rc:${RC}${IT},filename:${TRAIN}"  &> ${OUT}
${WOPR} -r window_lr -p lc:${LC},rc:${RC}${IT},filename:${TRAIN} >> ${OUT} 2>&1

echo "FILTER INSTANCES"
#creates   ${TRAIN}.l${LC}${T}r${RC}.pf${PF}
if [ ! -e "${TRAIN}.l${LC}${T}r${RC}.pf${PF}" ]
then
    echo " python ${FI} -f ${TRAIN}.l${LC}${T}r${RC} -l${LC} -r${RC} -c ${CFSET} ${E} -i${PF} -F"
    echo " python ${FI} -f ${TRAIN}.l${LC}${T}r${RC} -l${LC} -r${RC} -c ${CFSET} ${E} -i${PF} -F" >> ${OUT} 2>&1
    python ${FI} -f ${TRAIN}.l${LC}${T}r${RC} -l${LC} -r${RC} -c ${CFSET} ${E} -i${PF} -F >> ${OUT} 2>&1
else
    echo " EXISTS: ${TRAIN}.l${LC}${T}r${RC}.pf${PF}"
fi

echo "MAKE INSTANCE ERRORS"
#creates   ${TRAIN}.l${LC}${T}r${RC}.pf${PF}.ie${IE}
if [ ! -e "${TRAIN}.l${LC}${T}r${RC}.pf${PF}.ie${IE}" ]
then
    echo " python ${MI} -f ${TRAIN}.l${LC}${T}r${RC}.pf${PF} -v ${CFSET} -c ${ERRPER} -n ${IE} -F"
    echo " python ${MI} -f ${TRAIN}.l${LC}${T}r${RC}.pf${PF} -v ${CFSET} -c ${ERRPER} -n ${IE} -F" >> ${OUT} 2>&1
    python ${MI} -f ${TRAIN}.l${LC}${T}r${RC}.pf${PF} -v ${CFSET} -c ${ERRPER} -n ${IE} -F >> ${OUT} 2>&1
else
    echo " EXISTS: ${TRAIN}.l${LC}${T}r${RC}.pf${PF}.ie${IE}"
fi

echo "MAKE IBASE"
echo "${WOPR} -r make_ibase -p filename:${TRAIN}.l${LC}${T}r${RC}.pf${PF}.ie${IE},timbl:\"${TIMBL}\""
echo "${WOPR} -r make_ibase -p filename:${TRAIN}.l${LC}${T}r${RC}.pf${PF}.ie${IE},timbl:\"${TIMBL}\"" >> ${OUT} 2>&1
${WOPR} -r make_ibase -p filename:${TRAIN}.l${LC}${T}r${RC}.pf${PF}.ie${IE},timbl:"${TIMBL}" >> ${OUT} 2>&1

#need to prepare tserver.ini/def ...
#tserver_001.ini:
#  port=2000
#  maxconn=32
#  ENETT_ERR="-i ${TRAIN}.l2t1r2.pf00.ie000_-a1+D.ibase -a1 +D +vdb+di"
#tserver_001.def:
#  ENETT_ERR WORDPRED 2 2 2
echo "The following must be added to the timblserver config:"
echo "IBASE=\"-i ${TRAIN}.l${LC}${T}r${RC}.pf${PF}.ie${IE}_${TIMBL// /}.ibase -a1 +D +vdb+di\""
echo "NAME NAME ${LC} ${RC} 2" #for error type

#TESTING DATA:
echo "TESTING DATA"
#creates   ${TEST}.cc${CC} and ${TEST}.cc${CC}.m2
echo "python ${IC} -f ${TEST} -c ${TCFSET} -p ${TERRPER} -n ${CC}"
echo "python ${IC} -f ${TEST} -c ${TCFSET} -p ${TERRPER} -n ${CC}" >> ${OUT} 2>&1
python ${IC} -f ${TEST} -c ${TCFSET} -p ${TERRPER} -n ${CC} >> ${OUT} 2>&1

#SECOW2012-01XS_TEXT.out.txt.1e3.cc000.m2
