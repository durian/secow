#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Simple TIMbleserver PYthon Interface
#
import os
import re
import sys
from xml.dom import minidom
import datetime
import time
from time import strptime
from time import asctime
from math import sqrt,sin,cos,asin,pi
import getopt
import math
import codecs
import socket
from time import sleep
from itertools import islice, izip
from operator import itemgetter
import random
import copy
import math;
from itertools import izip
import cProfile, pstats, io

# ---
# 2014-01-30 10:00:00: Added confidence
# 2013-12-06 14:27:00: added confusion parameter
# 2013-12-10 11:08:32: added self.md
# 2014-04-30 13:28:00: Added self.distr in classifier to fix in_distr 
# 2014-06-06 09:48:00: Added fix or DISTANCE with exponent in timblserver output
# ---

debug = False
def dbg(*strs):
    if debug:
        print >> sys.stderr, "DBG:", "".join(str(strs))

def find(f, seq):
  """Return first item in sequence where f(item) == True."""
  for item in seq:
    if f(item): 
      return item

# ----

class Cache():
    def __init__(self, name):
        self.name = name
        self.cache = {}
        self.keys = []
        #print "New cache:",name
    def store(self, k, v):
        if k in self.keys:
            return
        #print "Store in", self.name, k #, repr(v)
        self.cache[k] = v
        self.keys.append(k)
        #print self.name, "has now", len(self.keys), "items"
    def retrieve(self, k):
        try:
            #print "Retrieved from",self.name, k
            return self.cache[k]
        except:
            return None
    def has_key(self, k):
        if k in self.keys:
            return True
        return False
    def strhash(self, str):
        return hash(str)
    
'''
[ _ _ _ the quick brown fox _ _ _ ]
        ^start
        [ pos-LC : pos+LC ]
'''
def window_lr( str_ar, lc, rc ):
    if type( str_ar ) == "str":
        str_ar = str_ar.split()
    # words = ["_" for x in range(lc-1)] + ["<S>"] + str_ar + ["</S>"] + ["_" for x in range(rc-1)]
    words = ["_" for x in range(lc)] + str_ar + ["_" for x in range(rc)]
    result = []
    for i in range(len(str_ar)):
        #              shift to right index by added lc
        res = words[i:i+lc] + words[i+1+lc:i+rc+1+lc] + [str_ar[i]]
        #print i, words[i:i+lc],words[i+1+lc:i+rc+1+lc],"=",str_ar[i]
        #print " ".join(res)
        result.append( " ".join(res) )
    return result

def window_lr_nt( str_ar, lc, rc ):
    """
    Windows without a blank target position, and the target is the string "MISSING".
    Older version which does include the focus in the instance.
    """
    if type( str_ar ) == "str":
        str_ar = str_ar.split()
    words = ["_" for x in range(lc)] + str_ar + ["_" for x in range(rc)]
    result = []
    for i in range(len(str_ar)):
        #              shift to right index by added lc
        res = words[i:i+lc] + words[i+lc:i+rc+lc] + ["MISSING"]
        result.append( " ".join(res) )
    return result

def window_lr_nt2( str_ar, lc, rc ):
    """
    Windows without a blank target position, and the target is the string "MISSING"
    Skips the word at target position!
    """
    if type( str_ar ) == "str":
        str_ar = str_ar.split()
    words = ["_" for x in range(lc)] + str_ar + ["_" for x in range(rc)]
    result = []
    for i in range(len(str_ar)):
        #              shift to right index by added lc
        res = words[i:i+lc] + words[i+lc+1:i+rc+lc+1] + ["MISSING"]
        result.append( " ".join(res) )
    return result

# Window in str_ar, but only around word i (the i in the loop above)
# 2-1-2
def window_lri( str_ar, lc, rc, i ):
    """
    Windows without a target position, 2-1-2, around
    position i in the str_ar.
    """
    if type( str_ar ) == "str":
        str_ar = str_ar.split()
    # words = ["_" for x in range(lc-1)] + ["<S>"] + str_ar + ["</S>"] + ["_" for x in range(rc-1)]
    words = ["_" for x in range(lc)] + str_ar + ["_" for x in range(rc)]
    result = []
    try:
        res = words[i:i+lc] + words[i+1+lc:i+rc+1+lc] + [str_ar[i]]
        result.append( " ".join(res) )
    except IndexError:
        print words
        print str_ar
        print i, lc, rc
        #sys.exit(8)
    return result

def window_lri_nt2( str_ar, lc, rc, i ):
    """
    Windows without a target position, 2-0-2, around
    position i in the str_ar. Target is "MISSING". Skips
    word at target position.
    """
    if type( str_ar ) == "str":
        str_ar = str_ar.split()
    words = ["_" for x in range(lc)] + str_ar + ["_" for x in range(rc)]
    result = []
    res = words[i:i+lc] + words[i+lc+1:i+rc+lc+1] + ["MISSING"]
    result.append( " ".join(res) )
    return result

# Window around i, 2-0-2
def window_lri_nt( str_ar, lc, rc, i ):
    """
    Windows without a target position, 2-0-2, around
    position i in the str_ar. Target is "MISSING"
    """
    if type( str_ar ) == "str":
        str_ar = str_ar.split()
    words = ["_" for x in range(lc)] + str_ar + ["_" for x in range(rc)]
    result = []
    res = words[i:i+lc] + words[i+lc:i+rc+lc] + ["MISSING"]
    result.append( " ".join(res) )
    return result

# As above, but supply a list with targets (e.g pos tags)
# Other difference, str is a tokenized list here.
def window_lrt( tokens, lc, rc, targets ):
    """
    Windows the "tokens", fills in the targets from the "targets" argument.
    """
    words = ["_" for x in range(lc)] + tokens + ["_" for x in range(rc)]
    result = []
    for i in range(len(tokens)):
        #              shift to right index by added lc
        res = words[i:i+lc] + words[i+1+lc:i+rc+1+lc] + [targets[i]]
        result.append( " ".join(res) )
    return result

def window_to( str, lc, o ): #offset
    str_ar = str.split()
    # words = ["_" for x in range(lc-1)] + ["<S>"] + str_ar + ["</S>"] + ["_" for x in range(rc-1)]
    words = ["_" for x in range(lc)] + str_ar
    result = []
    for i in range(len(str_ar)-o):
        #              shift to right index by added lc
        res = words[i:i+lc] + [str_ar[i+o]]
        #print i, words[i:i+lc],words[i+1+lc:i+rc+1+lc],"=",str_ar[i]
        #print " ".join(res)
        result.append( " ".join(res) )
    return result
        
def window_lr_wt( tokens, lc, rc, targets ):
    """
    Windows the "tokens" with target from tokens, fills in the targets 
    in target position from the "targets" argument. This is the "it:1"
    format used in wopr.
    """
    if targets == None:
        targets = tokens
    words = ["_" for x in range(lc)] + tokens + ["_" for x in range(rc)]
    result = []
    for i in range(len(tokens)):
        #              shift to right index by added lc
        res = words[i:i+lc] + words[i+lc:i+lc+1] + words[i+1+lc:i+rc+1+lc] + [targets[i]]
        result.append( " ".join(res) )
    return result

def window_lr_wti( str_ar, lc, rc, target, i ):
    if type( str_ar ) == "str":
        str_ar = str_ar.split()
    if target == None:
        target = str_ar[i] #"MISSING"
    words = ["_" for x in range(lc)] + str_ar + ["_" for x in range(rc)]
    result = []
    res = words[i:i+lc] + words[i+lc:i+lc+1] + words[i+1+lc:i+rc+1+lc] + [target]
    result.append( " ".join(res) )
    return result

class TServers():
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.ibs = []
        self.type = 0 #normal, 1=missing, 2=it:1
        self.classifiers = []
        self.s = None
        self.file = None
        self.lex = {}
        self.topn = 3
        self.triggers = {}
        self.contexts = {}
        self.caches = {}
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.connect((self.host, self.port))
            self.file = self.s.makefile("rb") # buffered
            #self.s.settimeout(1)
            #print self.s.gettimeout()
        except:
            #print "Error, no timblserver"
            raise Exception('TServer', 'Cannot contact timblserver.')
        self.readline() #available bases
                        #print "1",self.data
        self.readline() #available bases
                        #print "2",self.data
        #self.readline() #available bases
        #print "3",self.data

    def info_str(self):
        tmp = ""
        for cl in self.classifiers:
            tmp += cl.info_str()+" "
        return tmp
    def readline(self):
        "Read a line from the server.  Strip trailing CR and/or LF."
        CRLF = "\r\n"
        if not self.file:
            return
        s = self.file.readline()
        dbg(s)
        if not s:
            raise EOFError
        if s[-2:] == CRLF:
            s = s[:-2]
        elif s[-1:] in CRLF:
            s = s[:-1]
        self.data = s

    def sendline(self,l):
        try:
            self.s.sendall(l)
        except socket.error:
            print "Socket kapot."
        
    # classify one instance, classifier c
    def classify( self, c, i ):
        if not self.s:
            return
        if type(i) is list:
            self.i = ' '.join(i)
            tokens = i
        else:
            self.i = i
            tokens = self.i.split()
        self.target = tokens[-1]
        #what do we return? Own class for ib?
        c.error = False
        #try:
        self.sendline("b "+c.name+"\n")
        self.readline()
        # check result!
        if self.data[0:5] == "ERROR":
            c.ans = []
            c.error = True
            return
        self.sendline("c "+self.i+"\n")
        self.readline()
        if self.data[0:5] == "ERROR":
            c.ans = []
            c.error = True
            return
        self.grok( c, self.data )
        c.ans = self.ans

    def exit_ts(self):
        self.sendline("EXIT\n")
        self.readline()
        
    # classify with triggers.
    def classify_tr(self, i):
        if not self.s:
            return
        self.i = i
        tokens = self.i.split()
        self.target = tokens[-1]
        if self.target in self.triggers:
            c = self.triggers[self.target]
            return self.classify(c,i)
        return []

    def get_trigger(self, i):
        tokens = i.split()
        target = tokens[-1]
        if target in self.triggers:
            c = self.triggers[target]
            return c
        return None
    
    def grok( self, c, tso ):
        '''
        Parse the TimblServer output
        '''
        #CATEGORY {concerned} DISTRIBUTION { concerned 2.00000, volatile 1.00000 } DISTANCE {0} 
        #       eventually                                                                      MATCH_DEPTH {0}
        dbg(tso)
        # error checking
        if tso[0:5] == "ERROR":
            print tso
            print self.i
            self.data = ""
            self.ans = []
            self.distr = []
            c.error = True
            return
        m = re.search( r'^CATEGORY {(.*)} DISTRIBUTION { (.*) } DISTANCE {([0-9e\.]*?)}$', tso )
        #print m.group(1) #concerned
        if not m:
            #m = re.search( r'^CATEGORY {(.*)} DISTRIBUTION { (.*) } DISTANCE {([0-9e\.]*?)} MATCH_DEPTH {(.*?)}$', tso )
            m = re.search( r'^CATEGORY {(.*)} DISTRIBUTION { (.*) } DISTANCE {(.*?)} MATCH_DEPTH {(.*?)}$', tso )
        if not m:
            dbg("No matching output?")
            c.ans = []
            c.error = True
            return
        # check cache
        if c.name in self.caches:
            strh = self.caches[c.name].strhash(tso)
            if self.caches[c.name].has_key(strh):
                (self.ans, c.distr, c.distr_w) = self.caches[c.name].retrieve(strh)
                return
        self.classification = m.group(1)
        #print m.group(2) #concerned 2.00000, volatile 1.00000
        #print m.group(3) #0 distance
        #print m.group(4) #0 match_depth, if present
        self.distance = float(m.group(3))
        try:
            self.md = int(m.group(4))
        except IndexError:
            self.md = -1
        #maybe set a cap on large distributions - we don't use them anyway
        bits = m.group(2).split()
        pairs = zip(bits[::2], bits[1::2])
        #remove silly commas from frequencies
        self.distr = {}
        c.distr = []
        self.sum_freqs = 0
        self.distr_count = 0
        c.distr_w = [] #work directly in Classifier
        for pair in pairs:
            #print pair[0], pair[1].rstrip(",")
            self.sum_freqs += float(pair[1].rstrip(","))
            c.distr_w.append(pair[0])
            self.distr_count += 1
            c.distr.append( (pair[0], float(pair[1].rstrip(","))) ) #float(pair[1][:-1])) )
            #CHECK IN THIS LOOP FOR CD ! Order is wrong for RR?

        if c.raw == True: #doesn't really make it faster, for-loop above is slowest?
            c.distr = [(w,f,f/self.sum_freqs) for (w,f) in c.distr]
            topn = c.distr[0:self.topn]
            self.ans = (self.i, self.classification, 0, 0, 0,\
                    "?", "?", self.distr_count, self.sum_freqs, 0, topn, self.md)
            if c.name in self.caches:
                strh = self.caches[c.name].strhash(tso)
                if self.caches[c.name].has_key(strh):
                    return
                self.caches[c.name].store(strh, (self.ans, c.distr, c.distr_w))
            return

        #print sorted( distr.iteritems(), key=itemgetter(1), reverse=True )[0:5]
        #print "dc,sf",distr_count, sum_freqs
        #self.distr = copy.deepcopy(\
        #            sorted( distr.iteritems(), key=itemgetter(1), reverse=True ) )
        c.distr = sorted( c.distr, key=itemgetter(1), reverse=True )
        #self.distr = sorted( self.distr.iteritems(), key=operator.itemgetter(1), reverse=True)
        c.distr = [(w,f,f/self.sum_freqs) for (w,f) in c.distr]
        topn = c.distr[0:self.topn]
        #c.distr = copy.deepcopy(self.distr) #have a full version
        # Most of the following are 0/[] for not used in hoo2013
        # If True, we calculate all the probs, otherwise, return
        # immediately, (after filling the cache).
        if c.calc_probs == False:
            self.ans = (self.i, self.classification, 0, 0, 0,\
                    "?", "?", self.distr_count, self.sum_freqs, 0, topn, self.md)
            if c.name in self.caches:
                strh = self.caches[c.name].strhash(tso)
                if self.caches[c.name].has_key(strh):
                    return
                self.caches[c.name].store(strh, (self.ans, c.distr, c.distr_w))
            return
        self.logs = [p * math.log(p,2) for (w,f,p) in c.distr]
        self.entropy =-sum(d for d in self.logs)
        self.pplx = math.pow(2, self.entropy)
        self.p = 0
        self.indicator = "??"
        self.ku = "u"
        self.rr = 0
        self.log2p = 0
        self.wlpx = 0

        lexf = c.in_lex(self.target) * 1.0 
        if lexf:
            self.ku = "k"
        if self.classification == self.target:
            self.p = (c.distr[0])[2]
            self.indicator = "cg"
            self.rr = 1
        else:
            #print "ID",self.in_distr(self.target) #faster than next line?
            tmp = [(w,f,p) for (w,f,p) in c.distr if w == self.target]
            if tmp != []:
                tmp = tmp
                self.p = tmp[0][2]
                self.indicator = "cd"
                self.rr = 1.0/(c.distr.index(tmp[0])+1)
            else:
                self.indicator = "ic"
                if lexf:
                    self.p = lexf / c.get_lex_sumfreq()
        #if self.p == 0: self.p = 1.8907e-06 #p(0) should be calculated
        try:
            self.log2p = math.log(self.p,2) #word logprob
            self.wlpx  = math.pow(2,-self.log2p)
        except ValueError:
            self.log2p = -99.0
            self.wlpx  = 0 #pow(2,32) #0 #should be inf, ok for logscale y plot
        
        self.ans = (self.i, self.classification, self.log2p, self.entropy, self.wlpx,\
                    self.indicator, self.ku, self.distr_count, self.sum_freqs, self.rr, topn, self.md)
        # check cache
        if c.name in self.caches:
            strh = self.caches[c.name].strhash(tso)
            if self.caches[c.name].has_key(strh):
                return
            self.caches[c.name].store(strh, (self.ans, c.distr, c.distr_w))
  
    def in_distr(self, w):
        getword = itemgetter(0)
        res = find( lambda ding: ding[0] == w, self.distr )
        return res

    def in_top_distr(self, w, top):
        getword = itemgetter(0)
        res = find( lambda ding: ding[0] == w, self.distr[0:top] )
        return res

    def read_lex(self, lexfile):
        self.lex = dict( ( line.split()[0], int(line.split()[1])) for line in open(lexfile))
        self.lex_sumfreq = sum(self.lex.itervalues())
        self.lex_count = len(self.lex)

    def in_lex(self, w):
        try:
            return self.lex[w]
        except KeyError:
            return 0
        
    def add_triggers(self, c, t):
        for trigger in t:
            self.triggers[trigger] = c

    def add_classifier(self, c):
        self.classifiers.append(c)
        #should know context size
        if c.type <= 1:
            ctx = "l"+str(c.lc)+"r"+str(c.rc)+"t"+str(c.type)
        else:
            ctx = "l"+str(c.lc)+"t1r"+str(c.rc)
        if ctx in self.contexts:
            self.contexts[ctx].append(c)
        else:
            self.contexts[ctx] = [c]
        # Add cache
        if c.name not in self.caches:
            self.caches[c.name] = Cache(c.name)
        # add triggers to TServer, trigger_word => classifier
        self.add_triggers(c, c.triggers)
    def get_classifiers(self, ctx):
        if ctx in self.contexts:
            return self.contexts[ctx]
        return []

    def get_classifier_by_name(self, name):
        """
        name refers to the name of the igtree, in timblserver
        """
        for c in self.classifiers:
            if c.name == name:
                return c
        return None

    def get_classifier_by_id(self, id):
        """
        id can be anything (unique)
        """
        for c in self.classifiers:
            if c.id == id:
                return c
        return None

    def get_classifier_by_trigger(self, tr):
        """
        """
        if tr in self.triggers:
            return self.triggers[tr]
        return None

    def get_contexts(self):
        return self.contexts.keys()

    def window_all(self, l):
        #window the line for all the context sizes this server handles.
        #possibilities are l2r0, l2t1r0, l2r0t1
        res = dict()
        for ctx in self.get_contexts():
            ctx_re = re.compile("l(\d)r(\d)t(\d)")
            m = ctx_re.match(ctx)
            if m:
                lc = int(m.group(1))
                rc = int(m.group(2))
                ty = int(m.group(3))
                if ty == 1:
                    il = window_lr_nt(l, lc, rc)
                else:
                    il = window_lr(l, lc, rc)
                res[ctx] = [i.split() for i in il] # = il
            else:
                ctx_re = re.compile("l(\d)t1r(\d)")
                #res = dict()
                #for ctx in self.get_contexts():
                m = ctx_re.match(ctx)
                if m:
                    lc = int(m.group(1))
                    rc = int(m.group(2))
                    il = window_lr_wt(l, lc, rc, None)
                    res[ctx] = [i.split() for i in il] # = il
        return res

    def window_around(self, l, i):
        #window only around word l[i] for all the context sizes this server handles.
        #if type==1, we have a "missing" classifier, we windows lc-rc, instead of
        # lc-t-rc
        res = dict()
        for ctx in self.get_contexts():
            ctx_re = re.compile("l(\d)r(\d)t(\d)")
            m = ctx_re.match(ctx)
            if m:
                lc = int(m.group(1))
                rc = int(m.group(2))
                ty = int(m.group(3))
                if ty == 1:
                    il = window_lri_nt(l, lc, rc, i)
                else:
                    il = window_lri(l, lc, rc, i)
                if len(il) > 0:
                    res[ctx] = il[0].split()
            else:
                ctx_re = re.compile("l(\d)t1r(\d)")
                m = ctx_re.match(ctx)
                if m:
                    lc = int(m.group(1))
                    rc = int(m.group(2))
                    il = window_lr_wti(l, lc, rc, None, i)
                    res[ctx] = il[0].split()
        return res

# Classifier, uses TimblServer
class Classifier():
    """
    name refers to the name of the igree (send to timblserver)
    id is the name we use to get the classifier.
    """
    def __init__(self, name, lc, rc, ty, ts):
        self.name = name
        self.id = name
        self.lc = lc
        self.rc = rc
        self.type = ty #1 is "missing"
        if ty <= 1:
            self.ctx = "l"+str(lc)+"r"+str(rc)+"t"+str(ty)
        if ty == 2: #the confusibles it:1 error version
            self.ctx = "l"+str(lc)+"t1"+"r"+str(rc)
        self.to = 0
        self.ts = ts #Timblserver
        self.ans = None  #one instance answer
        self.distr = []
        self.distr_w = None
        self.error = False
        self.triggers = []
        self.lex = None
        self.calc_probs = True #False for easier grok in TServer
        self.raw = False #don't even sort the distr. This will return a different c.distr
        self.cache = Cache(name)
    def info_str(self):
        return self.name+"/"+self.ctx
    def exit_ts(self):
        self.ts.exit_ts()
    def window_lr(self, s):
        if self.to == 0:
            res = window_lr(s, self.lc, self.rc)
        else:
            res = window_to(s, self.lc, self.to)
        return res
    def set_triggers(self, t):
        self.triggers = t
        self.ts.add_triggers(self, t)
    def classify_i(self, i):
        #self.ts.lex = self.lex
        #self.ts.lex_sumfreq = self.lex_sumfreq
        #self.ts.lex_count = self.lex_count
        t0 = datetime.datetime.now()
        i_str = repr(i) #PJB CRUDE!!
        if self.cache.has_key(i_str):
            # from cache ?
            #  self.ans = []
            #  self.distr = []
            tmp = self.cache.retrieve(i_str)
            if tmp:
                self.ans = tmp[0]
                self.distr = tmp[1]
                self.distr_w = tmp[2]
                t1 = datetime.datetime.now()
                td = t1-t0
                #print self.name+": td: "+str(td)
                return self.ans
            return None
        self.ts.classify(self, i)
        if self.ans:
            self.cache.store(i_str, (self.ans, self.distr, self.distr_w))
        t1 = datetime.datetime.now()
        td = t1-t0
        #print self.name+": td: "+str(td)
        return self.ans

    def classify_s(self, s):
        return [ self.classify_i(i) for i in self.window_lr(s) ]
    def classify_il(self, l):
        #cProfile.run('return [ self.classify_i(i) for i in l ]')
        return [ self.classify_i(i) for i in l ]
    def in_distr(self, w):
        getword = itemgetter(0)
        res = find( lambda ding: ding[0] == w, self.distr )
        return res
    def in_top_distr(self, w, top):
        getword = itemgetter(0)
        res = find( lambda ding: ding[0] == w, self.distr[0:top] )
        return res
    def in_distr_w(self, w):
        return w in self.distr_w
    def add_lex(self, lexicon):
        self.lex = lexicon
    def in_lex(self, w):
        if self.lex:
            return self.lex.in_lex(w)
        return 0 #this fun returns frequency
    def get_lex(self, w):
        if self.lex:
            return self.lex.get_lex(w)
        return None
    def hapax(self, line, h):
        if self.lex:
            return self.lex.hapax(line, h)
        return None
    def get_lex_sumfreq(self):
        if self.lex:
            return self.lex.lex_sumfreq
        return 0
    def get_lex_count(self):
        if self.lex:
            return self.lex.count
        return 0

# Classifier, uses TimblServer
class Lexicon():
    def __init__(self, name):
        self.name = name
        self.lex = {}
        self.trie =TrieNode()
        self.lex_sumfreq = 0
        self.lex_count = 0
        self.lex_file = None
    def make_trie(self):
        for word in self.lex.keys():
            self.trie.insert( word )
    def search(self, word, maxCost):
        # build first row
        currentRow = range( len(word) + 1 )
        results = []
        # recursively search each branch of the trie
        for letter in self.trie.children:
            self._search( self.trie.children[letter], letter, word, currentRow, results, maxCost )
        return results
    def _search(self, node, letter, word, previousRow, results, maxCost ):
        columns = len( word ) + 1
        currentRow = [ previousRow[0] + 1 ]
        # Build one row for the letter, with a column for each letter in the target
        # word, plus one for the empty string at column 0
        for column in xrange( 1, columns ):
            insertCost = currentRow[column - 1] + 1
            deleteCost = previousRow[column] + 1
            if word[column - 1] != letter:
                replaceCost = previousRow[ column - 1 ] + 1
            else:                
                replaceCost = previousRow[ column - 1 ]
            currentRow.append( min( insertCost, deleteCost, replaceCost ) )
        # if the last entry in the row indicates the optimal cost is less than the
        # maximum cost, and there is a word in this trie node, then add it.
        if currentRow[-1] <= maxCost and node.word != None:
            results.append( (node.word, currentRow[-1] ) )
        # if any entries in the row are less than the maximum cost, then 
        # recursively search each branch of the trie
        if min( currentRow ) <= maxCost:
            for letter in node.children:
                self._search( node.children[letter], letter, word, currentRow, results, maxCost )
    def read_lex(self, lexfile):
        try:
            self.lex = dict( ( line.split()[0], int(line.split()[1])) for line in open(lexfile))
            self.lex_sumfreq = sum(self.lex.itervalues())
            self.lex_count = len(self.lex)
            self.lex_file = lexfile
        except (IOError):
            pass
    def in_lex(self, w):
        try:
            return self.lex[w]
        except KeyError:
            return 0 #we return frequency here
    def get_lex(self, w):
        if w in self.lex:
            return self.lex[w]
        return None
    def hapax(self, line, h):
        words = line.split()
        res = []
        for w in words:
            wl = self.get_lex(w)
            if wl > h:
                res.append(w)
            else:
                res.append('HPX')
        return ' '.join(res)

class TrieNode:
    """
    http://stevehanov.ca/blog/index.php?id=114
    """
    def __init__(self):
        self.word = None
        self.children = {}
    def insert( self, word ):
        node = self
        for letter in word:
            if letter not in node.children:
                node.children[letter] = TrieNode()
            node = node.children[letter]
        node.word = word

# read dictionary file into a trie
#trie = TrieNode()
#for word in open(DICTIONARY, "rt").read().split():
#    WordCount += 1
#    trie.insert( word )
    
# ----

# Output from wopr:
# instance+target classification log2prob entropy word_lp guess k/u md mal dist.cnt dist.sum RR ([topn])
# stympy:
# (i, classification, log2p, entropy, wlpx, indicator, ku, distr_count, sum_freqs, rr, topn, md)

#('Thursday , in in', 'in', 0.0, -0.0, 1.0, 'cg', 'u', 1, 3766.0, 1, [('in', 3766.0, 1.0)])
# instance_str         cl   stats                                    [distr]
def ans_str(ans):
    if ans and len(ans) == 12:
        return '{0} {1} {2:.4f} {3:.4f} {4:.4f} {5} {6} _ _ {7:d} {8:.0f} {9:.4f}'.format(*ans) + topn_str(ans[10])
    return None

#  pberck@scylla:/exp2/pberck/2013/confusibles2$ head utexas.t10000.dt.cf05.l4t1r4_CFEV12041.sc
#  _ _ _ _ Thursday , in one of Thursday (Thursday) 0 0 1 1 [ ]
#_   _ _ Thursday , in one of the , (,) -4.38438 10.6671 20.8848 217138 [ ]
def ans_sc(ans):
    # target is wrapped around () for wopr compatibility
    # THESE ARE PROLLY NOT THE RIGHTS FIELDS COMPARED TO WOPR SC OUTPUT
    if ans and len(ans) == 12:
        return '{0} ({1}) {2:.4f} {3:.4f} {8:.0f} {9:.4f}'.format(*ans) + topn_str(ans[10])
    return None

# Short string
def ans_shstr(ans):
    if ans and len(ans) == 12:
        #  classification distr
        return '{1}'.format(*ans) + topn_str(ans[10])
    return None

def ans_to_dict(ans):
    """
    Some extra stats are calculated here. Should simplify, have min_md and confidence calculation.
    confidence = ans[10][0][1] / sumf (1 = 50:50)
    min_md - do we have md? We do now.
    """
    if ans and len(ans) == 12:
        nms = [ "i", "classification", "log2p", "entropy", "wlpx", "ind", "ku", "dcount", "sumf", "rr", "topn", "md" ]
        b = dict(zip(nms, ans))
        posneg_r = 0
        confidence = 0
        if len(ans[10]) > 1:
            """
            Ratio op top-0 / top-1, or, between the nrs 1 and 2.
            """
            posneg_r = float(ans[10][0][1]) / float(ans[10][1][1]) #independent from topn
        confidence = float(ans[10][0][1]) / float(ans[8])
        b["posneg_r"] = posneg_r
        b["confidence"] = confidence
        return b
    else:
        return None
    
def topn_str(tns):
    if len(tns) == 0:
        return ""
    res = " [ "
    for tn in tns:
        s = '{0} {1:.0f} '.format(*tn)
        res += s
    res += "]"
    return res

def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if not s1:
        return len(s2)
    
    previous_row = xrange(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1 # j+1 instead of j since previous_row and current_row are one character longer
            deletions = current_row[j] + 1       # than s2
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

#file with ans_str(results):
#plot [][] "plt" using 6:xticlabels(3) with lp

# -----------------------------------------------------------------------------
# ----- MAIN starts here
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print "Python interface for timblserver."

    c = Cache("1")
    print c.has_key("t")
    c.store("t", ("a", "b"))
    print c.has_key("t")
    print
    print c.retrieve("t")
    print

    print "window_lr( '1 2 3 4'.split(), 2, 2 )"
    print window_lr( "1 2 3 4".split(), 2, 2 )
    print
    print "window_lr_nt( '1 2 3 4'.split(), 2, 2 )"
    print window_lr_nt( "1 2 3 4".split(), 2, 2 )
    print
    print "window_lr_nt2( '1 2 3 4'.split(), 2, 2 )"
    print window_lr_nt2( "1 2 3 4".split(), 2, 2 )
    print
    print 'window_lri( "1 2 3 4".split(), 2, 2, 2)'
    print window_lri( "1 2 3 4".split(), 2, 2, 2)
    print
    print 'window_lri_nt( "1 2 3 4".split(), 2, 2, 2)'
    print window_lri_nt( "1 2 3 4".split(), 2, 2, 2)
    print
    print 'window_lrt( "1 2 3 4".split(), 2, 2, "t1 t2 t3 t4".split() )'
    print window_lrt( "1 2 3 4".split(), 2, 2, "t1 t2 t3 t4".split() )
    print
    print 'window_to( "1 2 3 4", 2, 1 )'
    print window_to( "1 2 3 4", 2, 1 )
    print
    print 'window_lr_wt( "1 2 3 4".split(), 2, 2, "None" )'
    print window_lr_wt( "1 2 3 4".split(), 2, 2, None )
    print
    print 'window_lr_wt( "1 2 3 4".split(), 2, 2, "t1 t2 t3 t4".split() )'
    print window_lr_wt( "1 2 3 4".split(), 2, 2, "t1 t2 t3 t4".split() )
    print

    # pretend timbleserver with "test" ibase
    try:
        s = TServers("localhost", 2000)
    except:
        print "No timblserver."
        sys.exit(1)
    c0 = Classifier("test", 2, 2, 1, s)
    s.add_classifier(c0) #c0.classify_i() will use 2-1-2
    c1 = Classifier("test", 2, 2, 0, s)
    c1.id = "test1" #c1.classify_i() will use 2-0-2, get_by_id("test1")
    s.add_classifier(c1)
    c2 = Classifier("test", 2, 2, 2, s)
    c2.id = "test2" #c1.classify_i() will use 2-1-2, get_by_id("test2"), it:1 wopr format
    s.add_classifier(c2)
    print 's.get_contexts()'
    print s.get_contexts()
    print 's.window_all( "A b c d".split() )'
    print s.window_all( "A b c d".split() )

    wla = s.window_around( "A b c d".split(), 2 )
    print wla
    
    #s1=TServers("localhost", 2000)
    # DTI is 2-2, austen is 2-0
    #cl = Classifier("test", 2, 2, 0, s1) 
    #cl.calc_probs = False
    #cl.raw = True
    #timing

    t0 = time.time()
    #cProfile.run("cl.classify_i(instance)")
    num = 1
    for i in xrange(num): 
        # Force a default distribution result
        instance = (str(time.time())+" ") * c0.lc + "__NOT__ " * c0.rc + "_"
        print instance
        c1.classify_i(instance)
        print 'cl.ans'
        print c1.ans
        print 'ans_str(cl.ans)'
        print ans_str(c1.ans)
        print 'ans_shstr(cl.ans)'
        print ans_shstr(c1.ans)

    print "Wall clock time for",num,"classifications:",time.time()-t0, (time.time()-t0)/10.0
