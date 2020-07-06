from log_stuff import init_logger

log = init_logger()

class Quadrant:
    def __init__(self, w, h, id):
        self.w = w
        self.h = h
        self.id = id
        self.stars = []
    
    def add_star(self, star):
        self.stars.append(star)
    
    def adjust_coordinates(self, w, h):
        return w + self.w, h + self.h
    
class Star:
    _id_next = 0
    _star_db = {}
    
    @classmethod
    def get_star_by_id(cls, id):
        return cls._star_db[id]
    
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
        if not self.is_master:
            self.quadrant = quadrant
            self.size     = self.master_star.size
            self.w        = self.master_star.w + self.quadrant.w
            self.h        = self.master_star.h + self.quadrant.h
            self.color    = self.master_star.color
            self.childs   = None
            self.master_star.add_child(self)
            self.quadrant.add_star(self)
        else:
            self.size     = size
            self.w        = w
            self.h        = h
            self.color    = color
            self.childs   = []
            self.quadrant = None
        self.taken = False
        
    def __str__(self):
        return "Star %i (%s, %s) at %i,%i, size %.3f"%(self.id, 
                                                 "master" if self.is_master else "child@%s"%(self.quadrant.id,),
                                                 "taken" if self.taken else "free",
                                                 self.w,
                                                 self.h, 
                                                 self.size)
        
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