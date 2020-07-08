import os
import configparser
import re
from .log_stuff import init_logger
from . import config_file
import svgwrite
import random
from .stars import Star
from .quadrant import Quadrant
from .constellations import get_constellations
#from svgwrite import pt
pt = 1

log = init_logger()

def generate_chart(filename, config):
    log.info("Creating chart %s"%(filename,))
    dwg = svgwrite.Drawing(filename=filename, debug=True)

    # Master quadrant
    central_quadrant = None
    if config.add_neighbor_quadrants:
        central_quadrant = Quadrant(id = "C", config = config, x = 1, y = 1)
    master_stars = _get_chart(dwg, config, quadrant = central_quadrant)
    
    if config.add_neighbor_quadrants:
        log.info("Writting neighbor quadrants")
        
        quadrants = []
        
        quadrants.append(Quadrant(id = "E",  config = config, x = 2,  y = 1 ))
        quadrants.append(Quadrant(id = "SE", config = config, x = 2,  y = 0 ))
        quadrants.append(Quadrant(id = "S",  config = config, x = 1,  y = 0 ))
        quadrants.append(Quadrant(id = "SW", config = config, x = 0,  y = 0 ))
        quadrants.append(Quadrant(id = "W",  config = config, x = 0,  y = 1 ))
        quadrants.append(Quadrant(id = "NW", config = config, x = 0,  y = 2 ))
        quadrants.append(Quadrant(id = "N",  config = config, x = 1,  y = 2 ))
        quadrants.append(Quadrant(id = "NE", config = config, x = 2,  y = 2 ))
        
        for quadrant in quadrants:
            _get_chart(dwg, config, quadrant = quadrant, master_stars = master_stars)
        
        quadrants.append(central_quadrant)
        
        if config.add_constellations:
            _add_shared_constellations(dwg, config, master_stars, quadrants)
        
        
    log.info("Writting file")
    dwg.save()
    
def _add_shared_constellations(dwg, config, master_stars, quadrants):
    log.info("Adding constellations")

    constellations = get_constellations(config, master_stars, quadrants)
    
    constellations_dwg = dwg.add(dwg.g(id='constellations', 
                                       stroke=config.constellation_stroke_color.get_hex_value(), 
                                       stroke_width = config.constellation_stroke_width,
                                       fill = "none"))
    
    for constellation in constellations:
        const_points = []
        for star in constellation.stars:
            const_points.append((star.w, star.h))
        
        # TODO: add closed/open check here
        
        # Finally, make a polygon with the chosen stars
        constellations_dwg.add(dwg.polyline(points = const_points))
        
        const_names = dwg.add(dwg.g(id='constellation_names', 
                                    stroke='none',
                                    fill=config.constellation_name_font.color.get_hex_value(),
                                    font_size=config.constellation_name_font.size*pt,
                                    font_family=config.constellation_name_font.font_family))
        
        log.warning("Constellation name groups are not working!")
        
        if config.constellation_name_enable:
            w, h = constellation.get_mean_position()
            const_names.add(dwg.text(constellation.name,
                                     insert=(w*pt, h*pt),
                                     )
        )
        
    
def _get_chart(dwg, config, quadrant = None, master_stars = None):
    #assert quadrant == None or master_stars != None
    
    q_w = 0 if quadrant == None else quadrant.w
    q_h = 0 if quadrant == None else quadrant.h
    
    # out box
    out_box = dwg.add(dwg.g(id='out_box', 
                            stroke=config.box_stroke_color.get_hex_value(), 
                            fill=config.box_fill_color.get_hex_value(), 
                            stroke_width = config.box_stroke_width))
    out_box.add(dwg.polygon(points=[((0 + q_w)*pt,         (0 + q_h)*pt), 
                                    ((0 + q_w)*pt,         (config.box_size.height + q_h)*pt),
                                    ((config.box_size.width + q_w)*pt, (config.box_size.height + q_h)*pt),
                                    ((config.box_size.width + q_w)*pt, (0 + q_h)*pt)]))
    
    # grid
    if config.add_grid and (config.grid_line_count_horizontal != 0 or config.grid_line_count_vertical != 0):
        grid = dwg.add(dwg.g(id='grid', 
                             stroke=config.grid_stroke_color.get_hex_value(),
                             stroke_width = config.grid_stroke_width))
        # Horizontal lines
        sep = config.box_size.height / (1 + config.grid_line_count_vertical)
        for i in range(0, config.grid_line_count_vertical):
            grid.add(dwg.line(start=((0 + q_w)*pt, (sep + sep*i + q_h)*pt), end=((config.box_size.width + q_w)*pt, (sep + sep*i + q_h)*pt)))
        # Vertical lines
        sep = config.box_size.width / (1 + config.grid_line_count_horizontal)
        for i in range(0, config.grid_line_count_horizontal):
            grid.add(dwg.line(start=((sep + sep*i + q_w)*pt, (0 + q_h)*pt), end=((sep + sep*i + q_w)*pt, (config.box_size.height + q_h)*pt)))
    
    # stars
    generated_stars = []
    if master_stars == None:
        log.info("Writting %i stars to central quadrant %s"%(config.star_count, quadrant))
        min_size = config.star_size_range[0]
        max_size = config.star_size_range[1]
        size_range = max_size - min_size
        stars_group = dwg.add(dwg.g(id='stars_group_central'))
        if config.star_random_seed != None:
            random.seed(config.star_random_seed)
        for i in range(0, config.star_count):
            # star size
            r = 1
            for j in range(0, config.star_size_random_count): r *= random.random()
            star_size = (r**config.star_size_distribution_power) * size_range + min_size
            
            w = random.random()*config.box_size.width*pt
            h = random.random()*config.box_size.height*pt
            
            star = Star(size = star_size,
                        w = w, 
                        h = h,
                        color = config.star_color.clone(),
                        quadrant = quadrant)
            
            generated_stars.append(star)
            
        # Split the process in two loops to keep the random behavior for the same seed when random colors are enabled            
        for star in generated_stars:
            if config.star_color.color_name == config_file.COLOR_RANDOM_COLOR_INDEX:
                star.set_color_index(_get_random_color_index())

            circle = dwg.circle(center = (star.w, star.h), 
                                r = star.size*pt, 
                                fill = star.color.get_hex_value())
            stars_group.add(circle)
    else:
        log.info("Writting %i stars to quadrant %s"%(len(master_stars), quadrant))
        stars_group = dwg.add(dwg.g(id='stars_group_q%s'%(quadrant.id,)))
        for master_star in master_stars:
            #w, h = quadrant.adjust_coordinates(master_star.w, master_star.h)
        
            child_star = Star(master_star = master_star, 
                              quadrant = quadrant)
            generated_stars.append(child_star)
        
            log.debug("%s (out of %s)"%(child_star, master_star))
            #log.debug("w: %i, h: %i"%(w, h))
            
        
            circle = dwg.circle(center = (child_star.w, child_star.h), 
                                r = child_star.size*pt, 
                                fill = child_star.color.get_hex_value())
            stars_group.add(circle)
            
    return generated_stars
    
def _get_random_color_index():
    # ci <-0.4,+2.0> 
    return random.random() * 2.4 - 0.4