import os
import configparser
import re
from log_stuff import init_logger
import config_file
import svgwrite
import random
import operator
from stars import Quadrant, Star
import math
#from svgwrite import pt
pt = 1

log = init_logger()

def generate_chart(filename, config):
    log.info("Creating chart %s"%(filename,))
    dwg = svgwrite.Drawing(filename=filename, debug=True)
    
    # Master quadrant
    master_stars = _get_chart(dwg, config)
    
    if config.add_neighbor_quadrants:
        log.info("Writting neighbor quadrants")
    
        box_width = config.box_size[0]
        box_height = config.box_size[1]
        
        quadrants = []
        quadrants.append(Quadrant(id = "E",  w = box_width,  h = 0          ))
        quadrants.append(Quadrant(id = "SE", w = box_width,  h = -box_height))
        quadrants.append(Quadrant(id = "S",  w = 0,          h = -box_height))
        quadrants.append(Quadrant(id = "SW", w = -box_width, h = -box_height))
        quadrants.append(Quadrant(id = "W",  w = -box_width, h = 0          ))
        quadrants.append(Quadrant(id = "NW", w = -box_width, h = box_height ))
        quadrants.append(Quadrant(id = "N",  w = 0,          h = box_height ))
        quadrants.append(Quadrant(id = "NE", w = box_width,  h = box_height ))
        
        for quadrant in quadrants:
            _get_chart(dwg, config, quadrant = quadrant, master_stars = master_stars)
        
        if config.add_constellations:
            _add_shared_constellations(dwg, config, master_stars)
        
        
    log.info("Writting file")
    dwg.save()
    
def _add_shared_constellations(dwg, config, master_stars):
    log.info("Adding constellations in shared mode")

    sorted_stars = list(sorted(master_stars, key=operator.attrgetter('size')))
    
    if config.constellation_random_seed != None:
        random.seed(config.constellation_random_seed)
        
    # Determine the number of stars to use per constellation
    star_counts = []
    for i in range(0, config.constellation_count):
        if len(config.constellation_star_count) == 1:
            star_counts.append(config.constellation_star_count[0])
        else:
            star_count = random.randint(config.constellation_star_count[0], config.constellation_star_count[1])
            star_counts.append(star_count)
    
    total_star_count = sum(star_counts)
    selected_master_stars = sorted_stars[-total_star_count:]
    
    # Add all child stars into the mix
    selected_all_stars = []
    for ms in selected_master_stars:
        selected_all_stars.append(ms)
        selected_all_stars.extend(ms.childs)
    
    constellations_dwg = dwg.add(dwg.g(id='constellations', 
                                       stroke=config.constellation_stroke_color.hex_value, 
                                       stroke_width = config.constellation_stroke_width,
                                       fill = "none"))

    
    # fun beggins here
    for const_num in range(0, config.constellation_count):
        log.debug("Doing constellation %i"%(const_num,))
        constellation_stars = []
    
        # pick a random star to start with
        base_star = _get_random_star(selected_all_stars, must_be_master = True)
        log.debug("base star: %s"%(base_star,))
        constellation_stars.append(base_star)
        
        last_star = base_star
        while len(constellation_stars) < star_counts[const_num]:
            # Calculate the distances to the rest of stars
            distances = _get_distances_to_stars(last_star, selected_all_stars)
            d_keys = list(distances.keys())
            d_keys.sort()
            star = random.choice(distances[d_keys[0]])
            star.take()
            log.debug("star %i: %s"%(len(constellation_stars), star))
            constellation_stars.append(star)
            last_star = star
        
        
        const_points = []
        for star in constellation_stars:
            const_points.append((star.w, star.h))
        
        # Finally, make a polygon with the chosen stars
        constellations_dwg.add(dwg.polyline(points = const_points))
    
        
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
        
    
def _get_chart(dwg, config, quadrant = None, master_stars = None):
    assert quadrant == None or master_stars != None
    
    box_width = config.box_size[0]
    box_height = config.box_size[1]
    q_w = 0 if quadrant == None else quadrant.w
    q_h = 0 if quadrant == None else quadrant.h
    
    # out box
    out_box = dwg.add(dwg.g(id='out_box', 
                            stroke=config.box_stroke_color.hex_value, 
                            fill=config.box_fill_color.hex_value, 
                            stroke_width = config.box_stroke_width))
    out_box.add(dwg.polygon(points=[((0 + q_w)*pt,         (0 + q_h)*pt), 
                                    ((0 + q_w)*pt,         (box_height + q_h)*pt),
                                    ((box_width + q_w)*pt, (box_height + q_h)*pt),
                                    ((box_width + q_w)*pt, (0 + q_h)*pt)]))
    
    # grid
    if config.add_grid and (config.grid_line_count_horizontal != 0 or config.grid_line_count_vertical != 0):
        grid = dwg.add(dwg.g(id='grid', 
                             stroke=config.grid_stroke_color.hex_value,
                             stroke_width = config.grid_stroke_width))
        # Horizontal lines
        sep = box_height / (1 + config.grid_line_count_vertical)
        for i in range(0, config.grid_line_count_vertical):
            grid.add(dwg.line(start=((0 + q_w)*pt, (sep + sep*i + q_h)*pt), end=((box_width + q_w)*pt, (sep + sep*i + q_h)*pt)))
        # Vertical lines
        sep = box_width / (1 + config.grid_line_count_horizontal)
        for i in range(0, config.grid_line_count_horizontal):
            grid.add(dwg.line(start=((sep + sep*i + q_w)*pt, (0 + q_h)*pt), end=((sep + sep*i + q_w)*pt, (box_height + q_h)*pt)))
    
    # stars
    generated_stars = []
    if master_stars == None:
        min_size = config.star_size_range[0]
        max_size = config.star_size_range[1]
        size_range = max_size - min_size
        stars_group = dwg.add(dwg.g(id='stars_group'))
        if config.star_random_seed != None:
            random.seed(config.star_random_seed)
        for i in range(0, config.star_count):
            # star size
            r = 1
            for j in range(0, config.star_size_random_count): r *= random.random()
            star_size = (r**config.star_size_distribution_power) * size_range + min_size
            color = config.star_color.hex_value
            
            w = random.random()*box_width*pt
            h = random.random()*box_height*pt
     
            star = Star(size = star_size,
                        w = w, 
                        h = h,
                        color = color)
            generated_stars.append(star)
            
            circle = dwg.circle(center = (w, h), 
                                r = star_size*pt, 
                                fill = color)
            stars_group.add(circle)
    else:
        stars_group = dwg.add(dwg.g(id='stars_group_q%s'%(quadrant.id,)))
        for master_star in master_stars:
            w, h = quadrant.adjust_coordinates(master_star.w, master_star.h)
        
            child_star = Star(master_star = master_star, 
                              quadrant = quadrant)
            generated_stars.append(child_star)
        
            circle = dwg.circle(center = (w, h), 
                                r = master_star.size*pt, 
                                fill = master_star.color)
            stars_group.add(circle)
            
    return generated_stars
    
