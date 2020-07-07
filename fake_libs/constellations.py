from .log_stuff import init_logger
from .stars import Star
import random
import operator
import math

log = init_logger()

ALGORITHM_BASIC = "basic"
KNOWN_ALGORITHMS = (ALGORITHM_BASIC, 
                   )

class Constellation:
    _id_next = 0
    
    def __init__(self, 
                 quadrants,
                 id = None):
        if id == None:
            self.id = str(Constellation._id_next)
            Constellation._id_next += 1
        else:
            self.id = id
        
        self._quadrants = quadrants
        self.stars = []
    
    def add_star(self, star):
        self.stars.append(star)
        
    def get_copies(self):
        # need to find out how many extra quadrants are added
        assert self.stars[0].is_master
        
        log.info("Getting constellation copies for constellation %s"%(self.id))
        
        master_star = self.stars[0]
        req_quadrant_copies = []
        for star in self.stars[1:]:
            rel_quad = master_star.get_rel_quadrant_to_other_star(star)
            if rel_quad != (0, 0) and rel_quad not in req_quadrant_copies:
                req_quadrant_copies.append(rel_quad)
        
        log.info("Creating %i constellation copies"%(len(req_quadrant_copies), ))
        
        copies = []
        for index, req_quad in enumerate(req_quadrant_copies):
            const_copy = Constellation(quadrants = self._quadrants, 
                                       id = "%s.%s"%(self.id, index))
            copies.append(const_copy)
            
            for base_star in self.stars:
                # need to find an star which has the same relative position to req_quad
                star_peers = base_star.get_peers()
                for peer_star in star_peers:
                    if peer_star.get_rel_quadrant_to_other_star(base_star) == req_quad:
                        const_copy.add_star(peer_star)
                        break
            
        return copies
        
    
def get_constellations(config, master_stars, quadrants):
    sorted_stars = list(sorted(master_stars, key=operator.attrgetter('size')))
    
    if config.constellation_random_seed != None:
        random.seed(config.constellation_random_seed)
    
    log.info("Constellations algorithm: %s"%(config.constellation_algorithm, ))
    if config.constellation_algorithm == ALGORITHM_BASIC:
        constellations = _get_constellations_alg_basic(config, sorted_stars, quadrants)
    else:
        raise Exception("Internal error, unsupported constellation algorithm: %s"%(config.constellation_algorithm, ))

    log.info("Creating constellation copies")
    constellation_copies = []
    for constellation in constellations:
        constellation_copies.extend(constellation.get_copies())
    
    constellations.extend(constellation_copies)

    return constellations
    
def _get_constellations_alg_basic(config, sorted_master_stars, quadrants):
        
    # Determine the number of stars to use per constellation
    star_counts = []
    for i in range(0, config.constellation_count):
        if len(config.constellation_star_count) == 1:
            star_counts.append(config.constellation_star_count[0])
        else:
            star_count = random.randint(config.constellation_star_count[0], config.constellation_star_count[1])
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
    for const_num in range(0, config.constellation_count):
        log.debug("Doing constellation %i"%(const_num,))
        constellation = Constellation(quadrants = quadrants)
        constellations.append(constellation)
    
        # pick a random star to start with
        base_star = _get_random_star(selected_all_stars, must_be_master = True)
        log.debug("base star: %s"%(base_star,))
        constellation.add_star(base_star)
        
        last_star = base_star
        while len(constellation.stars) < star_counts[const_num]:
            # Calculate the distances to the rest of stars
            distances = _get_distances_to_stars(last_star, selected_all_stars)
            d_keys = list(distances.keys())
            d_keys.sort()
            star = random.choice(distances[d_keys[0]])
            
            star.take()
            log.debug("star %i: %s"%(len(constellation.stars), star))
            
            constellation.add_star(star)
            last_star = star
    
    return constellations
        
def _get_distances_to_stars(base_star, star_list):
    log.debug("Getting distance measurement to %s"%(base_star,))
    distances = {}
    assert len(star_list) > 0, "no stars to measure distance to"
    for star in star_list:
        if star.taken or star.id == base_star.id: 
            log.debug("distance skip %s"%(star,))
            log.debug("%s, %s"%(bool(star.taken), bool(star.id == base_star.id)))
            continue
        d = math.sqrt((base_star.w - star.w)**2 + (base_star.h - star.h)**2)
        log.debug("d = %.3f for %s"%(d, star))
        if d not in distances:
            distances[d] = []
        distances[d].append(star)
    
    assert len(distances) > 0, "no stars meet criteria to measure distance to from %i provide stars"%(len(star_list))
    
    return distances
        
def _get_random_star(star_list, must_be_master = False):
    # make a list of stars which are still available
    av_stars = []
    for star in star_list:
        if not star.taken and (must_be_master == False or star.is_master):
            av_stars.append(star)
    assert len(av_stars) > 0, "ran out of stars to chose from"
    
    star_index = random.randint(0, len(av_stars) - 1)
    
    star = av_stars[star_index]
    star.take()
    
    return star
        
