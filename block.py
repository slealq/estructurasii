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
