from ..log_stuff import init_logger
from ..constellations_common import *
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
    all_available_stars = []
    for ms in selected_master_stars:
        all_available_stars.append(ms)
        all_available_stars.extend(ms.childs)
        
    #for star in all_available_stars:
    #    star.color.set_rgb_val("#00FF00FF")
    #    star.size = config.star_size_range[1]
    
    available_stars = all_available_stars
    
    constellations = []
    # fun beggins here
    for const_num in range(0, const_count):
        # Filter out taken stars
        available_stars = get_available_stars(available_stars)
        
        master_av_stars = count_available_master_stars(available_stars)
        
        log.info("Creating constellation %i out of %i possible stars"%(const_num, master_av_stars))
        
        if master_av_stars == 0:
            break
        
        # Special case, can't have a constellation of 1 star. Need to assign it to the nearest constellation (by nearest star)
        if master_av_stars == 1:
            # there will be child stars from each quadrant, need to check against each one of them
            # need to make sure the proper copy of the star is added to the proper constellation, otherwise 
            # weird things happen
            # The easiest way to do that is to compare only against stars which have been assigned to a constellation
            assigned_stars = []
            for star in all_available_stars:
                if star.taken and star.constellation != None:
                    assigned_stars.append(star)
            
            min_d = None
            min_const = None
            min_star = None
            for star in available_stars:
                d = get_distances_to_stars(star, assigned_stars, skip_taken_stars = False)
                d_keys = list(d.keys())
                d_keys.sort()
                if min_d == None or d_keys[0] < min_d:
                    min_d = d_keys[0]
                    min_const = d[d_keys[0]][0].constellation
                    min_star = star
            
            min_star.take()
            min_const.add_star(min_star)
            break
                
        # pick a random star to start with
        base_star = get_random_star(available_stars, must_be_master = True)
        log.debug("base star: %s"%(base_star,))
        constellation = Constellation(quadrants = quadrants, name_display_style = config.constellation_name_display_style)
        constellations.append(constellation)
        constellation.add_star(base_star)
        
        while len(constellation.stars) < star_counts[const_num]:
            # Calculate the distances to the rest of stars
            distances = get_distances_to_stars(constellation, available_stars, skip_taken_stars = True)
            if len(distances) == 0:
                break
            
            d_keys = list(distances.keys())
            d_keys.sort()
            star = random.choice(distances[d_keys[0]])
            
            star.take()
            log.debug("star %i: %s"%(len(constellation.stars), star))
            
            constellation.add_star(star)
        
        # Filter out taken stars
        available_stars = get_available_stars(available_stars)
        
        # Now, check if there's stars close enough to any of the constellation´s stars
        # get the man distance of all the stars to the mean center
        distances_to_mean_center = get_distances_to_stars(constellation, constellation.stars, skip_taken_stars = False)
        
        values = []
        for d, stars in distances_to_mean_center.items():
            for i in range(0, len(stars)):
                values.append(d)
        avg_dist = sum(values) / len(values)
        
        # now, for every star in the constellation, check distances to the available stars
        index = 0
        while index < len(constellation.stars):
            const_star = constellation.stars[index]
            index += 1
            distances = get_distances_to_stars(const_star, available_stars, skip_taken_stars = True)
            for distance, star_list in distances.items():
                if distance > (avg_dist/1.5):
                    continue
                for star in star_list:
                    star.take()
                    constellation.add_star(star)
    
    for constellation in constellations:
        # now, lets sort the stars by angle from the mean center
        center_w, center_h = constellation.get_mean_position()
        
        for star in constellation.stars:
            angle = 360*math.atan2(star.h - center_h, star.w - center_w)/(2*math.pi)
            star.tag = angle
    
        # Sort the stars by angle
        constellation.stars = list(sorted(constellation.stars, key=operator.attrgetter('tag')))
    
    return constellations
