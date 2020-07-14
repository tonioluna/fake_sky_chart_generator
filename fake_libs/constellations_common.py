from .log_stuff import init_logger
from .stars import Star
import random
import operator
import math
import os
import collections

log = init_logger()


NAME_DISPLAY_STYLE_NAME = "name"
NAME_DISPLAY_STYLE_NAME_ID = "name+id"
KNOWN_NAME_DISPLAY_STYLES = (NAME_DISPLAY_STYLE_NAME,
                             NAME_DISPLAY_STYLE_NAME_ID
                            )
Segment = collections.namedtuple("ConstellationSegment", ("star_ids", "is_closed"))
                            
class Constellation:
    _id_next = 0
    
    def __init__(self, 
                 quadrants,
                 name_display_style,
                 id = None,
                 name = None,
                 custom_color = None):
        if id == None:
            self.id = str(Constellation._id_next)
            Constellation._id_next += 1
        else:
            self.id = id
        
        self.name = self.id if name == None else name
        
        self.name_display_style = name_display_style
        
        self._quadrants = quadrants
        self.stars = []
        self.star_dict = {}
        self.segments = []
        self.custom_color = custom_color
        
    def __str__(self):
        return "Constellation %s%s (%i stars)"%(self.id, "" if (self.name == None or self.id == self.name) else (" (%s)"%(self.name)), len(self.stars))
    
    def get_display_name(self):
        if self.name_display_style == NAME_DISPLAY_STYLE_NAME:
            return self.name
        if self.name_display_style == NAME_DISPLAY_STYLE_NAME_ID:
            return "%s (%s)"%(self.name, self.id) if self.name != self.id else self.name
        raise Exception("Not implemented style: %s"%(self.name_display_style, ))
    
    def add_star(self, star):
        self.star_dict[star.id] = star
        self.stars.append(star)
        star.constellation = self
        
    def get_copies(self):
        # need to find out how many extra quadrants are added
        log.info("Getting constellation copies for constellation %s (%s)"%(self.name, self.id))
        
        master_star = None
        # get any master star
        for star in self.stars:
            if star.is_master:
                master_star = star
                break
        # There should be at least one master star
        assert master_star != None, "Constelation %s does not have any master star"%(self.id)
        
        req_quadrant_copies = []
        for star in self.stars:
            if star.id == master_star.id: continue
            rel_quad = master_star.get_rel_quadrant_to_other_star(star)
            if rel_quad != (0, 0) and rel_quad not in req_quadrant_copies:
                req_quadrant_copies.append(rel_quad)
        
        log.info("Creating %i constellation copies"%(len(req_quadrant_copies), ))
        
        copies = []
        for index, req_quad in enumerate(req_quadrant_copies):
            const_copy = Constellation(quadrants = self._quadrants, 
                                       name_display_style = self.name_display_style,
                                       id = "%s.%s"%(self.id, index + 1),
                                       name = self.name,
                                       custom_color = self.custom_color)
            star_xlation_dict = {}
            copies.append(const_copy)
            
            for base_star in self.stars:
                # need to find an star which has the same relative position to req_quad
                star_peers = base_star.get_peers()
                for peer_star in star_peers:
                    if peer_star.get_rel_quadrant_to_other_star(base_star) == req_quad:
                        const_copy.add_star(peer_star)
                        star_xlation_dict[base_star.id] = peer_star.id
                        break
        
            # Finally, copy the segments
            for segment in self.segments:
                copy_stars = []
                for star_id in segment.star_ids:
                    copy_stars.append(star_xlation_dict[star_id])
                const_copy.draw_segment(copy_stars, segment.is_closed)

        return copies
        
    def get_mean_position(self):
        assert len(self.stars) >= 1
        x = []
        y = []
        for star in self.stars:
            x.append(star.w)
            y.append(star.h)
        
        return (sum(x)/len(x), sum(y)/len(y))

    def draw_segment(self, star_ids, is_closed):
        segment = []
        for star_id in star_ids:
            assert star_id in self.star_dict, "Star %s is not part of this constellation"%(star_id,)
            segment.append(star_id)
        self.segments.append(Segment(star_ids, is_closed))
        
class ConstellationNames:
    def __init__(self, filename = None):
        self._filename = filename
        self._load()
        self.reset_used_constellation_name()
        
    def _load(self):
        log.info("Loading constellation names from %s"%(self._filename, ))
        
        assert os.path.isfile(self._filename), "Constelation name does not exist: %s"%(self._filename, )
        
        with open(self._filename, "r") as fh:
            self.constellation_names = [l.replace("\n", "").strip() for l in fh.readlines()]
        
    def get_random_constellation_name(self):
        assert len(self._available_constellation_names) > 0, "No more constellation names available to use"
        index = random.randint(0, len(self._available_constellation_names) - 1)
        return self._available_constellation_names.pop(index)
            
    def reset_used_constellation_name(self):
        self._available_constellation_names = []
        self._available_constellation_names.extend(self.constellation_names)
        
def get_available_stars(stars):
    av_stars = []
    for star in stars:
        if star.taken: continue
        av_stars.append(star)
    return av_stars
        
def count_available_master_stars(stars):
    c = 0
    for s in stars:
        if s.is_master and not s.taken:
            c += 1
    return c
        
def get_distances_to_stars(ref_obj, star_list, skip_taken_stars):
    base_star = None
    if isinstance(ref_obj, Star):
        ref_w = ref_obj.w
        ref_h = ref_obj.h
        base_star = ref_obj
    elif isinstance(ref_obj, Constellation):
        ref_w,ref_h = ref_obj.get_mean_position()
    else:
        raise Exception("Can't get distance to object type %s"%(type(ref_obj)))
    
    #log.debug("Getting distance measurement to %s"%(ref_obj,))
    distances = {}
    #assert len(star_list) > 0, "no stars to measure distance to"
    for star in star_list:
        if (skip_taken_stars and star.taken) or (base_star != None and star.id == base_star.id): 
            continue
        d = math.sqrt((ref_w - star.w)**2 + (ref_h - star.h)**2)
        #log.debug("d = %.3f for %s"%(d, star))
        if d not in distances:
            distances[d] = []
        distances[d].append(star)
    
    #assert len(distances) > 0, "no stars meet criteria to measure distance to from %i provide stars"%(len(star_list))
    
    return distances
        
def get_distance_star_to_star(star_a, star_b):
    return math.sqrt((star_a.w - star_b.w)**2 + (star_a.h - star_b.h)**2)
        
def get_random_star(star_list, must_be_master = False):
    # make a list of stars which are still available
    av_stars = []
    for star in star_list:
        if not star.taken and (must_be_master == False or star.is_master):
            av_stars.append(star)
    #assert len(av_stars) > 0, "ran out of stars to chose from"
    if len(av_stars) == 0:
        log.warning("Ran out of stars to chose from")
        return None
    
    star_index = random.randint(0, len(av_stars) - 1)
    
    star = av_stars[star_index]
    star.take()
    
    return star