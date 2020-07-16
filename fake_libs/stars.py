import random
from .log_stuff import init_logger
from .color import COLORS_FROM_START_INDEX

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
        self.constellation = None
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
            self.master_star = self
            self.size     = size
            self.w        = w + (0 if self.quadrant == None else self.quadrant.w)
            self.h        = h + (0 if self.quadrant == None else self.quadrant.h)
            self.base_w   = w
            self.base_h   = h
            self.color    = color
            self.childs   = []
        self.taken = False
        self.tag = None
        
        
    def set_color_index(self, color_index):
        self.color.set_star_color_index(color_index)
        return self.color.get_hex_rgb()
        
    def get_rel_quadrant_to_other_star(self, other_star):
        return (self.quadrant.x - other_star.quadrant.x, self.quadrant.y - other_star.quadrant.y)
        
    def __str__(self):
        return "Star %i (%s, %s) at %i,%i, size %.3f"%(self.id, 
                                                 "master" if self.is_master else "child@%s"%(self.quadrant.id,),
                                                 "taken" if self.taken else "free",
                                                 self.w,
                                                 self.h, 
                                                 self.size)
    
    def __repr__(self):
        return "<%s>"%(str(self),)
    
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
            
    def untake(self):
        self.constellation = None
        if self.is_master:
            self.taken = False
            for child in self.childs:
                child.taken = False
        else:
            self.master_star.untake()
            
def get_random_stars(min_size, 
                     max_size, 
                     max_w, 
                     max_h, 
                     star_count,
                     quadrant = None,
                     size_random_count = 0,
                     size_distribution_power = 1,
                     color = None):
                     
                     
    generated_stars = []
    size_range = max_size - min_size
    for i in range(0, star_count):
        # star size
        r = 1
        for j in range(0, size_random_count): r *= random.random()
        star_size = (r**size_distribution_power) * size_range + min_size
        
        w = random.random()*max_w
        h = random.random()*max_h
        
        star = Star(size = star_size,
                    w = w, 
                    h = h,
                    color = color.clone() if color != None else "#FFFFFF",
                    quadrant = quadrant)
        
        generated_stars.append(star)
    
    # Split the process in two loops to keep the random behavior for the same seed when random colors are enabled            
    for star in generated_stars:
        if star.color.color_name in COLORS_FROM_START_INDEX:
            star.set_color_index(_get_random_color_index())
    return generated_stars
            
def _get_random_color_index():
    # ci <-0.4,+2.0> 
    return random.random() * 2.4 - 0.4