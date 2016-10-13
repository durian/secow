#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# 2013-12-11 Implemented start of MD version, corr1 
#            Seperate MIN_MD parameters per error type 
#            Added pattern.en library
#            Added tokenize=False
#            Added chunks, relations=False, alternative
#            Added pipsqueak
#            Added fix for id_str for corr1 (did not work)
#            Added vform code, neg and hasspc
# 2013-12-12 Version 005, added param_set
#            Fixed id_str (again)
#            Added param_set 3
# 2013-12-13 Added param_set 4
#            Addes server config 5 (copy of 4, but tserver_005.ini has a4 instead of a1)
# 2013-12-16 Added param_set 5, version 006
# 2013-12-16 Ignore this 007 version
# 2013-12-18 Added VERBPRED and NOUNDPRED and corr2 for tserver_007.ini
#            added -S 008
# 2013-12-23 Added corr3
#            added -S 009
# 2013-12-27 Added dp1 for DetsPreps only (hoo2012)
# 2013-12-28 Added -S 010 for dp1
#            Added dp2 with extra min_md parameters
# 2013-12-29 gc_013.py: Added dp3 with only min_md params
# 2014-01-28 gc_014.py Work on connl hared task 2014, "cst_" heuristics
# 2014-01-29 Fixes, improvements, added tserver_001#
# 2014-01-31 Some cleanup, removed pyconfig deprecated code
# 2014-02-03 Added VERBPRED stuff
# 2013-02-04 Added paramset 6 for conll2014st
# 2014-02-05 Renamed to conll2014.py, removed old stuff.
# 2014-02-06 Moved tserver and paramsets to files.
# 2014-02-12 Added PREP stuff
# 2014-02-13 Bugfixes
# 2014-02-17 Clean up (kuch) and fixes
# 2014-03-03 Better stats, some fixes.
# 2014-03-10 Added LOG
# 2014-03-11 Added DC, self.classify(...), fixed confidence in stimpy
# 2014-03-16 removed cst1, implemented preps
# 2014-03-20 More fixes, added a new cst1 again
# 2014-04-29 Started with hoo2012 code in this // framework
# 2014-04-30 Implemented hoo212 and hoo2012new
# 2014-05-01 Work arounf for double-space crash bug in pattern.en
# 2014-05-02 Added hoo2012err, hoo2012 is now without ERR classifiers
# 2014-05-05 Fixes for hoo2012 (original)
# 2014-05-06 Xhange for high DETMIS in hoo2012err, and PREPMIS also
# 2014-05-17 Removed unnecessary stuff, only "wp " left.
#
# Instructions:
# Start a timbleserver:
#    timblserver --config=tserver_001.ini --daemonize=no
# Start run
#   python2.7 conll2014.py -f conll14st.txt -p24 -S tsdefs.txt -c cst0 -C pm.txt -i run002c
#                                                 ^            ^       ^         ^- ID string for output
#                                                 |            |       |- parameter set file
#                                                 |            +- correction algorithm "cst0" (defined in the python code)
#                                                 +- timbleserver definition file
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
import cProfile
import threading
from threading import Thread, Lock
from Queue import Queue
from Queue import PriorityQueue
from Queue import Empty
import multiprocessing
from stimpy import *
try:
    from pattern.en import *
except ImportError:
    print "WE NEED THE PATTERN.EN LIBRARY!"
    #sys.exit(2)
#
import logging
import logging.handlers
#
cur_pid = ""
try:
    cur_pid = "_{0:05n}".format(os.getpid())
except:
    pass
#
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s')
#
logfile = "./gc"+cur_pid+".log"
rtfile  = logging.handlers.RotatingFileHandler(logfile ,maxBytes=1024*1024*50, backupCount=1)
console = logging.StreamHandler()
#
glog = logging.getLogger('GC')
rtformat='%(asctime)s %(levelname)-8s %(message)s'
rtformatter = logging.Formatter(fmt=rtformat)
rtfile.setFormatter(rtformatter)
glog.addHandler(rtfile)
glog.propagate = False #stop console log for this one
# Set up console
cformat='%(asctime)s %(message)s'
cformatter = logging.Formatter(fmt=cformat, datefmt="%Y%m%d %H:%M:%S")
console.setFormatter(cformatter)
console.setLevel(logging.INFO)
glog.addHandler(console)
#
glog.info("START conll2014.py")
glog.info("See "+logfile+" for debug info.")
#
LOG = True
#
# Regexen
#
#NUM   = re.compile( r'''(\d+) | ((\d+[\.,:\/]?)+(\d+[:\/]?))''', re.DOTALL | re.VERBOSE)
#PUNC  = re.compile( r'''([][(){}<>=,\.\?\!;\'&:*+-/]+)''', re.DOTALL )
#CLEAN = re.compile( r'''([-A-Za-z]{3,})''', re.DOTALL | re.VERBOSE) # NOT FOR UTF8 texts!!

# Thread worker class thingy.
#
class myThread (threading.Thread):
    def __init__(self, threadID, server_id):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.res = []
        self.distr = []
        self.c = None
        self.sid = server_id
        self.cont = True
        self.cnt = 0
    def debug(self, s):
        glog.debug(self.threadID+": "+s)
    def debug_ans(self, ans, sid, istr):
        if LOG:
            try:
                posneg_r = float(ans['posneg_r'])
                md = int(ans['md'])
                cf = float(ans['confidence'])
                dc = int(ans['dcount'])
                #out = "PN:{0:0.2f} MD:{1:02d} CF:{2:0.2f} DC:{3:06d}".format(posneg_r, md, cf, dc)
                #out = "ANS {"+sid+"} "+out+" ["+istr+"]"
                #self.debug(out) #we calculate averages etc from these strings....need all digits
                self.debug("ANS {"+sid+"} PN:"+str(posneg_r)+" MD:"+str(md)+" CF:"+str(cf)+" DC:"+str(dc)+" ["+istr+"]")
            except:
                pass
    def classify(self, sid, wla):
        c = servers[self.sid].get_classifier_by_id(sid)
        if not c:
            self.error(sid+" not found.")
            sys.exit(1) #abort if not found.
        instance = wla[c.ctx] #Ask for the instance associated with this classifiers context (#wl[c.ctx][i])
        res = c.classify_i( instance ) #and classify it
        if c.error:
            self.error(sid+" returned error ["+repr(instance)+"]")
            sys.exit(1) #if error, abort.
        self.distr = c.distr #copy.deepcopy(c.distr) 
        self.c = c
        instance_str = ' '.join(instance) + " ("+res[1]+")"
        ans = ans_to_dict( res ) #creates an array with answer and relevant info.
        self.debug_ans( ans, sid, instance_str )
        return (res, ans, instance_str)
    def info(self, s):
        if not type(s) == "str":
            s = repr(s)
        glog.info(self.threadID+": "+s)
    def error(self, s):
        glog.error(self.threadID+": "+s)
    def process(self, idx, line, cmd, extra):

        if cmd == "wp": # Test, a WORDPRED only
            if not sentences:
                #          handle instances.
                #print idx, line
                words = line.split()
                self.res = []
                self.debug("words "+str(words))
                target = words[-1:][0]
                x = (line, target, 0.0, 0.0, 0.0, '--', '-', 0, 1, 1, [])
                res = ans_sc(x) + " [ ]"
                c = servers[self.sid].get_classifier_by_trigger(target)
                if c:
                    #print c.name
                    res = c.classify_i( line )
                    res = ans_sc(res)
                    #print "classsifier", res #ans_str, wopr output? #add classifier used?
                r.put( (idx, [(0, res)]) )
            else:
                '''
                Testing testing.
                '''
                words = line.split()
                self.res = []
                # Zero the stats
                self.stats = {}
                changes = []
                new_s = []
                prev_was_class = '' #the previous word was class ''
                """
                ------------------------------------ LOOP ----------------------------------------------
                
                """
                for i,w in enumerate(words):
                    local_changes = []
                    fired = 0
                    pos = len(new_s) #NB this is position in the new string, not POS(tag), not i
                    stat = "NOP"
                    try:
                        self.debug("START["+str(idx)+"]:"+str(i)+"-"+str(pos)+" "+w+":"+repr(new_s)+"/"+repr(words[i:]))
                    except UnicodeDecodeError:
                        self.debug( "START["+str(idx)+"]:"+str(i)+"-"+str(pos)+" UnicodeDecodeError" )
                    """
                    Prepare possibllse instances around current position in wla. We take the modified (!)
                    words before our current position in the instances if feedback is True.
                    """
                    if feedback:
                        wla = servers[self.sid].window_around(new_s + words[i:], pos) #contexts, new_s contains the corrected sentence up to now.
                    else:
                        wla = servers[self.sid].window_around(words, i ) #pos) #no feedback from corrections
                    if True or i == 0:
                        self.debug("wla="+repr(wla))

                    #if w in ["ett", "en"]:
                    if w in ["han", "honom"]:
                        sid = "WORDPRED" 
                        (res, ans, instance_str) = self.classify(sid, wla)
                        #print instance_str
                        ding = self.c.in_distr( w ) #returns if word in text is in distribution
                        self.debug("WID="+repr(ding)) #WID for easy grepping
                        if res[1] != w: #res[1] is the anwer from timblserver
                            #print w, float(ans['confidence'])
                            if float(ans['confidence']) > 0.1: 
                                local_changes.append( ("REP", w, [res[1]], 1, instance_str, "WORDPRED") ) #the "change" info
                                fired = 1
                                stat = "REP" #put in local changes?
                            else:
                                self.debug(sid+" did not pass parameters.")

                    """
                    Take the change, and apply it. Take highest priority.
                    """
                    self.debug("numchanges="+str(len(local_changes)))
                    if len(local_changes) > 0:
                        self.debug("changes="+repr(local_changes))
                        ordered_changes = sorted(local_changes, key=itemgetter(3), reverse=True) #highest num first
                        (typ, wrd, lst, pri, ist, stat) = ordered_changes[0]
                        changes.append(typ+"/"+wrd)
                        self.debug("oc="+repr((typ, wrd, lst, pri, ist, stat) ))
                        #new_s += lst 
                        if typ == "MIS":
                            new_s += lst
                        elif typ == "REP":
                            new_s += lst 
                        elif typ == "RED":
                            pass
                    else:
                        new_s += [w]
                        changes.append("---/"+w)
                        stat = "NOP"
                        
                    try:
                        self.stats[stat] += 1 #count it
                    except KeyError:
                        self.stats[stat] = 1 #count it

                    tmp = str(" ".join(new_s))
                    self.debug(str(i)+",new_s="+tmp )
                    
                self.debug( repr(changes) )
                tmp = str(" ".join(new_s))
                self.cnt += len(words)
                r.put( (idx, [(0, tmp)], self.stats) )

    
    def run(self):
        self.info( "Starting" )
        while self.cont:
            try:
                (idx, line, cmd, extra) = q.get_nowait()
                if idx % info_gap == 0:
                    self.info(str(idx)+","+line[:40]+"...")
                self.process(idx, line, cmd, extra)
                q.task_done()
            except Empty:
                self.info( "Queue empty." )
                self.cont = False 
        self.info( "Exit." )
        return 0

# ----

"""
s = pattern.en.parse('this is an apple .')
s.split()
[[[u'this', u'DT', u'O', u'O'], [u'is', u'VBZ', u'B-VP', u'O'], [u'an', u'DT', u'B-NP', u'O'], [u'apple', u'NN', u'I-NP', u'O'], [u'.', u'.', u'O', u'O']]]
[0][0][0] is the first word,
[0][0][1] is the first POS

lock.acquire()
    try:
        res_str = corenlp.parse(line)
    finally:
        lock.release()
        #res_str = corenlp.parse(line)
"""
def parse_str(s):   
    sp = parse(s, tokenize=False, chunks=False, relations=False, )
    items = sp.split()
    return items[0]

def tag_str(s):   
    '''
    >>> from pattern.en import *
    >>> parse("the quick brown fox")
    u'the/DT/B-NP/O quick/JJ/I-NP/O brown/JJ/I-NP/O fox/NN/I-NP/O'
    >>> tag("the quick brown fox")
    [(u'the', u'DT'), (u'quick', u'JJ'), (u'brown', u'JJ'), (u'fox', u'NN')]
    '''
    #pattern.en this crashes on double spaces.
    s0 = s.split()
    s = ' '.join(s0)
    sp = tag(s, tokenize=False)
    return sp

"""
Determine is we are dealing with don't, won't, &c.
"""
def neg(form):
    if len(form) > 3 and form[-3:] == "n't":
        return True
    elif len(form) > 3 and form[-4:] == " not":
        return True
    return False

def has_spc(form):
    """
    We need to filter out these:
    CHANGE 32 VBZ isn't wasn't [u'am not', u"aren't", u"wasn't", u"weren't"]
    otherwise we can change one word to two!
    """
    if ' ' in form:
        return True
    return False

# --------------------------------------------------------------------------------------------------------
# ---- Command line params, etc.
# --------------------------------------------------------------------------------------------------------

q = Queue()
r = PriorityQueue()
lock = Lock()

afile      = None
dirmode    = False 
dirpattern = "*"
workers    = []
procs      = int(multiprocessing.cpu_count() / 2)+1 
lexfile    = None
cmd        = "cst0" #we can have different algos here too, "corr1", "corr2", etc
outfile    = None
info_gap   = None
test       = False
test_words = ["One", "two", "three"]
test_pos   = 1
test_c_id  = None #means all classifiers
force      = False
sentences  = True #False #expect instances in test file
# pyconfig   = None #"pyserver_SET00.py" #generated by split_data_confusibles.py ##DEPRECATED##
param_set  = None #choose PARAMS = ...
id_str     = None
tserver    = "000" #tserver ID
feedback   = False #put our corrections back in sentence for context
info_only  = False #just print settings
vk_file    = None #extra input from valkuil

#PARAMS = { "MAX_DSIZE":100, "MINFREQ":0, "MINLD":0, "MAXLD":20, "MAXALT":100 }
CLEAN  = re.compile( r'''([-A-Za-z]{3,})''', re.DOTALL | re.VERBOSE) # NOT FOR UTF8 texts!!
# max distribution size
# in top-n
# minimum frequency of alternative
# minimum levenshtein distance
# maximum levenshtein distance
# maximum number of alternatives 
# test parameters:
#PARAMS = { "MAX_DSIZE":2000000, "INTOP":2000000, "MINFREQ":0, "MINLD":0, "MAXLD":3, "MAXALT":2000 }
#CLEAN  = re.compile( r'''([-A-Za-z]{1,})''', re.DOTALL | re.VERBOSE) # NOT FOR UTF8 texts!!

try:
    opts, args = getopt.getopt(sys.argv[1:], "C:c:d:ef:Fg:i:l:o:p:qsS:tP:T:I:V:", ["file=", "info"])
except getopt.GetoptError, err:
    print str(err)
    sys.exit(1)
for o, a in opts:
    if o in ("-f", "--file="):
        afile = a #if dirmode, is dirname
    elif o in ("-F"):
        force = True
    elif o in ("-c"):
        cmd = a
    elif o in ("-C"): #NOW A FILE
        param_set = a
    elif o in ("-d"):
        dirmode = True
    elif o in ("-e"):
        feedback = True      
    elif o in ("-g"):
        info_gap = int(a)
    elif o in ("-i"):
        id_str = a
    elif o in ("-l"):
        lexfile = a
    elif o in ("-o"):
        outfile = a
    elif o in ("-p"):
        procs = int(a)
    elif o in ("-s"):
        sentences = True
    elif o in ("-t"):
        test = True
    elif o in ("-T"):
        test_words = a.split()
    elif o in ("-P"):
        test_pos = int(a)
    elif o in ("-I"):
        test_c_id = a
    elif o in ("-S"): #This is now a filename
        tserver = a
    elif o in ("-q"): # "quiet"
        glog.setLevel(logging.WARNING)
    elif o in ("--info"): # "quiet"
        info_only = True
    elif o in ("-V"): 
        vk_file = a
    else:
        assert False, "unhandled option"

#optstr = "-f "+str(afile)+" -c "+str(cmd)+" -C "+str(param_set)+" -i "+str(id_str)+" -p "+str(procs)+" -S "+str(tserver)
optstr = " ".join(sys.argv)
glog.info("OPTIONS: "+optstr)

# Append to log file
#
try:
    with open("conll2014.log", "a") as fl:
        fl.write("\n"+str(datetime.datetime.now())+" "+platform.node()+"\n")
        fl.write(" python2.7 "+optstr+"\n")
except:
    glog.info("conll2014.log?")
    
# Connect to a timblserver on port 2000, uvt/hoo2013/software
# timblserver --config=ts.out --daemonize=no
#
# The servers[] has an entry for each processor to a TServer.
# We run only one TServer, so they are the same.
servers = []

#HOO lists

DETS=["a","all","an","another","any","both","each","either","every","many","neither","no","some","that","the","these","this","those","what","whatever","which","whichever","who","A","All","An","Another","Any","Both","Each","Either","Every","Many","Neither","No","Some","That","The","These","This","Those","What","Whatever","Which","Whichever","Who"]

#DETS = ["a", "an", "the" ]

PREPS=["about","above","across","after","against","along","alongside","amid","among","amongst","apart","around","as","aside","at","atop","before","behind","below","beneath","beside","besides","between","beyond","by","down","due","for","from","in","inside","into","near","next","of","off","on","onto","out","outside","over","past","per","since","though","through","throughout","till","to","toward","towards","under","unlike","until","up","upon","versus","via","vs.","whether","while","with","within","without","About","Above","Across","After","Against","Along","Alongside","Amid","Among","Amongst","Apart","Around","As","Aside","At","Atop","Before","Behind","Below","Beneath","Beside","Besides","Between","Beyond","By","Down","Due","For","From","In","Inside","Into","Near","Next","Of","Off","On","Onto","Out","Outside","Over","Past","Per","Since","Though","Through","Throughout","Till","To","Toward","Towards","Under","Unlike","Until","Up","Upon","Versus","Via","Vs.","Whether","While","With","Within","Without"]

'''
awk '{print $5}' < combined.l2r2.pf01 | sort | uniq -c | sort -n | tail -n10
 845690 from
 880052 at
1049086 by
1252938 as
1337578 with
1429463 on
2057544 for
3727884 in
5747260 to
6616979 of
'''
#PREPS = ["from", "at", "by", "as", "with", "on", "for", "in", "to", "of"]

'''
awk '{print $5}' < combined.l2r2.pf00 | sort | uniq -c | sort -n | tail
 133402 provide
 147244 being
 149778 see
 155146 know
 156981 make
 158877 used
 173108 made
 187502 did
 280271 said
 # 329178 's #no
 350528 do
 437629 been
 521042 were
 554384 has
 555552 had
 882834 have
1130187 are
1223013 was
1383222 be
2013278 is
'''
VERBS = [ "been", "were", "has", "had", "have", "are", "was", "be", "is", "do", "said", "did", "made", "used", "make", "know", "see", "being" ]

PARAMS = {}
if param_set:
    with open(param_set, "r") as f:
        glog.debug("Loading param_set: "+param_set)
        for line in f:
            if line[0] != "#" and len(line) > 2:
                bits = line.split()
                try:
                    PARAMS[bits[0]] = float(bits[1])
                except:
                    glog.info("Error in param_set: ["+line[:-1]+"]")            
glog.info("PARAMS: "+repr(PARAMS))

# ------------ END PARAM SETS ---------------------

'''
read from file:

EXAMPLE:
Using the same instance base in the server for two "tasks":

VERBPRED    VERBPRED    4 4 0  # left-context right-context type
VERBPRED    VERBMIS     4 4 1
DETS_PN_MIS DETS_PN_RED 2 2 0  # A
DETS_PN_MIS DETS_PN_MIS 2 2 1  # B
^^          ^^ name in conl2014.py code (get_classifier_by_id(name))
++ name in timble
   
A will generate normal instances
B will generate instances with "missing" focus

Text           : One two three
normal instance: _ One three _ -> two
type 1         : _ One two three -> MISSING

-----

#WORDPRED="-i utexas.10e6.dt.1e5.l2r2_-a1+D.ibase -a1 +D +vdb+di +vmd"
m = re.search( r'^(.*?)=\"-i (.*?) (.*?) (.*)$', line )
if m:
name = m.group(1)
filn = m.group(2)
n = re.search( r'l(\d+)r(\d+)', filn)
if n:
lc = int(n.group(1))
rc = int(n.group(2))
'''
if True or platform.node() == "scootaloo" or platform.node() == "rarity" or platform.node() == "pipsqueak" or platform.node() == "cheerilee":
    glog.info("Loading classifiers: "+tserver)
    try:
        for i in range(procs): 
            s1=TServers("localhost", 2000) #NB port number is hardcoded here...
            with open(tserver, "r") as f:
                for line in f:
                    if line[0] != "#":
                        bits = line.split()
                        try:
                            tmp = Classifier( bits[0], int(bits[2]), int(bits[3]), int(bits[4]), s1)
                            tmp.id = bits[1]
                            s1.add_classifier( tmp )
                        except:
                            glog.info("Error in tserver: ["+line[:-1]+"]")
            servers.append( s1 )
    except:
        glog.error("Help")
        raise
        sys.exit(1)
    glog.info( servers[0].info_str() ) #just the one
    
else: #local macbook defs
    try:
        for i in range(procs):
            s1=TServers("localhost",2000)
            
            if tserver == "000":
                # timblserver --config=tserver_000.ini --daemonize=no
                # Determiner PosNeg classifer for REDUNDANT DET
                WORDPRED=Classifier("WORDPRED", 2, 2, 0, s1) # normal l2r2 predictor
                WORDPRED.id="WORDPRED"
                s1.add_classifier(WORDPRED)
            else:
                glog.error("ERROR: Specify valid timblserver config! (-S 000)")
                sys.exit(1)
                servers.append( s1 )
    except KeyError:
        glog.error("Help")
        sys.exit(1)
glog.info( "Timblservers initialized.")

if info_only:
    sys.exit(0)
    
if test:    
    glog.error(repr(test_words))
    for ts in servers[0:1]:
        glog.error("t="+repr(ts))
        wa = ts.window_around(test_words,test_pos)
        for c in ts.classifiers:
            if test_c_id == None or test_c_id == c.id:
                glog.error("        "+c.id+"/"+c.name+"/"+str(c.type))
                glog.error(repr(wa[c.ctx])+" :"+str(len((wa[c.ctx]))))
                res = c.classify_i(wa[c.ctx])
                if c.error:
                    glog.error("RETURNED ERROR")
                    #glog.error(repr(res))
                ans = ans_to_dict( res )
                glog.error(repr(ans))
                glog.error(repr(c.in_distr("the")))
    sys.exit(2)

# Open outfile
if not afile:
    glog.error( "Need input file." )
    sys.exit(1)

if outfile:
  afile_out = outfile
else:
  # local file
  f_path, f_name = os.path.split(afile)
  if True or cmd[0:4] == "corr" or cmd[0:2] == "pr" or cmd[0:3] == "cst" or cmd[0:3] == "hoo":
    if not id_str:
      afile_out = f_name+".sc"
    else:
      afile_out = f_name+"_"+id_str+".sc"
  else:
    afile_out = f_name+".out"
    #afile_out = afile+".out"
if not force and os.path.exists(afile_out):
  glog.info("File exists: "+afile_out)
  glog.info("Specify -F to overwrite.")
  sys.exit(1)
glog.info("Output in "+afile_out)

all_files = []
if dirmode: #not implemented yet
    # Find all
    test     = re.compile("txt$", re.IGNORECASE)
    files = os.listdir( the_dir )
    files = filter(test.search, files)    
    for a_file in files:
        all_files.append( the_dir + a_file)
else:
    all_files.append( afile )

"""
Read input file and put content on queues for processing. 
The queue entry is a tuple: (line-nr, line, cmd)
Process per line or per instance? Parameter? Depend on cmd?
"""
if os.path.exists(afile):
    input_lines = 0
    if afile != None:
        f = open(afile, "r")
        input_lines = 0
        for line in f:
            l = line[:-1]
            if len(l) > 0:
                q.put( (input_lines, l, cmd, []) )
                input_lines += 1
            else:
                glog.info( "WARNING: short line "+str(input_lines)+" ["+l+"]")
                sys.exit(8)
        f.close()
else:
   glog.error("ERROR: cannot read input file.")
   sys.exit(8)
    
# Filled by file or from test
glog.info("Queue filled with "+str(input_lines)+" lines.")

"""
Read vk file
"""
vk = None
if vk_file and os.path.exists(vk_file):
    vk = []
    f = open(vk_file, "r")
    vk_lines = 0
    for line in f:
        l = line[:-1]
        if len(l) > 0:
            vk_lines += 1
            vk.append(l)
        else:
            glog.info( "WARNING: short line "+str(input_lines)+" ["+l+"]")
            sys.exit(8)
    f.close()
if vk:
    glog.info( "VK file: "+str(vk_lines)+" lines." )
    
if not info_gap:
    info_gap = input_lines // 10 # 10*procs for write info?
if info_gap < 1:
    info_gap = 1 

"""
Start the Threads. They will all point to the same timblserver.
"""
for i in range(procs):
    t = myThread("T{:02n}".format(i), i ) #i points to servers[i]
    workers.append(t)
    t.daemon = True
    t.start()

td0 = int(time.time())

# Open the output file
fo = open( afile_out, "w" )

"""

HERE we proces the results from the queue.

"""
# Keep reading, because of order issues, we keep
# procs "distance" from the end of the queue, the
# item[0] from the tuples is the print index, which
# should be equal to the print_idx to get the order
# right. Put item back on queue if out of order.
print_idx   = 0
gap         = 1 #Gap lets the result queue fill before taking items from it.
last_r_size = 0
stuck_cnt   = 0
stats = {} #{ 'W_REP':0, 'V_REP':0, 'N_REP':0, 'DETS_REP':0, 'DETS_RED':0, 'DETS_MIS':0, 'NOP':0, 'PREPS_REP':0, 'PREPS_RED':0, 'PREPS_MIS':0, 'OTHER':0 }

while any( [ t.isAlive() for t in workers ] ):
    if r.qsize() > gap:
        """
        r.put( (idx, [(0, tmp)], self.stats) )
        The result is a tuple (line-nr, [(result_str)], stats)
        The second element is a list with tuples.
        Third is stats.
        """
        res = r.get() #check for empty? not if we use gap
        if print_idx != res[0]: #res[0] is the index of the line
                                #glog.error( "Print_idx out of order, "+str(print_idx)+" vs "+str(res[0])+" ("+str(r.qsize())+")" )
            r.put( res ) #put back and wait
            time.sleep(1) #maybe longer?
        else:
            res_list = res[1] #res[1] is list of tuples (i,str)
            res_stat = res[2] #dict with stats
            for s in res_stat:
                try:
                    stats[s] += res_stat[s]
                except KeyError:
                    stats[s] = res_stat[s]
            #print res_list[0] 
            fo.write( str(res_list[0][1])+"\n" )
            fo.flush()
            td1 = int(time.time())
            td = td1-td0
            print_idx += 1
            #calculate time left from q.qsize, not r.qsize !
            if print_idx % info_gap == 0:
                persec = float(float(td)/float(print_idx+r.qsize())) #printed + left on queue but ready
                left = int( persec * (q.qsize()+len([ 1 for t in workers if t.isAlive() ])) )
                glog.info(  "Wrote line "+str(print_idx)+", time taken: %s (%s left)", str(datetime.timedelta(seconds=td)),  str(datetime.timedelta(seconds=left)) )
    else:
        time.sleep(1) #wait for r.queue to be filled
    if r.qsize() == last_r_size:
        #list [ for t.cnt for t in thread ] - [the same last time] => any 0?
        #glog.error( "Queue not changing? ("+str(last_r_size)+")" )
        stuck_cnt += 1
        if stuck_cnt >40:
            glog.error( "Result queue not changing? ("+str(last_r_size)+" in queue)" )
            stuck_cnt = 0
    else:
        stuck_cnt = 0
    last_r_size = r.qsize()

glog.info( "All threads exited." )

# the rest of the result, order is OK now 
while r.qsize() > 0:
    res = r.get() # (idx, [list-with-tuples])
    res_list = res[1] #res[1] is list of tuples (i,str)
    res_stat = res[2] #dict with stats
    for s in res_stat:
        try:
            stats[s] += res_stat[s]
        except KeyError:
            stats[s] = res_stat[s]
    #print res_list[0] 
    fo.write( str(res_list[0][1])+"\n" )
    fo.flush()
    td1 = int(time.time())
    td = td1-td0
    print_idx += 1
    #calculate time left from q.qsize, not r.qsize !
    if print_idx % info_gap == 0:
        persec = float(float(td)/float(print_idx+r.qsize())) #printed + left on queue but ready
        left = 0
        glog.info( "Wrote line "+str(print_idx)+", time taken: %s (%s left)", str(datetime.timedelta(seconds=td)),  str(datetime.timedelta(seconds=left)) )

fo.close()

glog.setLevel(logging.DEBUG)
td1 = int(time.time())
td = td1-td0
glog.debug( "Result Queue contains: "+str(r.qsize()) )
total_cnt = 0
for w in workers:
    glog.debug( str(w.name)+" processed "+str(w.cnt)+ " instances." )
    total_cnt += w.cnt
glog.info("Time taken: %s", str(datetime.timedelta(seconds=td)))
glog.info( "Processed "+str(total_cnt)+ " instances, in "+str(procs)+" threads." )
if total_cnt == 0:
  sys.exit(1)
tdw = float(float(td)/float(total_cnt))
#scootaloo, -p24: Time per word: 0.0596267637688 (16 p/s)
glog.info("Time per instance: %s", str(tdw))
glog.info( "Output in "+afile_out )
glog.info( repr(stats) )
glog.info("See "+logfile+" for debug info.")
#rough guess of how to score:
print
print "python ./release3.0/m2scorer/scripts/m2scorer.py -v",afile_out,afile+".m2 >",afile_out+".score"
sys.exit(0)
