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

def upcase_first_letter(s):
    return s[0].upper() + s[1:]
def lower_first_letter(s):
    return s[0].lower() + s[1:]
def toggle_first_letter(s):
    if s[0].isupper():
        return lower_first_letter(s)
    return upcase_first_letter(s)

"""
2014-05-01 Changed formatting to three digits in output file numbering

EXAMPLE:
Takes a plain text file, and inserts confusibles/errors,
generates an m2 scoring file on the side.

python insert_confusibles_m2.py -f utexas.10e6.dt3.ucto.t1000 -c preps_for_icm2.txt

cfile:
ArtOrDet REP:2,DEL:1 a an,...
"""

afile      =  None
cfile      = None
skip       =  0   # errors every Nth line, 0 & 1 is in all lines
default_p  =  0.5 #chance we take another from the confusible set
classname  = None
n          = 0
    
try:
    opts, args = getopt.getopt(sys.argv[1:], "c:C:f:n:p:s:", ["file="])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a 
    elif o in ("-c"): 
        cfile = a
    elif o in ("-C"): 
        classname = a #ArtOrDet, ...
    elif o in ("-p"): 
        default_p = float(a)
    elif o in ("-s"): 
        skip = int(a)
    elif o in ("-n"): 
        n = int(a)
    else:
        assert False, "unhandled option"

f_path, f_name = os.path.split(afile)
afile_outs = f_name+".cc"+'{0:03n}'.format( n ) # with errors # id_str = '{0:03n}'.format( idx )
m2file = afile_outs+".m2"

confusibles = {}
operations = {} #maps confusible to possible operations, INS, REP etc
with open(cfile, "r") as f:
    for line in f:
        if line == "" or line[0] == "#":
            continue
        line = line[:-1]
        words = line.split()
        classname = words[0] #as used in the m2 file ("ArtOrDet", etc)
        opsf = words[1].split(",") # REP:6,INS:4 (60% replacements, 40% inserts)
        ops = []
        for opf in opsf:
            (op,f) = opf.split(":") #REP:10 -> (REP 10)
            ops += [op] * int(f)
        words2 = [] #[ toggle_first_letter(w) for w in words[2:]]
        #print classname, repr(words[2:]+words2)
        for c in words[2:]+words2:
            confusibles[c] = classname
            operations[c] = ops #"expanded" REP:3,INS:1,DEL:2 operations [REP REP REP INS DEL DEL]
#print repr(confusibles.keys())
##print repr(confusibles)
#print random.choice(confusibles.items())

# Pass one, count confusibles in data, make hash
#possible = [] #line->position
#with open(afile, "r") as f:
#    lc = 0
#    for line in f:
#        wc = 0
#        line = line[:-1]
#        words = line.split()
#        for word in words:
#            if word in confusibles:
#                h = (lc, wc, word)
#                possible.append( h )
#            wc += 1
#        lc += 1

r = random.Random()
made_changes = 0
poss_changes = 0
skipped_poss_changes = 0
changed = {}
skip_cnt = skip
"""
INS insert one, creates an unnecessary/redundant word
DEL delete one, missing
REP replace one
"""
ops = ["INS"]*2 + ["DEL"]*49 + ["REP"]*49 #INS often rubbish, we take a random one te determine op.
counts = {}
for op in ops:
    counts[op] = []

grand_total = 0
with open(afile, "r") as f:
    with open(afile_outs, "w") as fo:
        with open(m2file, "w") as fo_m2:
            for line in f:
                #print line[:-1]
                line = line[:-1]
                words = line.split()
                indexes = [] #list of index->word which we can errorify
                idx = 0
                for word in words:
                    if word in confusibles:
                        grand_total += 1
                        chance = random.random()
                        #print confusibles[word], chance, operations[word]
                        if chance < default_p:
                            indexes.append(idx)
                            poss_changes += 1
                    idx += 1
                """
                Now choose an position, operation, apply, write file/m2file
                Difficult to get exact numbers...
                """
                pos = 0
                op = "NOP"
                if indexes:
                    pos = random.choice(indexes)
                    the_word = words[pos]
                    the_ops = operations[the_word]
                    op = random.choice(the_ops) #it is double random, maybe only use ops from confusibles. why choose here?
                    #print pos, the_word, [ (i,the_ops.count(i)) for i in set(the_ops) ], op
                astr = ""
                if op == "DEL" and pos > 1:
                    #A 15 16|||ArtOrDet||||||REQUIRED|||-NONE-|||0
                    astr = "A "+str(pos-1)+" "+str(pos)+"|||"+classname+"|||"+words[pos-1]+" "+words[pos]+"|||REQUIRED|||-NONE-|||0"
                    counts[op].append(words[pos])
                    words[pos] = ""
                    made_changes += 1
                if op == "REP" and pos > 0:
                    items = [ (x,y) for (x,y) in confusibles.items() if x != words[pos] ] #don't choose me
                    (alt, classname) = random.choice(items)
                    alt = alt.lower() #because pos > 0
                    if words[pos] != alt:
                        #A 4 5|||ArtOrDet|||the|||REQUIRED|||-NONE-|||0
                        astr = "A "+str(pos)+" "+str(pos+1)+"|||"+classname+"|||"+words[pos]+"|||REQUIRED|||-NONE-|||0"
                        counts[op].append( words[pos]+"/"+alt )
                        words[pos] = alt
                        made_changes += 1
                if op == "INS":
                    if len(words) > 2:
                        pos = random.randint(0, len(words)-2)
                        (alt, classname) = random.choice(confusibles.items())
                        alt = alt.lower()
                        # A 24 25|||Wci|||drawing near|||REQUIRED|||-NONE-|||0
                        astr = "A "+str(pos+1)+" "+str(pos+2)+"|||"+classname+"||||||REQUIRED|||-NONE-|||0"
                        words[pos] = words[pos]+" "+alt
                        counts[op].append(alt)
                        made_changes += 1
                words_str = " ".join(words)
                words = words_str.split() #get rid of double spaces etc.
                fo.write( " ".join(words)+"\n" )
                fo_m2.write( "S "+" ".join(words)+"\n" )
                if astr:
                    fo_m2.write( astr+"\n" )
                fo_m2.write( "\n" )
                    
print "Made", made_changes, "changes out of", poss_changes, "possible changes, grand total =", grand_total
print "Skipped", skipped_poss_changes, " possible changes in the skipped lines."
print "Percentage", made_changes/float(grand_total)
for op in counts:
    print op, len(counts[op])
print "Output in", afile_outs, "and", m2file
