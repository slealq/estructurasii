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

    def _get_firsthighrpbit(self):
        """ This is a helper function for the NRU replacement
        policy. The idea is that if there's a first 1, the return that
        block. If this block returns a block with tag 0, it didn't find
        anything. """

        if self._replacement_policy == "NRU":
            wanted_rpbit = 1
        elif self._replacement_policy == "SSRIP":
            wanted_rpbit = pow(2, self._m-1) # set the wanted rpbit to be 2^m-1

        temp = Block() # Make a helper block to compare
        temp.set_pos(len(self._structure)+1) #set pos to be higher than the last
        if self._replacement_policy == "NRU":
            for each_block in self._structure:
                if self._structure[each_block].get_rpbit() == wanted_rpbit:
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
                eviction_block = self._get_firsthighrpbit()

                if eviction_block.get_tag() == 0: # Theres no block with rpbit == 1
                    self._update_rpbit() # set all rpbits to 1
                    eviction_block = self._get_firsthighrpbit() # try again
                
                if eviction_block.get_dirty() == 1: # check if eviction is dirty
                    result.append(DIRTY_EVICTION)

                temp_pos = eviction_block.get_pos() # save the pos of this block
                self._structure.pop(eviction_block.get_tag()) # evict
                
                eviction_block 
                    
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
                    self._structure[tag] = Block(tag, 0, pow(2, m-2)) # rrpv enters in 2
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(LOAD_MISS)
                elif ls == 1:
                    self._structure[tag] = Block(tag, 1, pow(2, m-2)) # gets in dirty rrpv enters in 2
                    self._structure[tag].set_pos(len(self._structure))
                    result.append(STORE_MISS)
                self._update_free() # update free space
                return result

            else: # theres no free space
                eviction_block = self._get_firsthighrpbit()

                if eviction_block.get_tag() == 0: # Theres no block with rpbit == 2^m-1
                    self._update_rpbit() # increment rppv
                    eviction_block = self._get_firsthighrpbit() # try again
                
                if eviction_block.get_dirty() == 1: # check if eviction is dirty
                    result.append(DIRTY_EVICTION)

                temp_pos = eviction_block.get_pos() # save the pos of this block
                self._structure.pop(eviction_block.get_tag()) # evict
                
                eviction_block 
                    
                if ls == 0:
                    result.append(LOAD_MISS)
                    self._structure[tag] = Block(tag, 0, pow(2,m-2))
                    self._structure[tag].set_pos(temp_pos)
                elif ls == 1:
                    result.append(STORE_MISS)
                    self._structure[tag] = Block(tag, 1, pow(2,m-2))
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
        data. M is for the SRRIP implementation"""

        result = []
        
        ls = int(ls)
        
        if self._replacement_policy == "LRU":
            result = self._lru(tag, ls, result)
                    
        elif self._replacement_policy == "NRU":
            result = self._nru(tag, ls, result)

        elif self._replacement_policy == "SRRIP":
            result = self._srrip(tag, ls, result)
    
        else:
            raise TypeError("The replacement Policy you asked for is not implemented: "+str(self._replacement_policy))

        return result
                
    def __repr__(self):
        """ Representation for cache printing. """
        return str(self._structure)
