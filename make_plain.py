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
2014
2014-05-19 Write grammatical cats also
"""

afile     = None

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
<s freq="12">
word tag lemma
...
</s>

<s freq=...>
'''

inside = False
sentence = []
gcats = []
afile_out = afile+".utf8.txt"
gcats_out = afile+".utf8.cats"
enc = "ISO-8859-1"
freq = 1
with codecs.open(afile, "r", encoding=enc) as f:
    with codecs.open(afile_out, "w", encoding="utf-8") as fo:
        with codecs.open(gcats_out, "w", encoding="utf-8") as fc:
            for line in f:
                line = line[:-1]
                if not inside:
                    m = re.search( "<s freq=\"(\d+)\">", line)
                    if m:
                        freq = int(m.group(1))
                        inside = True
                else:
                    #print line
                    if line == "</s>":
                        inside = False
                        if len(sentence) > 3:
                            for i in xrange(0, freq):
                                fo.write( ' '.join(sentence)+"\n" )
                                fc.write( ' '.join(gcats)+"\n" )
                        sentence = []
                        gcats = []
                        freq = 1
                    else:
                        bits = line.split()
                        if len(bits) > 0:
                            sentence.append(bits[0])
                            gcats.append(bits[1])
                            
