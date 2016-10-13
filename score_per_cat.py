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

"""
Get a better idea of which categorier get corrected or not.

official-preprocessed.5types.m2.txt_run000.sc.score:

-------------------------------------------
>> Chosen Annotator for line 19 : 0

>> Annotator: 0
SOURCE        : After finding and analyzing the black box of the Valujet after t
he incidence , police investigators found out reasons for causing this severe in
cidence .
HYPOTHESIS    : In this and that the black women in the decades , prosecutors ,
the user found that in some the world .
EDIT SEQ      : [(18, 25, u'reasons for causing this severe incidence .', u'that
 in some the world .'), (17, 18, u'out', ''), (6, 16, u'box of the Valujet after
 the incidence , police investigators', u'women in the decades , prosecutors , t
he user'), (0, 5, u'After finding and analyzing the', u'In this and that the')]
GOLD EDITS    : [(17, 18, u'out', [u'']), (18, 18, '', [u'the']), (20, 21, u'cau
sing', [u'caused'])]
CORRECT EDITS : [(17, 18, u'out', '')]
# correct     : 1
# proposed    : 51
# gold        : 26
precision     : 0.0196078431373
recall        : 0.0384615384615
f1            : 0.025974025974
-------------------------------------------

official-preprocessed.5types.m2

S After finding and analyzing the black box of the Valujet after the incidence ,
 police investigators found out reasons for causing this severe incidence .
A 17 18|||Prep||||||REQUIRED|||-NONE-|||0
A 18 18|||ArtOrDet|||the|||REQUIRED|||-NONE-|||0
A 20 21|||Vform|||caused|||REQUIRED|||-NONE-|||0

"""

cfile = None #corrected file
mfile = None #m2 file
verbose = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "c:m:v", [])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)
for o, a in opts:
    if o in ("-c"):
        cfile = a 
    elif o in ("-m"):
        mfile = a
    elif o in ("-v"):
        verbose = True
    else:
        assert False, "unhandled option"

"""
First read and store the m2 file
"""

lcount = 0
m2annos = [] # [line] -> [ [start, end, typ, ...], ... ]
m2stats = {}
words = []
sumerrs = 0
with open(mfile, "r") as f:
    annos = []
    for line in f:
        l = line[:-1]
        if l[0:2] == "S ":
            words = l[2:].split()
            if not cfile:
                if verbose:
                    print "\n",l[2:]
                    print words
            next
        elif l[0:2] == "A ": #A 20 21|||Vform|||caused|||RE ...
            m = re.match( "A (\d+) (\d+)\|\|\|(.*?)\|\|\|(.*?)\|\|\|(.*)", l)
            # all end with "|||REQUIRED|||-NONE-|||0"
            #m = re.match( "A (\d+) (\d+)\|\|\|(.*?)\|\|\|(.*?)\|\|\|REQUIRED\|\|\|\-NONE\-\|\|\|0", l)
            if m:
                s = int(m.group(1))
                e = int(m.group(2))
                t = m.group(3)
                r = m.group(4)
                n = re.match( "\|\|", r)
                if n:
                    print l #multiple corrections.
                    sys.exit(1)
                r_words = r.split()
                snippet = words[s:e]
                if verbose and False:
                    print lcount, s,e,t
                if not cfile:
                    cp = e-s #nuber of changed positions
                    rp = len(r_words)
                    a = "REP"# +str(cp)+str(rp)
                    if cp == 0 and rp == 0:
                        pass #strange ones...
                    if cp == 0 and rp != 0:
                        a = "INS" #+str(rp)
                    if rp == 0 and cp != 0:
                        a = "DEL" #+str(cp)
                    a += str(cp)+str(rp)
                    print s,e,a,t,"'"+"_".join(snippet)+"'","=>","'"+r.replace(' ','_')+"'"
                annos.append( [s,e,t] )
                sumerrs += 1
                if t in m2stats:
                    m2stats[t] += 1
                else:
                    m2stats[t] = 1
        else:
            m2annos.append([lcount, annos] )
            annos = []
            lcount +=1
if not cfile:
    print sumerrs

"""            
for l,a in m2annos:
    print l, a
"""
if not cfile:
    sys.exit(0)

stats = {}
with open(cfile, "r") as f:
    in_edit = False
    linenr = 0
    for line in f:
        l = line[:-1]
        if l[0:6] == "SOURCE":
            in_edit = True
        elif l[0:10] == "HYPOTHESIS":
            pass
        elif l[0:8] == "EDIT SEQ":
            pass
        elif l[0:10] == "GOLD EDITS":
            pass
        elif l[0:13] == "CORRECT EDITS": #CORRECT EDITS : [(11, 12, u'does', u'do'), (8, 9, u'is', u'are')]
            if in_edit:
                edits_str = l[16:]
                edits = eval(edits_str)
                try:
                    goldline, gold_annos = m2annos[linenr]
                except:
                    print "ERROR",linenr
                for es, ee, e0, e1 in edits:
                    for anno in gold_annos:
                        if anno[0] == es and anno[1] == ee: #not efficient, but meh
                            if verbose:
                                print linenr, es, ee, anno[2], anno, repr(e0), repr(e1)
                            t = anno[2]
                            if t in stats:
                                stats[t] += 1
                            else:
                                stats[t] = 1
        elif l[0:19] == ">> Chosen Annotator":
            in_edit = False
            linenr += 1

print "Gold", repr(m2stats)
print "Corr", repr(stats)
for m2s in m2stats:
    #print m2s, m2stats[m2s], 
    out = '{0:<10} {1:5n} '.format(m2s, m2stats[m2s])
    if m2s in stats:
        #print  stats[m2s], stats[m2s]*100.0/m2stats[m2s]
        out += '{0:5n} {1:5.2f}'.format(stats[m2s], stats[m2s]*100.0/m2stats[m2s])
    else:
        #print 0, 0
        out += '{0:5n} {1:5n}'.format(0,0)
    print out        

