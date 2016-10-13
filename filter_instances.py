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
import codecs
try:
    from collections import Counter
except:
    pass

"""
Filter instances on verbs only (experts so to say)

1.90 2014-05-17 Removed posfilter/pattern stuff/logic
1.80 2014-05-16 Added swedish stuff
1.70 2014-02-26 Added -e for error data
1.60 2014-02-14 Added lc, rc
1.50 2014-02-12 Inverse option (to create PN data)
1.40 2013-01-02 Made pattern do tagging on the word _in context_. Only for l4r4 now.
1.30 2014-01-30 added hc2 for verbs in tokenised texts, both hc and pos are run now.
1.20 2013-12-23 hcfilter added (hardcoded lists).
1.10 2013-12-18 posfilter added.
1.00 2013-12-16 First version.

Examples:
Filter error data with DETS:
python filter_instances.py -f combined.cf000.l2t1r2 -e -l2 -r2 -h0
 Output file: combined.cf000.l2t1r2.pf00

python filter_instances.py -f combined.cf001.l2t1r2 -e -l2 -r2 -h1 -i 01
 Output file: combined.cf001.l2t1r2.pf01
"""

idx       = "00"
afile     =  None
cfile     =  None #confusible set ("ett en" per line)
pos       = -1 #pos of word to check
hcfilter  =  None
inverse   = False
lc        = 4
rc        = 4
eformat   = 0 #for l2t1r2
force     = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:ef:h:i:Ip:l:r:F", ["file="])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a 
    elif o in ("-c"): 
        cfile = a
    elif o in ("-i"): 
        idx = a
    elif o in ("-e"): 
        eformat = 1
    elif o in ("-p"): 
        pos = int(a)
    elif o in ("-I"): 
        inverse = True
    elif o in ("-h"): 
        hcfilter = int(a)
    elif o in ("-l"): 
        lc = int(a)
    elif o in ("-r"): 
        rc = int(a)
    elif o in ("-H"): 
        hcfilter = int(a)
    elif o in ("-F"): 
        force = True
    else:
        assert False, "unhandled option"

if not afile:
    print "Specify a filename with -f"
    sys.exit(1)

hc = [
    ["a","all","an","another","any","both","each","either","every","many","neither","no","some","that","the","these","this","those","what","whatever","which","whichever","who","A","All","An","Another","Any","Both","Each","Either","Every","Many","Neither","No","Some","That","The","These","This","Those","What","Whatever","Which","Whichever","Who"],

    ["about","above","across","after","against","along","alongside","amid","among","amongst","apart","around","as","aside","at","atop","before","behind","below","beneath","beside","besides","between","beyond","by","down","due","for","from","in","inside","into","near","next","of","off","on","onto","out","outside","over","past","per","since","though","through","throughout","till","to","toward","towards","under","unlike","until","up","upon","versus","via","vs.","whether","while","with","within","without","About","Above","Across","After","Against","Along","Alongside","Amid","Among","Amongst","Apart","Around","As","Aside","At","Atop","Before","Behind","Below","Beneath","Beside","Besides","Between","Beyond","By","Down","Due","For","From","In","Inside","Into","Near","Next","Of","Off","On","Onto","Out","Outside","Over","Past","Per","Since","Though","Through","Throughout","Till","To","Toward","Towards","Under","Unlike","Until","Up","Upon","Versus","Via","Vs.","Whether","While","With","Within","Without"],

    ["n't"], #-h2
    ["en", "ett"] #-h3
    ]
        
f_path, f_name = os.path.split(afile)
afile_outs = f_name+".pf"+idx # pos filtered
if inverse:
    afile_outs += "i"
print "Output file:", afile_outs
if not force and os.path.exists(afile_outs):
    print "FILE EXISTS, ABORTING!"
    sys.exit(3)

if cfile:
    hci = len(hc)
    with open(cfile, "r") as f:
        for line in f:
            if line == "" or line[0] == "#":
                continue
            line = line[:-1]
            words = line.split()
            hc.append(words) #put an extra "entry" at the end of the hc array
    hcfilter = hci

l = 0
with codecs.open(afile, "r", encoding="utf-8") as f:
    with codecs.open(afile_outs, "w", encoding="utf-8") as fo: #file out
        for line in f:
            line = line[:-1]
            if line == "":
                print "EMPTY LINE"
                continue
            #print line
            words = line.split()
            if len(words) != lc+eformat+rc+1:
                print "ERROR: format is wrong."
                sys.exit(4)
            if hcfilter != None:
                w = words[pos] #this is default -1, the last token in the instance
                if inverse ^ bool(w in hc[hcfilter]): #XOR
                    fo.write( line + "\n" )
                    l += 1
print "Wrote", l, "lines."

                    
