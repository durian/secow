#!/usr/bin/python
# -*- coding: utf-8 -*-
#
import getopt
import sys
import time
import os
import datetime
import random
import re
import platform
from operator import itemgetter
import operator
try:
    from collections import Counter
except:
    pass

"""
20140619 Also count edits

Counts corrected types (ins/del/replace)

CORRECT EDITS : [(5, 5, '', u'with')]
CORRECT EDITS : [(30, 30, '', u'the'), (15, 15, '', u'the'), (7, 7, '', u'the')]
CORRECT EDITS : [(15, 15, '', u'the')]

"""

afile      =  None #the .score file, output from the m2scorer
    
try:
    opts, args = getopt.getopt(sys.argv[1:], "f:", ["file="])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a 
    else:
        assert False, "unhandled option"

'''
EDIT SEQ      : [(16, 17, u'whatever', u'the'), (7, 9, u'Encyclopedia of', u'Encyclopedia of the'), (1, 4, u'recently was an', u'recently was')]
GOLD EDITS    : [(16, 17, u'whatever', [u'the'])]
CORRECT EDITS : [(16, 17, u'whatever', u'the')]
'''

# Count only these
annotations = ["Prep", "ArtOrDet"]
stats = {}
gold_stats = {}
edit_stats = {}
with open(afile, "r") as f:
    for line in f:
        line = line[:-1]
        if line[0:8] == "EDIT SEQ":
            print line
            #EDIT SEQ      : [(19, 22, u'direct contact between', u'direct contact with any')]
            if line == "EDIT SEQ      : []":
                continue
            m = re.match( "EDIT SEQ      : (\[.*\])", line)
            if m:
                # get scores like in CORRECT, seems same format
                edits_str = str(m.group(1))
                #print "-->"+edits_str+"<--"
                if edits_str and len(edits_str) > 4:
                    edits = eval( edits_str )
                    typ = "NOP"
                    for edit in edits:
                        #print edit
                        pos0 = edit[0]
                        pos1 = edit[1]
                        lpos = pos1-pos0
                        orig = edit[2]
                        dest = ""
                        try:
                            dest = edit[3]
                        except IndexError:
                            dest = ""
                        ldest = len(dest.split())
                        if ldest > lpos or lpos == 0:
                            print edit, "CORR INS", lpos, ldest
                            typ = "INS"
                        elif lpos > ldest or (orig != '' and ldest == 0):
                            print edit, "CORR DEL", lpos, ldest
                            typ = "DEL"
                        else:
                            print edit, "CORR REP", lpos, ldest
                            typ = "REP"
                        try:
                            edit_stats[typ] += 1
                        except KeyError:
                            edit_stats[typ] = 1
            else:
                #print "2"
                pass
        if line[0:13] == "CORRECT EDITS":
            #print line
            #CORRECT EDITS : [(5, 5, '', u'with')]
            if line == "CORRECT EDITS : []":
                continue
            m = re.search( "CORRECT EDITS : (\[.*\])", line)
            if m:
                #print repr(m)
                # danger danger
                edits_str = str(m.group(1))
                #print "-->"+edits_str+"<--"
                if edits_str and len(edits_str) > 4:
                    edits = eval( edits_str )
                    typ = "NOP"
                    for edit in edits:
                        pos0 = edit[0]
                        pos1 = edit[1]
                        lpos = pos1-pos0
                        orig = edit[2]
                        dest = ""
                        try:
                            dest = edit[3]#[0]
                        except IndexError:
                            dest = ""
                        ldest = len(dest.split())
                        if ldest > lpos or lpos == 0:
                            print edit, "CORR INS", lpos, ldest
                            typ = "INS"
                        elif lpos > ldest or (orig != '' and ldest == 0):
                            print edit, "CORR DEL", lpos, ldest
                            typ = "DEL"
                        else:
                            print edit, "CORR REP", lpos, ldest
                            typ = "REP"
                        try:
                            stats[typ] += 1
                        except KeyError:
                            stats[typ] = 1
        if line[0:10] == "GOLD EDITS":
            if line == "GOLD EDITS    : []":
                continue
            m = re.search( "GOLD EDITS    : (\[.*\])", line)
            if m:
                edits_str = str(m.group(1))
                if edits_str and len(edits_str) > 4:
                    edits = eval( edits_str )
                    typ = "NOP"
                    for edit in edits:
                        pos0 = edit[0]
                        pos1 = edit[1]
                        lpos = pos1-pos0
                        orig = edit[2]
                        dest = edit[3][0] #is list, alwys one element?
                        ldest = len(dest.split())
                        if ldest > lpos or lpos == 0:
                            print edit, "GOLD INS", lpos, ldest
                            typ = "INS"
                        elif lpos > ldest or (orig != '' and ldest == 0):
                            print edit, "GOLD DEL", lpos, ldest
                            typ = "DEL"
                        else:
                            print edit, "GOLD REP", lpos, ldest
                            typ = "REP"
                        try:
                            gold_stats[typ] += 1
                        except KeyError:
                            gold_stats[typ] = 1
print "Gold", gold_stats
print "Corr", stats
print "Edit", edit_stats
