#!/usr/bin/env python2

import sys
import getopt
import ast
import json
from time import time
from math import log
from pprint import pprint
from sets import *
                
class Cache:
    """ Define the $ object so that replacement policies are done
    faster. Also here will be stored the data. """
    def __init__(self, options):
        self._cache_size = pow(2,10) * float(options['cache_size'])
        self._line_size = int(options['line_size'])
        self._asociativity = int(options['asociativity'])
        self._replacement_policy = options['replacement_policy']
        self._lines = self._cache_size / (self._line_size * self._asociativity) # lines per set
        self._index_size = int(log(self._lines, 2))
        self._offset_size = int(log(self._line_size, 2))
        self._cache = {}
        self._m = int(options['m']) # this value is only used for srrip
        
        for each_index in range(0, pow(2,self._index_size)):
            # cache structure is going to be a dict for the index, with each way inside
            self._cache[bin(each_index)[2:].zfill(self._index_size)] = Sets(self._asociativity, self._replacement_policy, self._m)

    def _get_params(self, bin_num):
        """ Returns the tag, index, offset of an address. bin_num is 
        expected to be a string. """
        tag = bin_num[:(len(bin_num)-self._index_size-self._offset_size)]
        index = bin_num[(len(bin_num)-self._index_size-self._offset_size) : (len(bin_num)-self._offset_size)]
        offset =  bin_num[(len(bin_num)-self._offset_size) : ]

        return tag, index, offset
        
    def _2bin(self, num, base=16, size=32):
        """ Convert a num value to its binary representation in str.
        base is the base of the number.
        size is the expected size of the returned value.
        usage: _hex2bin("301a75e9") should return 00110000000110100111010111100000 """

        return bin(int(num, base))[2:].zfill(size) # chop the first two items and resize
        
    def write(self, address, ls, debug):
        """ Write a specific address given. The algoritm behind 
        depends on the replacement policy. 
        ls value is load = 0, store = 1
        """

        if debug:
            print "Process address: " + str(address)
            print "Hexadecimal representation: " + str(self._2bin(address, 16, len(address)*4))

        tag, index, offset = self._get_params(self._2bin(address, 16, len(address)*4))

        if debug:
            print "Action: " + str(ls)
            print "Index size: " + str(self._index_size)
            print "Offset size: " + str(self._offset_size)
            print "Tag, Index, Offset: "
            print (tag, index, offset)
            print "Before: \n"
            print_cache(str(self._cache[index]))
            print "\n"
            
        result = self._cache[index].access(tag, ls) # access this cache index
        if debug:
            print "After:\n"
            print_cache(str(self._cache[index]))
            print "\n"
                
        return result
            
    def __str__(self):
        return str(self._cache)

def print_cache(cache_string):
    """ Helper function to print cache contents for debuggins. """
    json_data = ast.literal_eval(cache_string)
    pprint(json_data)

def start_simulation(data, options):
    """ Parse an input file given to the script by using stdin 
    to see the result of the mem access.
    options is used to define the cache size and properties such as 
    the replacement policy.
    usage: parse_input(sys.stdin.readlines(), options) for example. """

    output = {'instructions':0,
              'execution_time':0,
              'load_misses':0,
              'load_hits':0,
              'store_misses':0,
              'store_hits':0,
              'dirty_evictions':0,
              'memory_access' : 0,
              'overall_miss_rate' : '',
              'read_miss_rate' : '',
              'avg_memory_access_time' : '',
              'total_misses' : '',
              'total_hits' : ''
    }

    debug = options["debug"] # activate debugger mode

    cache = Cache(options)
    
    for each_line in data:
        parts = each_line.split()
        output['instructions'] += int(parts[-1]) # the last value in line is the ic
        output['memory_access'] += 1
        result = cache.write(parts[2], parts[1], debug)

        if LOAD_MISS in result:
            output['load_misses'] += 1
        if LOAD_HIT in result:
            output['load_hits'] += 1
        if STORE_MISS in result:
            output['store_misses'] += 1
        if STORE_HIT in result:
            output['store_hits'] += 1
        if DIRTY_EVICTION in result:
            output['dirty_evictions'] += 1



        # if debug mode is enabled
        if debug:
            print "Flags Raised: " + str(result)
            

    output['total_misses'] = output['load_misses'] + output['store_misses']
    output['total_hits'] = output['load_hits'] + output['store_hits']
    output['execution_time'] = (output['instructions'] +
                                int(options['miss_penalty'])*output['load_misses'])
    output['overall_miss_rate'] = float(output['total_misses'])/float(output['memory_access'])
    output['read_miss_rate'] = float(output['load_misses'])/float(output['load_hits']+output['load_misses'])
    # Note that all hits take 1 clock cycle (for load and for store
    output['avg_memory_access_time'] = 1 + output['overall_miss_rate']*float(options['miss_penalty'])
    
    return dict(output, **options)

def print_results(result):
    """ Given a result dictionary, with all necesary information
    print the content of the dictionary. 
    usage: print_results(dictionary). """

    print "---------------------------------------------"
    print "Cache parameters"
    print "---------------------------------------------"
    print "Cache Size (KB):\t\t" + str(result['cache_size'])
    print "Cache Asociativiy:\t\t" + str(result['asociativity'])
    print "Cache Block Size (Bytes):\t" + str(result['line_size'])
    print "Cache Replacement Policy:\t" + str(result['replacement_policy'])
    print "Miss Penalty (Cycles):\t\t" + str(result['miss_penalty'])
    print "---------------------------------------------"
    print "Simulation results"
    print "---------------------------------------------"
    print "Execution time (cycles):\t" + "{:,}".format(result['execution_time'])
    print "Instructions:\t\t\t" + "{:,}".format(result['instructions'])
    print "Memory Accesses:\t\t" + "{:,}".format(result['memory_access'])
    print "Overall miss rate:\t\t" + str(result['overall_miss_rate'])
    print "Read miss rate:\t\t\t" + str(result['read_miss_rate'])
    print "Avg. mem. access time (cyc):\t" + str(result['avg_memory_access_time'])
    print "Dirty Evictions:\t\t" + "{:,}".format(result['dirty_evictions'])
    print "Load misses:\t\t\t" + "{:,}".format(result['load_misses'])
    print "Store misses:\t\t\t" + "{:,}".format(result['store_misses'])
    print "Total misses:\t\t\t" + "{:,}".format(result['total_misses'])
    print "Load hits:\t\t\t" + "{:,}".format(result['load_hits'])
    print "Store hits:\t\t\t" + "{:,}".format(result['store_hits'])
    print "Total hits:\t\t\t" + "{:,}".format(result['total_hits'])
    print "---------------------------------------------"
    
def main(argv):
    start_time = time()
    
    options = {'cache_size' : '',
               'line_size' : '',
               'asociativity' : '',
               'replacement_policy' : '',
               'miss_penalty' : '',
               'debug' : False,
               'm' : 1
    }
    
    try:
        opts, args = getopt.getopt(argv, "t:l:a:m:h", ["rp=", "mp=", "debug"])
    except getopt.GetoptError:
        print 'cache.py -t <CacheSize(KB)> -l <LineSize(Bytes)> -a <Asociativity> --rp<LRU, NRU, SRRIP, Random> --mp <MissPenalty>'
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            print 'cache.py -t <CacheSize(KB)> -l <LineSize(Bytes)> -a <Asociativity> --rp<LRU, NRU, SRRIP, Random> --mp <MissPenalty>'
            sys.exit(2)
        elif opt == "-t":
            options['cache_size'] = arg
        elif opt == "-l":
            options['line_size'] = arg
        elif opt == "-a":
            options['asociativity'] = arg
        elif opt == "--rp":
            options['replacement_policy'] = arg
        elif opt == "--mp":
            options['miss_penalty'] = arg
        elif opt == "--debug":
            options["debug"] = True
        elif opt == "-m":
            options["m"] = arg

    for each_option in options:
        if each_option == 'm':
            continue # m is not always wanted
        if options[each_option] == '':
            raise SyntaxError('One argument was not given. Use ./cache.py -h for help.')
        if each_option != "replacement_policy" :
            if not unicode(options[each_option]).isnumeric():
                #raise ValueError("One of the arguments is not a valid number")
                pass
                
    result = start_simulation(sys.stdin.readlines(), options)
    print_results(result)
    print "\nElapsed time: " + str(time() - start_time)
    
if __name__ == "__main__":
    main(sys.argv[1:])
            



