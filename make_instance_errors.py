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
Create errors in l2t1r2 type data.

2014-05-17 first version
"""

afile     = None
chance    = 0.01 #chance we change a confusible (if random < change )
n         = 0 #index nr
vkfile    = None #file with confusibles ("et ett", ...)
lc        = 2
rc        = 2
force     = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:f:l:n:r:v:F", ["file="])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a 
    elif o in ("-c"): 
        chance = float(a)
    elif o in ("-l"): 
        lc = int(a)
    elif o in ("-n"): 
        n = int(a)
    elif o in ("-r"): 
        rc = int(a)
    elif o in ("-v"): 
        vkfile = a
    elif o in ("-F"): 
        force = True
    else:
        assert False, "unhandled option"

f_path, f_name = os.path.split(afile)
afile_outs = f_name+".ie"+'{0:03n}'.format( n )    # with instance errors 
lfile_outs = f_name+".ie"+'{0:03n}.lg'.format( n ) # log file

if not force and os.path.exists(afile_outs):
    print "FILE EXISTS, ABORTING!"
    sys.exit(3)

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

with open(lfile_outs, "w") as fl:
    for c in confusibles:
        fl.write(c+":"+repr(confusibles[c])+"\n")

# pass one, count

focus_pos  = lc
target_pos = -1
possible = [] # line/instance nr
'''
blir nog ett och annat ett
tror att en person som en
'''
with open(afile, "r") as f:
    lc = 0
    for line in f:
        line  = line[:-1] #instance, l2t1r2
        words = line.split()
        focus = words[focus_pos]
        if focus in confusibles:
            h = (lc, focus) # hash
            possible.append( h )
        lc += 1

# We need this many to get correct percentage
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
with open(afile, "r") as f: #instances
    with open(afile_outs, "w") as fo: #output
        with open(lfile_outs, "a") as fl: #logfile
            lc = 0
            for line in f:
                fl.write( line )
                line = line[:-1]
                words = line.split()
                focus = words[focus_pos]
                h = (lc, focus)
                if focus in confusibles:
                    poss_changes += 1 # here is a confusible
                    if h in chosen: # which had been chosen to be changed
                        confused = random.choice( confusibles[focus] )
                        words[focus_pos] = confused # error in focus pos
                        fl.write( "CHANGE "+focus+" "+confused+"\n" )
                        try:
                            changed[ confused ] += 1
                        except KeyError:
                            changed[ confused ] = 1
                        made_changes += 1
                        chosen.remove( h )
                        fl.write( "CHANGE "+' '.join(words)+"\n" )
                fo.write(' '.join(words)+"\n") #write to output
                lc += 1

with open(lfile_outs, "a") as fl:
    for change in changed:
        fl.write("FREQ "+str(change)+" "+str(changed[change])+"\n" ) #change is xxx changed into change
    fl.write( "Left in chosen: "+str(len(chosen))+"\n" )
    fl.write( repr(chosen)+"\n" )
    fl.write( "Made "+str(made_changes)+" changes out of "+str(poss_changes)+" possible changes, "+str(float(made_changes*100.0)/float(poss_changes))+"\n" )
    fl.write( "Percentage change: "+str(float(made_changes*100.0)/float(poss_changes))+"\n" )
    fl.write( "Output in: "+afile_outs+"\n")

print "Made", made_changes, "changes out of", poss_changes, "possible changes,", float(made_changes*100.0)/float(poss_changes)
print "Percentage change:",  float(made_changes*100.0)/float(poss_changes)
print "Output in:", afile_outs
