import os
import configparser
import re
from .log_stuff import init_logger
from . import config_file
import svgwrite
import random
from .stars import Star, get_random_stars
from .quadrant import Quadrant
from .constellations import get_constellations
from .dso import get_galaxies, get_clusters, DSO_GLOBULAR_CLUSTER, DSO_OPEN_CLUSTER
#from svgwrite import pt
pt = 1

draw_all_quadrants = False

log = init_logger()

def generate_chart(filename, config):
    log.info("Creating chart %s"%(filename,))
    
    box_w = config.box_size.width if not draw_all_quadrants else config.box_size.width * 3
    box_h = config.box_size.height if not draw_all_quadrants else config.box_size.height * 3
    box_offset = 0 if not draw_all_quadrants else 1
        
    dwg = svgwrite.Drawing(filename=filename, debug=True, size = (box_w*pt, box_h*pt))

    # Master quadrant
    central_quadrant = None
    if config.add_neighbor_quadrants:
        central_quadrant = Quadrant(id = "C", config = config, x = box_offset + 0, y = box_offset + 0)
    master_stars = _get_chart(dwg, config, quadrant = central_quadrant)
    
    if config.add_neighbor_quadrants:
        log.info("Writting neighbor quadrants")
        
        quadrants = []
        
        quadrants.append(Quadrant(id = "E",  config = config, x = box_offset + 1,   y = box_offset + 0 ))
        quadrants.append(Quadrant(id = "SE", config = config, x = box_offset + 1,   y = box_offset + -1))
        quadrants.append(Quadrant(id = "S",  config = config, x = box_offset + 0,   y = box_offset + -1))
        quadrants.append(Quadrant(id = "SW", config = config, x = box_offset + -1,  y = box_offset + -1))
        quadrants.append(Quadrant(id = "W",  config = config, x = box_offset + -1,  y = box_offset + 0 ))
        quadrants.append(Quadrant(id = "NW", config = config, x = box_offset + -1,  y = box_offset + 1 ))
        quadrants.append(Quadrant(id = "N",  config = config, x = box_offset + 0,   y = box_offset + 1 ))
        quadrants.append(Quadrant(id = "NE", config = config, x = box_offset + 1,   y = box_offset + 1 ))
        
        child_stars = []
        for quadrant in quadrants:
            child_stars.extend(_get_chart(dwg, config, quadrant = quadrant, master_stars = master_stars))
        
        quadrants.append(central_quadrant)
      
    constellations = None
    if config.add_constellations:
        log.info("Writting constellations into the final chart")
        constellations = _add_constellations(dwg, config, master_stars, quadrants)

    if config.add_galaxies:
        _add_galaxies(dwg, config, central_quadrant)
    
    if config.add_open_clusters:
        _add_open_clusters(dwg, config, central_quadrant)
        
    if config.add_globular_clusters:
        _add_globular_clusters(dwg, config, central_quadrant)
        
    # now write the stars here
    log.info("Writting stars into the final chart")
    stars_group = dwg.add(dwg.g(id='stars_group_central'))
    draw_stars = []
    draw_stars.extend(master_stars)
    if config.add_neighbor_quadrants and draw_all_quadrants:
        draw_stars.extend(child_stars)
    
    for star in draw_stars:
        if star.constellation == None or star.constellation.custom_color == None:
            fill = star.color.get_hex_rgb()
            fill_opacity = star.color.get_float_alpha()
        else:
            fill = star.constellation.custom_color.get_hex_rgb()
            fill_opacity = star.constellation.custom_color.get_float_alpha()
        
        circle = dwg.circle(center = (star.w*pt, star.h*pt), 
                            r = star.size*pt, 
                            fill = fill,
                            fill_opacity = fill_opacity,
                            )
        stars_group.add(circle)
    
    if config.add_constellations:
        log.info("Writting constellation names into the final chart")
        _add_constellation_names(dwg, constellations, config)
    
    log.info("Writting file %s"%(filename,))
    dwg.save()
    
def _add_galaxies(dwg, config, central_quadrant):
    log.info("Adding galaxies")
    galaxies = get_galaxies(config, central_quadrant)
    
    galaxies_dwg = dwg.add(dwg.g(id='galaxies', 
                                 stroke=config.galaxies_stroke_color.get_hex_rgb(), 
                                 stroke_opacity = config.galaxies_stroke_color.get_float_alpha(),
                                 stroke_width = config.galaxies_stroke_width,
                                 fill = config.galaxies_fill_color.get_hex_rgb(),
                                 fill_opacity = config.galaxies_fill_color.get_float_alpha()))
    
    for galaxy in galaxies:
        rx = galaxy.size
        ry = galaxy.size * galaxy.params["eccentricity"]
        galaxies_dwg.add(dwg.ellipse(center=(galaxy.w*pt, galaxy.h*pt), 
                                     r=(rx*pt, ry*pt),
                                     # it is necessary to specify the center of rotation, otherwise it seems to use the same center for the whole group
                                     transform="rotate(%i %i %i)"%(galaxy.params["rotate"], galaxy.w*pt, galaxy.h*pt)))
        
    return galaxies

def _add_open_clusters(dwg, config, central_quadrant):
    log.info("Adding open clusters")
    open_clusters = get_clusters(config, central_quadrant, cluster_type = DSO_OPEN_CLUSTER)
    
    open_clusters_dwg = dwg.add(dwg.g(id='open_clusters', 
                                 stroke=config.open_clusters_stroke_color.get_hex_rgb(), 
                                 stroke_opacity = config.open_clusters_stroke_color.get_float_alpha(),
                                 stroke_width = config.open_clusters_stroke_width,
                                 fill = config.open_clusters_fill_color.get_hex_rgb(),
                                 fill_opacity = config.open_clusters_fill_color.get_float_alpha()))
    
    for open_cluster in open_clusters:
        dash_size = config.open_clusters_stroke_dash_size*pt
        open_clusters_dwg.add(dwg.circle(center=(open_cluster.w*pt, open_cluster.h*pt), 
                                     r=open_cluster.size*pt).dasharray([dash_size, dash_size]))
        
    return open_clusters
    
def _add_globular_clusters(dwg, config, central_quadrant):
    log.info("Adding globular clusters")
    globular_clusters = get_clusters(config, central_quadrant, cluster_type = DSO_GLOBULAR_CLUSTER)
    
    globular_clusters_dwg = dwg.add(dwg.g(id='globular_clusters', 
                                 stroke=config.globular_clusters_stroke_color.get_hex_rgb(), 
                                 stroke_opacity = config.globular_clusters_stroke_color.get_float_alpha(),
                                 stroke_width = config.globular_clusters_stroke_width,
                                 fill = config.globular_clusters_fill_color.get_hex_rgb(),
                                 fill_opacity = config.globular_clusters_fill_color.get_float_alpha()))
    
    for globular_cluster in globular_clusters:
        cluster_group = globular_clusters_dwg.add(dwg.g(id='globular_cluster_%s'%(globular_cluster.id, ), ))
        
        cluster_group.add(dwg.circle(center=(globular_cluster.w*pt, globular_cluster.h*pt), 
                                     r=globular_cluster.size*0.75*pt))
        lv_w = globular_cluster.w
        lv_h_start = globular_cluster.h - globular_cluster.size
        lv_h_end   = globular_cluster.h + globular_cluster.size
        
        lh_h = globular_cluster.h
        lh_w_start = globular_cluster.w - globular_cluster.size
        lh_w_end   = globular_cluster.w + globular_cluster.size
        
        cluster_group.add(dwg.line(start=(lv_w*pt, lv_h_start*pt), end=(lv_w*pt, lv_h_end*pt)))
        cluster_group.add(dwg.line(start=(lh_w_start*pt, lh_h*pt), end=(lh_w_end*pt, lh_h*pt)))
        
    return globular_clusters
    
def _add_constellations(dwg, config, master_stars, quadrants):
    log.info("Adding constellations")

    constellations = get_constellations(config, master_stars, quadrants)
    
    constellations_dwg = dwg.add(dwg.g(id='constellations', 
                                       stroke=config.constellation_stroke_color.get_hex_rgb(), 
                                       stroke_opacity = config.constellation_stroke_color.get_float_alpha(),
                                       stroke_width = config.constellation_stroke_width,
                                       fill = "none"))
    
    for constellation in constellations:
        for segment in constellation.segments:
            const_points = []
            for star_id in segment.star_ids:
                star = constellation.star_dict[star_id]
                const_points.append((star.w, star.h))
            
            kwargs = {}
            
            if constellation.custom_color != None:
                kwargs["stroke"] = constellation.custom_color.get_hex_rgb()
                kwargs["stroke_opacity"] = constellation.custom_color.get_float_alpha()
            
            # Finally, make a polygon with the chosen stars
            if segment.is_closed:
                constellations_dwg.add(dwg.polygon(points = const_points, **kwargs))
            else:
                constellations_dwg.add(dwg.polyline(points = const_points, **kwargs))
        
    return constellations
    
def _add_constellation_names(dwg, constellations, config):
    const_names = dwg.add(dwg.g(id='constellation_names', 
                                stroke='none',
                                fill=config.constellation_name_font.color.get_hex_rgb(),
                                fill_opacity=config.constellation_name_font.color.get_float_alpha(),
                                font_size=config.constellation_name_font.size*pt,
                                font_family=config.constellation_name_font.font_family))
    
    for constellation in constellations:
        if config.constellation_name_enable:
            kwargs = {}
            if constellation.custom_color != None:
                kwargs["fill"] = constellation.custom_color.get_hex_rgb()
                kwargs["fill_opacity"] = constellation.custom_color.get_float_alpha()
            
            w, h = constellation.get_mean_position()
            const_names.add(dwg.text(constellation.get_display_name(),
                                     insert=(w*pt, h*pt),
                                     text_anchor="middle",
                                     **kwargs,
                                     )
        )
    
def _get_chart(dwg, config, quadrant = None, master_stars = None):
    #assert quadrant == None or master_stars != None
    
    q_w = 0 if quadrant == None else quadrant.w
    q_h = 0 if quadrant == None else quadrant.h
    
    
    # stars
    if master_stars == None or draw_all_quadrants:
    
        # out box
        out_box = dwg.add(dwg.g(id='out_box', 
                                stroke=config.box_stroke_color.get_hex_rgb(), 
                                stroke_opacity=config.box_stroke_color.get_float_alpha(), 
                                fill=config.box_fill_color.get_hex_rgb(), 
                                fill_opacity=config.box_fill_color.get_float_alpha(), 
                                stroke_width = config.box_stroke_width))
        out_box.add(dwg.polygon(points=[((0 + q_w)*pt,         (0 + q_h)*pt), 
                                        ((0 + q_w)*pt,         (config.box_size.height + q_h)*pt),
                                        ((config.box_size.width + q_w)*pt, (config.box_size.height + q_h)*pt),
                                        ((config.box_size.width + q_w)*pt, (0 + q_h)*pt)]))
        
        # grid
        if config.add_grid and (config.grid_line_count_horizontal != 0 or config.grid_line_count_vertical != 0):
            grid = dwg.add(dwg.g(id='grid', 
                                 stroke=config.grid_stroke_color.get_hex_rgb(),
                                 stroke_opacity=config.grid_stroke_color.get_float_alpha(),
                                 stroke_width = config.grid_stroke_width))
            # Horizontal lines
            sep = config.box_size.height / (1 + config.grid_line_count_vertical)
            for i in range(0, config.grid_line_count_vertical):
                grid.add(dwg.line(start=((0 + q_w)*pt, (sep + sep*i + q_h)*pt), end=((config.box_size.width + q_w)*pt, (sep + sep*i + q_h)*pt)))
            # Vertical lines
            sep = config.box_size.width / (1 + config.grid_line_count_horizontal)
            for i in range(0, config.grid_line_count_horizontal):
                grid.add(dwg.line(start=((sep + sep*i + q_w)*pt, (0 + q_h)*pt), end=((sep + sep*i + q_w)*pt, (config.box_size.height + q_h)*pt)))
        
    if master_stars == None:
    
        log.info("Adding %i stars to central quadrant %s"%(config.star_count, quadrant))
        min_size = config.star_size_range[0]
        max_size = config.star_size_range[1]
    
        if config.star_random_seed != None:
            random.seed(config.star_random_seed)
    
        generated_stars = get_random_stars(min_size = min_size,
                                           max_size = max_size,
                                           max_w = config.box_size.width,
                                           max_h = config.box_size.height,
                                           color = config.star_color,
                                           star_count = config.star_count,
                                           size_random_count = config.star_size_random_count,
                                           size_distribution_power = config.star_size_distribution_power,
                                           quadrant = quadrant)
        
    else:
        generated_stars = []
        #log.info("Writting %i stars to quadrant %s"%(len(master_stars), quadrant))
        #stars_group = dwg.add(dwg.g(id='stars_group_q%s'%(quadrant.id,)))
        for master_star in master_stars:
            #w, h = quadrant.adjust_coordinates(master_star.w, master_star.h)
        
            child_star = Star(master_star = master_star, 
                              quadrant = quadrant)
            generated_stars.append(child_star)
        
            #log.debug("%s (out of %s)"%(child_star, master_star))
            #log.debug("w: %i, h: %i"%(w, h))
            
            
            #circle = dwg.circle(center = (child_star.w, child_star.h), 
            #                    r = child_star.size*pt, 
            #                    fill = child_star.color.get_hex_rgb(),
            #                    fill_opacity = child_star.color.get_float_alpha())
            #stars_group.add(circle)
            
    return generated_stars
    
