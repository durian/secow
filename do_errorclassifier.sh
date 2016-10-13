#!/bin/bash
#
#
# bash do_errorclassifier.sh SECOW2012-00XS_TEXT.utf8.1000.txt cf_enett.txt 010 INSTANCES 0.05
#
#WOPR="/Users/pberck/uvt/wopr/wopr"
WOPR="/home/pberck/uvt/wopr_nt/src/wopr"
FI="filter_instances.py"
MI="make_instance_errors.py"
IC="insert_confusibles_m2.py"
#
TRAIN=$1
CFSET=$2 #cf_hanhonom.txt ("han honom")
PF=$3 # "010" index number in filename (pos filtered)
IE=$3 # "010" index number in filename (instance errors)
INSTANCES=$4
ERRPER=$5 # 0.05
#
LC=2
RC=2
E="-e"     #next two needed also
T="t1"     #added to context string
IT=",it:1" #added to wopr parameters
TIMBL="-a1 +D"

#SANITY CHECKS
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

OUT="OUTPUT_$$.txt"
echo "Output in ${OUT}"

#TRAINING DATA:
echo "WINDOWING"
#creates   ${TRAIN}.l${LC}${T}r${RC}
echo "${WOPR} -r window_lr -p lc:${LC},rc:${RC}${IT},filename:${TRAIN}"
echo "${WOPR} -r window_lr -p lc:${LC},rc:${RC}${IT},filename:${TRAIN}" &> ${OUT}
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

# Take a subset if required, else whole file.
if [[ ! $INSTANCES == "0" ]]
then
    echo "TAKE SUBSET"
    FILE="${TRAIN}.l${LC}${T}r${RC}.pf${PF}.h${INSTANCES}"
    echo " head -n${INSTANCES} ${TRAIN}.l${LC}${T}r${RC}.pf${PF} \> ${FILE}"
    echo " head -n${INSTANCES} ${TRAIN}.l${LC}${T}r${RC}.pf${PF} \> ${FILE}" >> ${OUT} 2>&1
    head -n${INSTANCES} ${TRAIN}.l${LC}${T}r${RC}.pf${PF} > ${FILE}
else
    FILE="${TRAIN}.l${LC}${T}r${RC}.pf${PF}"
fi
# We continue with ${FILE} here from here on

echo "MAKE INSTANCE ERRORS"
#creates   ${TFILE}.ie${IE}
if [ ! -e "${FILE}.ie${IE}" ]
then
    echo " python ${MI} -f ${FILE} -v ${CFSET} -c ${ERRPER} -n ${IE} -F"
    echo " python ${MI} -f ${FILE} -v ${CFSET} -c ${ERRPER} -n ${IE} -F" >> ${OUT} 2>&1
    python ${MI} -f ${FILE} -v ${CFSET} -c ${ERRPER} -n ${IE} -F >> ${OUT} 2>&1
else
    echo " EXISTS: ${FILE}.ie${IE}"
fi

echo "MAKE IBASE"
echo "${WOPR} -r make_ibase -p filename:${FILE}.ie${IE},timbl:\"${TIMBL}\""
echo "${WOPR} -r make_ibase -p filename:${FILE}.ie${IE},timbl:\"${TIMBL}\"" >> ${OUT} 2>&1
${WOPR} -r make_ibase -p filename:${FILE}.ie${IE},timbl:"${TIMBL}" >> ${OUT} 2>&1

#need to prepare tserver.ini/def ...
#tserver_001.ini:
#  port=2000
#  maxconn=32
#  ENETT_ERR="-i ${TRAIN}.l2t1r2.pf00.ie000_-a1+D.ibase -a1 +D +vdb+di"
#tserver_001.def:
#  ENETT_ERR WORDPRED 2 2 2

TS="tserver_$$.ini"
echo "tserver.ini in ${TS}"
echo "CREATING TSERVER.INI"
echo "port=2000" > ${TS}
echo "maxconn=32" >> ${TS}
echo "IBASE=\"-i ${FILE}.ie${IE}_${TIMBL// /}.ibase -a1 +D +vdb+di\"" >> ${TS}
echo "EXECUTE: timblserver --config=${TS} --daemonize=no"

TS="tserver_$$.def"
echo "tserver.def in ${TS}"
echo "IBASE WORDPRED ${LC} ${RC} 2" > ${TS}

