#!/usr/bin/env python2

import sys
import getopt
import ast
import json
from time import time
from math import log
from pprint import pprint

# Define constants
DIRTY_EVICTION = 1
LOAD_MISS = 2
STORE_MISS = 3
LOAD_HIT = 4
STORE_HIT = 5

class Block:
    """ Block contains the necesary information to do 
    the replacements, and also holds information about the 
    data as Tag, Dirty Evictions, and so. A block might
    also be called a Line. """

    def __init__(self, tag=0, dbit=0, rh=0):
        self._tag = tag
        self._dirty_bit = dbit
        self._replacement_helper = rh
        self._pos = 0
        
    def add(self, tag):
        self._tag = tag

    def get_tag(self):
        return self._tag

    def set_dirty(self, dirty_bit):
        self._dirty_bit = dirty_bit

    def get_dirty(self):
        return self._dirty_bit
        
    def set_rpbit(self, replacement_helper):
        self._replacement_helper = replacement_helper

    def incr_rpbit(self):
        self._replacement_helper += 1
        
    def get_rpbit(self):
        return self._replacement_helper

    def set_pos(self, pos):
        self._pos = pos

    def get_pos(self):
        return self._pos

    def incr_pos(self, pos):
        self._pos += 1

    def __repr__(self):
        return str(self.__dict__)
        
class Sets:
    """ Sets are the different blocks related to 
    one index in a cache. Size defines how many 
    blocks are, and also you need to define the replacement policy 
    in order to work """

    def __init__(self, asociativity, replacement_policy):
        self._asociativity = asociativity
        self._replacement_policy = replacement_policy
        self._structure = {}
        self._full = False

    def _update_free(self):
        """ Updates the full variable according to 
        the free space available in the sets. """
        
        if len(self._structure) >= self._asociativity:
            self._full = True
        else:
            self._full = False

    def _update_rpbit(self):
        if self._replacement_policy == "LRU":
            for each_block in self._structure:
                self._structure[each_block].incr_rpbit()
        if self._replacement_policy == "NRU":
            for each_block in self._structure:
                self._structure[each_block].set_rpbit(1)
                
    def _get_highrpbit(self):
        temp = Block()
        for each_block in self._structure:
            if temp.get_rpbit() < self._structure[each_block].get_rpbit():
                temp = self._structure[each_block]

        return temp # return block with highest rpbit

    def _get_firsthighrpbit(self):
        temp = Block()
        temp.set_pos(len(self._structure)+1) #set pos to be higher than the last
        for each_block in self._structure:
            if self._structure[each_block].get_rpbit() == 1:
                if temp.get_pos() > self._structure[each_block].get_pos():
                    if self._structure[each_block].get_tag() != 0:
                        temp = self._structure[each_block]

        return temp # return block with lowest pos

    def _lru(self, tag, ls, result):
        """ Logic for the LRU replacement policy. """

        self._update_rpbit()
        
        if tag in self._structure: # is in cache?
            self._structure[tag].set_rpbit(0)
            if ls == 0:
                result.append(LOAD_HIT)
            elif ls == 1:
                self._structure[tag].set_dirty(1)
                result.append(STORE_HIT)
                
            return result
            
        else: # is NOT in cache
            if not self._full: # theres free space
                if ls == 0:
                    self._structure[tag] = Block(tag, 0, 0)
                    result.append(LOAD_MISS)
                elif ls == 1:
                    self._structure[tag] = Block(tag, 1, 0) # gets in dirty
                    result.append(STORE_MISS)
                self._update_free() # update free space
                return result

            else: # theres no free space
                eviction_block = self._get_highrpbit()
                if eviction_block.get_dirty() == 1: # check if eviction is dirty
                    result.append(DIRTY_EVICTION)
                self._structure.pop(eviction_block.get_tag()) # evict
                
                if ls == 0:
                    result.append(LOAD_MISS)
                    self._structure[tag] = Block(tag, 0, 0)
                elif ls == 1:
                    result.append(STORE_MISS)
                    self._structure[tag] = Block(tag, 1, 0)
                return result

    def _nru(self, tag, ls, result):
        """ Replacement policy for NRU """

        if tag in self._structure: # is in cache?
            self._update_rpbit()
            self._structure[tag].set_rpbit(0)
            if ls == 0:
                result.append(LOAD_HIT)
            elif ls == 1:
                self._structure[tag].set_dirty(1)
                result.append(STORE_HIT)
                
            return result

        else: # is NOT in cache
            if not self._full: # theres free space
                self._update_rpbit()
                if ls == 0:
                    self._structure[tag] = Block(tag, 0, 0)
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(LOAD_MISS)
                elif ls == 1:
                    self._structure[tag] = Block(tag, 1, 0) # gets in dirty
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(STORE_MISS)
                self._update_free() # update free space
                return result

            else: # theres no free space
                eviction_block = self._get_firsthighrpbit()
                if eviction_block.get_dirty() == 1: # check if eviction is dirty
                    result.append(DIRTY_EVICTION)

                temp_pos = eviction_block.get_pos() # save the pos of this block
                self._structure.pop(eviction_block.get_tag()) # evict

                self._update_rpbit()
                    
                if ls == 0:
                    result.append(LOAD_MISS)
                    self._structure[tag] = Block(tag, 0, 0)
                    self._structure[tag].set_pos(temp_pos)
                elif ls == 1:
                    result.append(STORE_MISS)
                    self._structure[tag] = Block(tag, 1, 0)
                    self._structure[tag].set_pos(temp_pos)
                return result

    def access(self, tag, ls):
        """ Access is the method that arranges the data structure
        with each call for memory. ls is 0 for load and 1 for store. 
        In load, you must see if its a hit or miss based on if its 
        or not in the cache. If its not, then you should bring it 
        to cache, and evict data if theres no free space in cache.
        Dirty evictions are when a data was modified with store, 
        and then sent to principal memory. Only should look for them
        when evicting a data. If theres free space you only add the 
        data. """

        result = []
        
        ls = int(ls)
        
        if self._replacement_policy == "LRU":
            result = self._lru(tag, ls, result)
                    
        elif self._replacement_policy == "NRU":
            result = self._nru(tag, ls, result)
    
        else:
            raise TypeError("The replacement Policy you asked for is not implemented: "+str(self._replacement_policy))

        return result
                
    def __repr__(self):
        """ Representation for cache printing. """
        return str(self._structure)
                
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
        
        for each_index in range(0, pow(2,self._index_size)):
            # cache structure is going to be a dict for the index, with each way inside
            self._cache[bin(each_index)[2:].zfill(self._index_size)] = Sets(self._asociativity, self._replacement_policy)

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

        result = self._cache[index].access(tag, ls) # access this cache index
        
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
              'memory_access' : '',
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

        # count exection time
        if LOAD_HIT in result or LOAD_MISS in result:
            output['execution_time'] += 1 + int(options['miss_penalty'])
        else:
            output['execution_time'] += 1

        if debug:
            print "Flags Raised: " + str(result)
            print "\nCache Content: "
            print_cache(str(cache))
            print

    output['total_misses'] = output['load_misses'] + output['store_misses']
    output['total_hits'] = output['load_hits'] + output['store_hits']
        
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
    print "Cache Block Size (Bytes):\t" + str(result['asociativity'])
    print "Cache Replacement Policy:\t" + str(result['replacement_policy'])
    print "Miss Penalty (Cycles):\t\t" + str(result['miss_penalty'])
    print "---------------------------------------------"
    print "Simulation results"
    print "---------------------------------------------"
    print "Execution time (cycles):\t" + str(result['execution_time'])
    print "Instructions:\t\t\t" + str(result['instructions'])
    print "Memory Access:\t\t" + str(result['memory_access'])
    print "Overall miss rate:\t\t" + str(result['overall_miss_rate'])
    print "Read miss rate:\t\t" + str(result['read_miss_rate'])
    print "Avg. mem. access time (cyc):\t" + str(result['avg_memory_access_time'])
    print "Dirty Evictions:\t\t" + str(result['dirty_evictions'])
    print "Load misses:\t\t\t" + str(result['load_misses'])
    print "Store misses:\t\t\t" + str(result['store_misses'])
    print "Total misses:\t\t\t" + str(result['total_misses'])
    print "Load hits:\t\t\t" + str(result['load_hits'])
    print "Store hits:\t\t\t" + str(result['store_hits'])
    print "Total hits:\t\t\t" + str(result['total_hits'])
    print "---------------------------------------------"
    
def main(argv):
    start_time = time()
    
    options = {'cache_size' : '',
               'line_size' : '',
               'asociativity' : '',
               'replacement_policy' : '',
               'miss_penalty' : '',
               'debug' : False
    }
    
    try:
        opts, args = getopt.getopt(argv, "t:l:a:h", ["rp=", "mp=", "debug"])
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

    for each_option in options:
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
            



