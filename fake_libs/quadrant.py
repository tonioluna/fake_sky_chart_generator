from .log_stuff import init_logger

log = init_logger()

class Quadrant:
    def __init__(self, config, x, y, id):
        self.config = config
        self.x = x
        self.y = y
        self.w = self.x * self.config.box_size.width
        self.h = self.y * self.config.box_size.height
        self.id = id
        self.stars = []
    
    def add_star(self, star):
        self.stars.append(star)
    
    def adjust_coordinates(self, w, h):
        return w + self.w, h + self.h
    
    def __str__(self):
        return "Quadrant %s at %i,%i (with %i stars)"%(self.id, self.w, self.h, len(self.stars))
    
