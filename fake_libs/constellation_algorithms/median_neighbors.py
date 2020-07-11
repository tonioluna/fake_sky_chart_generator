from ..log_stuff import init_logger
from ..constellations_common import Constellation, get_distances_to_stars, get_random_star
import math
import operator
import random

log = init_logger()

def get_constellations(config, sorted_master_stars, quadrants, **kwargs):
        
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
        base_star = get_random_star(selected_all_stars, must_be_master = True)
        if base_star == None:
            break
        log.debug("base star: %s"%(base_star,))
        constellation = Constellation(quadrants = quadrants)
        constellations.append(constellation)
        constellation.add_star(base_star)
        
        while len(constellation.stars) < star_counts[const_num]:
            # Calculate the distances to the rest of stars
            distances = get_distances_to_stars(constellation, selected_all_stars, skip_taken_stars = True)
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
        distances = get_distances_to_stars(constellation, constellation.stars, skip_taken_stars = False)
        values = []
        for d, stars in distances.items():
            for i in range(0, len(stars)):
                values.append(d)
        avg_dist = sum(values) / len(values)
        
        distances = get_distances_to_stars(constellation, selected_all_stars, skip_taken_stars = True)
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
