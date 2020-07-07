from .log_stuff import init_logger

log = init_logger()

class Star:
    _id_next = 0
    _star_db = {}
    
    def __init__(self, 
                 size = None, 
                 w = None, 
                 h = None, 
                 color = None,
                 master_star = None,
                 quadrant = None):
        self.id = Star._id_next
        Star._id_next += 1
        self._star_db[self.id] = self
        
        self.master_star = master_star
        self.is_master = master_star == None
        self.quadrant = quadrant
        self.quadrant.add_star(self)
        if not self.is_master:
            self.size     = self.master_star.size
            self.w        = self.master_star.base_w + self.quadrant.w
            self.h        = self.master_star.base_h + self.quadrant.h
            self.color    = self.master_star.color
            self.childs   = None
            self.master_star.add_child(self)
        else:
            self.size     = size
            self.w        = w + (0 if self.quadrant == None else self.quadrant.w)
            self.h        = h + (0 if self.quadrant == None else self.quadrant.h)
            self.base_w   = w
            self.base_h   = h
            self.color    = color
            self.childs   = []
        self.taken = False
        
    def get_rel_quadrant_to_other_star(self, other_star):
        return (self.quadrant.x - other_star.quadrant.x, self.quadrant.y - other_star.quadrant.y)
        
    def __str__(self):
        return "Star %i (%s, %s) at %i,%i, size %.3f"%(self.id, 
                                                 "master" if self.is_master else "child@%s"%(self.quadrant.id,),
                                                 "taken" if self.taken else "free",
                                                 self.w,
                                                 self.h, 
                                                 self.size)
    def get_peers(self):
        if self.is_master:
            peers = [self]
            peers.extend(self.childs)
        else:
            peers = self.master_star.get_peers()
        return peers
        
    def add_child(self, child):
        assert self.is_master
        self.childs.append(child)
    
    def take(self):
        if self.is_master:
            self.taken = True
            for child in self.childs:
                child.taken = True
        else:
            self.master_star.take()