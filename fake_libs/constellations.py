from .log_stuff import init_logger
from .stars import Star
import random
import operator
import math
import os

log = init_logger()

ALGORITHM_BASIC = "basic"
ALGORITHM_MEDIAN_NEIGHBORS = "median_neighbors"
KNOWN_ALGORITHMS = (ALGORITHM_BASIC, 
                    ALGORITHM_MEDIAN_NEIGHBORS
                   )

_my_path = os.path.abspath(os.path.dirname(__file__))
_default_constellation_names_file = os.path.join(_my_path, "..", "doc", "constellation_names.txt")

class Constellation:
    _id_next = 0
    
    def __init__(self, 
                 quadrants,
                 id = None,
                 name = None):
        if id == None:
            self.id = str(Constellation._id_next)
            Constellation._id_next += 1
        else:
            self.id = id
        
        self.name = self.id if name == None else name
        
        self._quadrants = quadrants
        self.stars = []
    
    def add_star(self, star):
        self.stars.append(star)
        
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
        for star in self.stars[1:]:
            rel_quad = master_star.get_rel_quadrant_to_other_star(star)
            if rel_quad != (0, 0) and rel_quad not in req_quadrant_copies:
                req_quadrant_copies.append(rel_quad)
        
        log.info("Creating %i constellation copies"%(len(req_quadrant_copies), ))
        
        copies = []
        for index, req_quad in enumerate(req_quadrant_copies):
            const_copy = Constellation(quadrants = self._quadrants, 
                                       id = "%s.%s"%(self.id, index + 1),
                                       name = self.name)
            copies.append(const_copy)
            
            for base_star in self.stars:
                # need to find an star which has the same relative position to req_quad
                star_peers = base_star.get_peers()
                for peer_star in star_peers:
                    if peer_star.get_rel_quadrant_to_other_star(base_star) == req_quad:
                        const_copy.add_star(peer_star)
                        break
            
        return copies
        
    def get_mean_position(self):
        assert len(self.stars) >= 1
        x = []
        y = []
        for star in self.stars:
            x.append(star.w)
            y.append(star.h)
        
        return (sum(x)/len(x), sum(y)/len(y))

class ConstellationNames:
    def __init__(self, custom_filename = None):
        if custom_filename == None:
            custom_filename = _default_constellation_names_file
        self._filename = custom_filename
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
        
def get_constellations(config, master_stars, quadrants):
    sorted_stars = list(sorted(master_stars, key=operator.attrgetter('size')))
    
    if config.constellation_random_seed != None:
        random.seed(config.constellation_random_seed)
    
    log.info("Constellations algorithm: %s"%(config.constellation_algorithm, ))
    if config.constellation_algorithm == ALGORITHM_BASIC:
        constellations = _get_constellations_alg_basic(config, sorted_stars, quadrants)
    elif config.constellation_algorithm == ALGORITHM_MEDIAN_NEIGHBORS:
        constellations = _get_constellations_alg_median_neighbors(config, sorted_stars, quadrants)
    else:
        raise Exception("Internal error, unsupported constellation algorithm: %s"%(config.constellation_algorithm, ))

    # name constellations
    const_names = ConstellationNames()
    if config.constellation_name_random_seed != None:
        random.seed(config.constellation_name_random_seed)
    for const in constellations:
        const.name = const_names.get_random_constellation_name()

    log.info("Creating constellation copies")
    constellation_copies = []
    for constellation in constellations:
        constellation_copies.extend(constellation.get_copies())
    
    constellations.extend(constellation_copies)

    return constellations
    
def _get_constellations_alg_basic(config, sorted_master_stars, quadrants):
        
    # Determine the number of stars to use per constellation
    star_counts = []
    const_count = random.randint(config.constellation_count_range[0], config.constellation_count_range[1])
    log.debug("Constellation count: %s"%(const_count,))
    for i in range(0, const_count):
        star_count = random.randint(config.constellation_star_count_range[0], config.constellation_star_count_range[1])
        star_counts.append(star_count)
    
    total_star_count = sum(star_counts)
    selected_master_stars = sorted_master_stars[-total_star_count:]
    
    # Add all child stars into the mix
    selected_all_stars = []
    for ms in selected_master_stars:
        selected_all_stars.append(ms)
        selected_all_stars.extend(ms.childs)
    
    constellations = []
    # fun beggins here
    for const_num in range(0, const_count):
        log.info("Doing constellation %i with %i stars"%(const_num, star_counts[const_num]))
        
        # pick a random star to start with
        base_star = _get_random_star(selected_all_stars, must_be_master = True)
        if base_star == None:
            break
        log.debug("base star: %s"%(base_star,))
        constellation = Constellation(quadrants = quadrants)
        constellations.append(constellation)
        constellation.add_star(base_star)
        
        last_star = base_star
        while len(constellation.stars) < star_counts[const_num]:
            # Calculate the distances to the rest of stars
            distances = _get_distances_to_stars(last_star, selected_all_stars, skip_taken_stars = True)
            assert len(distances) > 0, "failed to find any non-taken star"
            d_keys = list(distances.keys())
            d_keys.sort()
            star = random.choice(distances[d_keys[0]])
            
            star.take()
            log.debug("star %i: %s"%(len(constellation.stars), star))
            
            constellation.add_star(star)
            last_star = star
    
    return constellations
        
def _get_constellations_alg_median_neighbors(config, sorted_master_stars, quadrants):
        
    # Determine the number of stars to use per constellation
    star_counts = []
    const_count = random.randint(config.constellation_count_range[0], config.constellation_count_range[1])
    log.debug("Constellation count: %s"%(const_count,))
    for i in range(0, const_count):
        star_count = random.randint(config.constellation_star_count_range[0], config.constellation_star_count_range[1])
        star_counts.append(star_count)

    total_star_count = sum(star_counts)
    selected_master_stars = sorted_master_stars[-total_star_count:]
    
    # Add all child stars into the mix
    selected_all_stars = []
    for ms in selected_master_stars:
        selected_all_stars.append(ms)
        selected_all_stars.extend(ms.childs)
    
    constellations = []
    # fun beggins here
    for const_num in range(0, const_count):
        log.info("Creating constellation %i"%(const_num,))
        
        # pick a random star to start with
        base_star = _get_random_star(selected_all_stars, must_be_master = True)
        if base_star == None:
            break
        log.debug("base star: %s"%(base_star,))
        constellation = Constellation(quadrants = quadrants)
        constellations.append(constellation)
        constellation.add_star(base_star)
        
        while len(constellation.stars) < star_counts[const_num]:
            # Calculate the distances to the rest of stars
            distances = _get_distances_to_stars(constellation, selected_all_stars, skip_taken_stars = True)
            if len(distances) == 0:
                break
            
            d_keys = list(distances.keys())
            d_keys.sort()
            star = random.choice(distances[d_keys[0]])
            
            star.take()
            log.debug("star %i: %s"%(len(constellation.stars), star))
            
            constellation.add_star(star)
        
        # Now, check if there's stars close enough to the constellation as to also anex them
        # get the man distance of all the stars to the mean center
        distances = _get_distances_to_stars(constellation, constellation.stars, skip_taken_stars = False)
        values = []
        for d, stars in distances.items():
            for i in range(0, len(stars)):
                values.append(d)
        avg_dist = sum(values) / len(values)
        
        distances = _get_distances_to_stars(constellation, selected_all_stars, skip_taken_stars = True)
        for distance, star_list in distances.items():
            if distance > avg_dist*2.2:
                continue
            for star in star_list:
                star.take()
                constellation.add_star(star)
                
    
        # now, lets sort the stars by angle from the mean center
        center_w, center_h = constellation.get_mean_position()
        
        for star in constellation.stars:
            angle = 360*math.atan2(star.h - center_h, star.w - center_w)/(2*math.pi)
            star.tag = angle
    
        # Sort the stars by angle
        constellation.stars = list(sorted(constellation.stars, key=operator.attrgetter('tag')))
    
    return constellations
        

def _get_distances_to_stars(ref_obj, star_list, skip_taken_stars):
    base_star = None
    if isinstance(ref_obj, Star):
        ref_w = ref_obj.w
        ref_h = ref_obj.h
        base_star = ref_obj
    elif isinstance(ref_obj, Constellation):
        ref_w,ref_h = ref_obj.get_mean_position()
    else:
        raise Exception("Can't get distance to object type %s"%(type(ref_obj)))
    
    
    log.debug("Getting distance measurement to %s"%(ref_obj,))
    distances = {}
    assert len(star_list) > 0, "no stars to measure distance to"
    for star in star_list:
        if (skip_taken_stars and star.taken) or (base_star != None and star.id == base_star.id): 
            continue
        d = math.sqrt((ref_w - star.w)**2 + (ref_h - star.h)**2)
        log.debug("d = %.3f for %s"%(d, star))
        if d not in distances:
            distances[d] = []
        distances[d].append(star)
    
    #assert len(distances) > 0, "no stars meet criteria to measure distance to from %i provide stars"%(len(star_list))
    
    return distances
        
def _get_random_star(star_list, must_be_master = False):
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
        
