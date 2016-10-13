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
!! POTENTIAL PROBLEM
!!
!! Low frequency instances could only exist in "errorenous" form
!! after this script.
!! Solve with confidence/freqs, etc?

Takes a plain text file, and inserts confusibles/errors

The error file looks like:
hun hen
de het 
in op onder naast 

python insert_confusibles2.py -v conf_nl.txt -f zin

python insert_confusibles2.py -v goldingroth3.txt -f test1  -c0.1 -n1

2014-05-16 Added balance option (doubles data size, correct ones also doubled)
2014-04-22 Bug fixes
2014-04-22 Made two pass
2014-01-07 Added expand option, logfile
...
"""
def upcase_first_letter(s):
    return s[0].upper() + s[1:]
def lower_first_letter(s):
    return s[0].lower() + s[1:]
def toggle_first_letter(s):
    if s[0].isupper():
        return lower_first_letter(s)
    return upcase_first_letter(s)

afile     = None
vkfile    = "goldenroth.txt"
skip      = 0   # errors every Nth line, 0 & 1 is in all lines
chance    = 0.5 #chance we change a confusible (if random < change )
n         = 0 #index nr
expand    = False #automatically generate Capitalized versions
balance   = 0 #balance inserted errors with the original correct form

try:
    opts, args = getopt.getopt(sys.argv[1:], "b:c:ef:v:s:n:", ["file="])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a 
    elif o in ("-b"): 
        balance = int(a)
    elif o in ("-v"): 
        vkfile = a
    elif o in ("-c"): 
        chance = float(a)
    elif o in ("-e"): 
        expand = True
    elif o in ("-s"): 
        skip = int(a)
    elif o in ("-n"): 
        n = int(a)
    else:
        assert False, "unhandled option"

f_path, f_name = os.path.split(afile)
if balance > 0:
    afile_outs = f_name+".cfb"+str(balance)+"_"+'{0:03n}'.format( n ) # with errors
    lfile_outs = f_name+".lgb"+str(balance)+"_"+'{0:03n}'.format( n ) # log file
else:
    afile_outs = f_name+".cf"+'{0:03n}'.format( n ) # with errors
    lfile_outs = f_name+".lg"+'{0:03n}'.format( n ) # log file

k = chance + 0.001 #adjust a little
vk_errors = {} # word => [ e1 e1 e2 e3 e3 e3 ]
confusibles = {}
with open(vkfile, "r") as f:
    for line in f:
        if line == "" or line[0] == "#":
            continue
        line = line[:-1]
        words = line.split()
        for w in words:
            others = [x for x in words if x != w]
            #print others
            if others:
                confusibles[w] = others
        if expand:
            words = [ toggle_first_letter(x) for x in words]
            for w in words:
                others = [x for x in words if x != w]
                #print others
                if others:
                    confusibles[w] = others

with open(lfile_outs, "w") as fl:
    for c in confusibles:
        fl.write(c+":"+repr(confusibles[c])+"\n")

# pass one, count
possible = [] #line->position
with open(afile, "r") as f:
    lc = 0
    for line in f:
        wc = 0
        line = line[:-1]
        words = line.split()
        for word in words:
            if word in confusibles:
                h = (lc, wc, word)
                possible.append( h )
                #possible.append( str(lc)+"."+str(wc) )
            wc += 1
        lc += 1

required = int((len(possible) * chance)+0.5)

with open(lfile_outs, "a") as fl:
    fl.write( "\nConfusibles in text: "+str(len(possible))+"\n" )
    fl.write( "Required changes for "+str(chance)+" is "+str(required)+" = "+str(float(required)/float(len(possible)))+"\n\n" )

print "Confusibles in text: "+str(len(possible))
print "Required changes for "+str(chance)+" is "+str(required)+" = "+str(float(required)/float(len(possible)))

r = random.Random()
chosen = []
for x in xrange(0, required):
    choice = random.choice(possible)
    while choice[2] == "I" and choice[1] == 0:
        choice = random.choice(possible)
    if not choice in chosen:
        possible.remove(choice)
        chosen.append(choice)
print "Chosen contains: "+str(len(chosen))

#chosen.sort(key=lambda tup: tup[1])
#print sorted(chosen)

# Pass two

made_changes = 0
poss_changes = 0
skipped_poss_changes = 0
changed = {}
lds = {}
skip_cnt = skip
with open(afile, "r") as f:
    with open(afile_outs, "w") as fo:
        with open(lfile_outs, "a") as fl:
            lc = 0
            for line in f:
                fl.write( line )
                line = line[:-1]
                wc = 0
                words = line.split()
                new_words = []
                for word in words:
                    #h = str(lc)+"."+str(wc)
                    h = (lc, wc, word)
                    if word in confusibles:
                        if wc != 0 or word != "I":
                            poss_changes += 1 #to get count correct
                        if h in chosen:
                            confused = random.choice( confusibles[word] )
                            new_words.append( confused )
                            fl.write( "CHANGE "+word+" "+confused+"\n" )
                            try:
                                changed[ confused ] += 1
                            except KeyError:
                                changed[ confused ] = 1
                            made_changes += 1
                            chosen.remove( h )
                        else:
                            new_words.append( word )
                    else:
                        new_words.append( word )
                    wc += 1
                new_line = ' '.join(new_words)
                fo.write(new_line+"\n")
                # Do we write the orginal line too, for balance?
                # This meses up the percentages/counts.
                if balance > 0:
                    fl.write( "Balancing\n" );
                    for i in xrange(0, balance):
                        fo.write(line+"\n")
                lc += 1

with open(lfile_outs, "a") as fl:
    for change in changed:
        fl.write("FREQ "+str(change)+" "+str(changed[change])+"\n" ) #change is xxx changed into change
    fl.write( "Left in chosen: "+str(len(chosen))+"\n" )
    fl.write( repr(chosen)+"\n" )
    fl.write( "Made "+str(made_changes)+" changes out of "+str(poss_changes)+" possible changes, "+str(float(made_changes*100.0)/float(poss_changes))+"\n" )
    fl.write( "Percentage change: "+str(float(made_changes*100.0)/float(poss_changes+skipped_poss_changes))+"\n" )
    fl.write( "Output in: "+afile_outs+"\n")

print "Made", made_changes, "changes out of", poss_changes, "possible changes,", float(made_changes*100.0)/float(poss_changes)
print "Percentage change:",  float(made_changes*100.0)/float(poss_changes+skipped_poss_changes)
print "Output in:", afile_outs
