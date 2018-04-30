import random
from block import Block

# Define constants
DIRTY_EVICTION = 1
LOAD_MISS = 2
STORE_MISS = 3
LOAD_HIT = 4
STORE_HIT = 5

class Sets:
    """ Sets are the different blocks related to 
    one index in a cache. Size defines how many 
    blocks are, and also you need to define the replacement policy 
    in order to work """

    def __init__(self, asociativity, replacement_policy, m=1):
        self._asociativity = asociativity
        self._replacement_policy = replacement_policy
        self._m = m #only used if replacement policy is srrip
        rpdict = {"LRU":self._lru, "NRU":self._nru, "SRRIP":self._srrip, "RANDOM":self._random} # Function to use for replacement
        self._rppolicy = rpdict[self._replacement_policy] # Define the function to use when replacing
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
        if self._replacement_policy == "LRU" or self._replacement_policy == "SRRIP":
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

    def _get_firsthighrpbit(self, wanted_rpbit):
        """ This is a helper function for the NRU replacement
        policy. The idea is that if there's a first 1, the return that
        block. If this block returns a block with tag 0, it didn't find
        anything. """

        temp = Block() # Make a helper block to compare
        temp.set_pos(len(self._structure)+1) #set pos to be higher than the last

        for each_block in self._structure:
            if self._structure[each_block].get_rpbit() == wanted_rpbit:
                if temp.get_pos() > self._structure[each_block].get_pos():
                    if self._structure[each_block].get_tag() != 0:
                        temp = self._structure[each_block]

        return temp # return block with lowest pos

    def _get_random(self):
        """ Return a random block inside the structure """

        random_block = random.choice(self._structure.keys())
        return self._structure[random_block]
        
    
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
                    self._structure[tag] = Block(tag, 0, 0) # first values enter with nrubits = 1
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(LOAD_MISS)
                elif ls == 1:
                    self._structure[tag] = Block(tag, 1, 0) # gets in dirty and nrubit = 1
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(STORE_MISS)
                self._update_free() # update free space
                return result

            else: # theres no free space
                eviction_block = self._get_firsthighrpbit(1)

                if eviction_block.get_tag() == 0: # Theres no block with rpbit == 1
                    self._update_rpbit() # set all rpbits to 1
                    eviction_block = self._get_firsthighrpbit(1) # try again
                
                if eviction_block.get_dirty() == 1: # check if eviction is dirty
                    result.append(DIRTY_EVICTION)

                temp_pos = eviction_block.get_pos() # save the pos of this block
                self._structure.pop(eviction_block.get_tag()) # evict
                
                if ls == 0:
                    result.append(LOAD_MISS)
                    self._structure[tag] = Block(tag, 0, 0)
                    self._structure[tag].set_pos(temp_pos)
                elif ls == 1:
                    result.append(STORE_MISS)
                    self._structure[tag] = Block(tag, 1, 0)
                    self._structure[tag].set_pos(temp_pos)
                return result

    def _srrip(self, tag, ls, result):
        """ Replacement policy for SRRIP. Very similar to nru 
        but with 2^M statues."""

        m = self._m # only for simplicity
        self._enter_pos = pow(2, m) - 2
        self._search_pos = pow(2, m) - 1
        
        if tag in self._structure: # is in cache?
            self._structure[tag].set_rpbit(0) # set rrpv to 0
            if ls == 0:
                result.append(LOAD_HIT)
            elif ls == 1:
                self._structure[tag].set_dirty(1) #  if store set dirty
                result.append(STORE_HIT)
                
            return result

        else: # is NOT in cache
            if not self._full: # theres free space
                if ls == 0:
                    self._structure[tag] = Block(tag, 0, self._enter_pos) # rrpv enters in 2
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(LOAD_MISS)
                elif ls == 1:
                    self._structure[tag] = Block(tag, 1, self._enter_pos) # gets in dirty rrpv enters in 2
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(STORE_MISS)
                self._update_free() # update free space
                return result

            else: # theres no free space
                eviction_block = self._get_firsthighrpbit(self._search_pos)

                while eviction_block.get_tag() == 0: # Theres no block with rpbit == 2^m-1
                    self._update_rpbit() # increment rppv
                    eviction_block = self._get_firsthighrpbit(self._search_pos) # try again
                
                if eviction_block.get_dirty() == 1: # check if eviction is dirty
                    result.append(DIRTY_EVICTION)

                temp_pos = eviction_block.get_pos() # save the pos of this block
                self._structure.pop(eviction_block.get_tag()) # evict
                
                if ls == 0:
                    self._structure[tag] = Block(tag, 0, self._enter_pos)
                    self._structure[tag].set_pos(temp_pos)
                elif ls == 1:
                    self._structure[tag] = Block(tag, 1, self._enter_pos)
                    self._structure[tag].set_pos(temp_pos)
                return result

    def _random(self, tag, ls, result):
        """ Implement a replacement policy, where on miss, 
        the cache replaces a random block. """

        if tag in self._structure: # is in cache
            if ls == 0:
                result.append(LOAD_HIT)
            elif ls == 1:
                self._structure[tag].set_dirty(1) #  if store set dirty
                result.append(STORE_HIT)
                
            return result

        else: # is NOT in cache
            if not self._full: # theres free space
                if ls == 0:
                    self._structure[tag] = Block(tag) # only tag is used
                    result.append(LOAD_MISS)
                elif ls == 1:
                    self._structure[tag] = Block(tag) # only tag is used
                    result.append(STORE_MISS)
                self._update_free() # update free space
                return result

            else: # theres no free space
                eviction_block = self._get_random() # get a random eviction block

                if eviction_block.get_dirty() == 1: # check dirt eviction
                    result.append(DIRTY_EVICTION)

                self._structure.pop(eviction_block.get_tag()) # evict
                
                if ls == 0:
                    result.append(LOAD_MISS)
                    self._structure[tag] = Block(tag)
                elif ls == 1:
                    result.append(STORE_MISS)
                    self._structure[tag] = Block(tag)
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
        data. M is for the SRRIP implementation"""

        result = []
        ls = int(ls)

        result = self._rppolicy(tag, ls, result) # this is defined at the beginning

        return result
                
    def __repr__(self):
        """ Representation for cache printing. """
        return str(self._structure)
