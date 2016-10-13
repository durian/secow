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

def overlap(s0, s1):
    for i in xrange(0, len(s0)+1):
        o = s1.startswith(s0[0:i])
        print i, s0[0:i]
        if not o:
            max = i-1
            #(common, extra-s0, extra-s1)
            return (s0[0:max], s0[max:], s1[max:])

print overlap("avsett", "avsed")
