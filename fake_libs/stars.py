import random
from .log_stuff import init_logger
from .color import COLOR_RANDOM_COLOR_INDEX

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
        self.tag = None
        
        
    def set_color_index(self, color_index):
        # color_index <-0.4,+2.0> 
        assert type(color_index) in (int, float)
        ci = float(color_index)
        if (ci < -0.4): 
            ci = -0.4 
        if (ci > 2.0):
            ci =  2.0
        # R
        if (( ci >= -0.40 ) and ( ci < 0.00 )):
            t = (ci + 0.40) / (0.00 + 0.40)
            r = 0.61 + (0.11 * t) + ( 0.1 * t * t)
        elif ((ci >= 0.00 ) and ( ci < 0.40)):
            t = (ci - 0.00) / (0.40 - 0.00)
            r = 0.83 + (0.17 * t)
        elif ((ci >= 0.40 ) and ( ci <= 2.10)):
            t = (ci - 0.40) / (2.10 - 0.40)
            r = 1.00
        #G
        if (( ci >= -0.40 ) and ( ci < 0.00 )):
            t = (ci + 0.40) / (0.00 + 0.40)
            g = 0.70 + (0.07 * t) + (0.1 * t * t )
        elif (( ci >= 0.00) and ( ci < 0.40)):
            t = (ci - 0.00) / (0.40 - 0.00)
            g = 0.87 + (0.11 * t)
        elif (( ci >= 0.40) and ( ci < 1.60)):
            t = (ci - 0.40) / (1.60 - 0.40)
            g = 0.98 - (0.16 * t)
        elif (( ci >= 1.60 ) and ( ci <= 2.00)):
            t = (ci - 1.60) / (2.00 - 1.60)
            g = 0.82 - (0.5 * t * t)
        # B     
        if (( ci >= -0.40) and ( ci < 0.40)):
            t = (ci + 0.40) /(0.40 + 0.40)
            b = 1.00
        elif (( ci >= 0.40) and ( ci <1.50)):
            t = (ci - 0.40) / (1.50 - 0.40)
            b = 1.00 - (0.47 * t) + (0.1 * t * t )
        elif (( ci >= 1.50) and ( ci <=1.94)):
            t = (ci - 1.50) / (1.94 - 1.50)
            b = 0.63 - (0.6 * t * t )
        else:
            b = 0
        #return (r, g, b)
        color = "#%02X%02X%02X"%(int(r*255),
                                 int(g*255),
                                 int(b*255))
        
        #log.debug("Setting color index for star %s to %.2f resulting in %s")
        
        self.color.set_rgb_val(color)
          
        #print color
        return color

        
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
        if star.color.color_name == COLOR_RANDOM_COLOR_INDEX:
            star.set_color_index(_get_random_color_index())
    return generated_stars
            
def _get_random_color_index():
    # ci <-0.4,+2.0> 
    return random.random() * 2.4 - 0.4