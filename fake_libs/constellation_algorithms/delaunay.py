from ..log_stuff import init_logger
from ..color import  Color, debug_colors
from ..constellations_common import *
import math
import operator
import random
from scipy.spatial import Delaunay

add_debug_colors = False
debug_color_index = 0

log = init_logger()

def get_constellations(config, sorted_master_stars, quadrants, **kwargs):
    global debug_color_index
        
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
    all_stars_dict = {}
    all_available_stars = []
    for ms in selected_master_stars:
        all_available_stars.append(ms)
        all_available_stars.extend(ms.childs)
        
    for star in all_available_stars:
        all_stars_dict[star.id] = star
        
    if add_debug_colors:
        for star in all_available_stars:
            star.color.set_rgb_val("#00FF00FF")
            star.size = config.star_size_range[1]
    
    available_stars = all_available_stars
    
    points_dict = {}
    for star in available_stars:
        c = (star.w, star.h)
        points_dict[c] = star
        #star.take()
        
    points = list(points_dict.keys())
        
    tri = Delaunay(points)
    
    # Draw the debug constellation with the full array of lines
    #debug_constellation = Constellation(quadrants = quadrants, name_display_style = config.constellation_name_display_style)
    #for star in available_stars:
    #    debug_constellation.add_star(star)
    #for triangle in tri.simplices:
    #    star_ids = []
    #    for index in triangle:
    #        star_ids.append(points_dict[points[index]].id)
    #    debug_constellation.draw_segment(star_ids, is_closed = True)
    #    #debug_constellation.set_as_debug_constellation()
    
    # Create a map of the valid transitions
    nodes = {}
    
    for triangle in tri.simplices:
        star_ids = []
        for index in triangle:
            star_ids.append(points_dict[points[index]].id)
        for src_star_id, dst_stars in ( (star_ids[0], (star_ids[1], star_ids[2])),
                                        (star_ids[1], (star_ids[2], star_ids[0])),
                                        (star_ids[2], (star_ids[0], star_ids[1]))
                                       ):
            if src_star_id not in nodes:
                nodes[src_star_id] = Node(all_stars_dict[src_star_id])
            node = nodes[src_star_id]
            for dst_star_id in dst_stars:
                if dst_star_id not in node.nodes:
                    node.nodes.append(dst_star_id)
    
    constellations = []
    # fun beggins here
    #for const_num in range(0, const_count):
    const_num = -1
    
    pending_lone_star = None
    
    while True:
        if pending_lone_star == None:
            const_num += 1
            
            # Filter out taken stars
            available_stars = get_available_stars(available_stars)
            
            master_av_stars = count_available_master_stars(available_stars)
            
            log.info("Creating constellation %i out of %i possible stars"%(const_num, master_av_stars))
            
            if master_av_stars == 0:
                break
        
        # Special case, can't have a constellation of 1 star. Need to assign it to the nearest constellation (by nearest star)
        if pending_lone_star != None or master_av_stars == 1:
            # there will be child stars from each quadrant, need to check against each one of them
            # need to make sure the proper copy of the star is added to the proper constellation, otherwise 
            # weird things happen
            # The easiest way to do that is to compare only against stars which have been assigned to a constellation
            assigned_stars = []
            for star in all_available_stars:
                if star.taken and star.constellation != None:
                    assigned_stars.append(star)
            
            star_copies_to_assing = None
            if pending_lone_star != None:
                log.info("Looking for nearby costellation for lone star %s"%(pending_lone_star,))
                star_copies_to_assing = []
                star_copies_to_assing.append(pending_lone_star.master_star)
                star_copies_to_assing.extend(pending_lone_star.master_star.childs)
            else:
                log.info("Looking for nearby constellation for last standing star %s"%(available_stars[0].master_star,))
                star_copies_to_assing = available_stars
            
            min_d = None
            min_const = None
            min_star = None
            for star in star_copies_to_assing:
                # Need to compare only against which have a valid constellation assigned
                all_neighbor_stars = [nodes[node_id].star for node_id in nodes[star.id].nodes]
                valid_neighbor_stars = []
                for ns in all_neighbor_stars:
                    if ns.taken and ns.constellation != None:
                        valid_neighbor_stars.append(ns)
                if len(valid_neighbor_stars) == 0: continue
                print (valid_neighbor_stars)
                print([s.master_star.id for s in valid_neighbor_stars])
                print(star.id)
                d = get_distances_to_stars(star, valid_neighbor_stars, skip_taken_stars = False)
                print (d)
                d_keys = list(d.keys())
                d_keys.sort()
                if min_d == None or d_keys[0] < min_d:
                    min_d = d_keys[0]
                    min_const = d[d_keys[0]][0].constellation
                    min_star = star
            
            min_star.take()
            min_const.add_star(min_star)
            
            if pending_lone_star != None:
                pending_lone_star = None
                continue
            else:
                break
                
        # pick a random star to start with
        base_star = get_random_star(available_stars, must_be_master = True)
        log.debug("base star: %s"%(base_star,))
        constellation = Constellation(quadrants = quadrants, name_display_style = config.constellation_name_display_style)
        constellation.add_star(base_star)
        
        if add_debug_colors:
            constellation.custom_color = Color(debug_colors[debug_color_index])
            debug_color_index = (debug_color_index + 1) % len(debug_colors)
        
        tgt_star_count = random.randint(config.constellation_star_count_range[0], config.constellation_star_count_range[1])
        
        while len(constellation.stars) < tgt_star_count:
            min_dist = None
            min_dist_star = None
            # Calculate the distances from every star on the constellation to any neighbor star of those stars
            for star in constellation.stars:
                neighbor_stars = [nodes[node_id].star for node_id in nodes[star.id].nodes]
                distances = get_distances_to_stars(star, neighbor_stars, skip_taken_stars = True)
            
                d_keys = list(distances.keys())
                if len(d_keys) == 0:
                    break
                d_keys.sort()
                local_min_dist = d_keys[0]
                local_min_dist_star = random.choice(distances[local_min_dist])
                
                if min_dist == None or local_min_dist < min_dist:
                    min_dist = local_min_dist
                    min_dist_star = local_min_dist_star
            
            # out of connected stars
            if min_dist == None:
                break
            
            min_dist_star.take()
            log.debug("star %i: %s"%(len(constellation.stars), min_dist_star))
            
            constellation.add_star(min_dist_star)
        
        if len(constellation.stars) > 1:
            constellations.append(constellation)
        else:
            star = constellation.stars[0]
            log.warning("No stars to connect to %s"%(star,))
            star.untake()
            const_num -= 1
            pending_lone_star = star
        
        
    # for the time being draw all the valid connections
    for constellation in constellations:
        drawn_segments = []
        
        for star in constellation.stars:
            for node_id in nodes[star.id].nodes:
                # If this valid node goes outside of this constellation
                if node_id not in constellation.star_dict:
                    continue
                segment_id = "%s_%s"%(star.id, node_id)
                alt_segment_id = "%s_%s"%(node_id, star.id)
                if segment_id not in drawn_segments:
                    constellation.draw_segment([star.id, node_id], is_closed = False)
                    drawn_segments.append(segment_id)
                    drawn_segments.append(alt_segment_id)
    
    return constellations

class Node:
    def __init__(self, star):
        self.star = star
        self.nodes = []
        self.id = self.star.id
    
    