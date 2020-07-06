import os
import configparser
import re
from log_stuff import init_logger
import config_file
import svgwrite
import random
#from svgwrite import pt
pt = 1

log = init_logger()

#class RGBColorFactory:

def generate_chart(filename, config):
    log.info("Creating chart %s"%(filename,))
    dwg = svgwrite.Drawing(filename=filename, debug=True)
    
    box_width = config.box_size[0]
    box_height = config.box_size[1]
    
    # out box
    out_box = dwg.add(dwg.g(id='out_box', 
                            stroke=config.box_stroke_color.hex_value, 
                            fill=config.box_fill_color.hex_value, 
                            stroke_width = config.box_stroke_width))
    out_box.add(dwg.polygon(points=[(0*pt, 0*pt), 
                                    (0*pt, box_height*pt),
                                    (box_width*pt, box_height*pt),
                                    (box_width*pt, 0*pt)]))
    
    # grid
    if config.grid_line_count_horizontal != 0 or config.grid_line_count_vertical != 0:
        grid = dwg.add(dwg.g(id='grid', 
                             stroke=config.grid_stroke_color.hex_value,
                             stroke_width = config.grid_stroke_width))
        # Horizontal lines
        sep = box_height / (1 + config.grid_line_count_horizontal)
        for i in range(0, config.grid_line_count_horizontal):
            grid.add(dwg.line(start=(0, (sep + sep*i)*pt), end=(box_width*pt, (sep + sep*i)*pt)))
        # Vertical lines
        sep = box_width / (1 + config.grid_line_count_vertical)
        for i in range(0, config.grid_line_count_vertical):
            grid.add(dwg.line(start=((sep + sep*i)*pt, 0), end=((sep + sep*i)*pt, box_height*pt)))
    
    # stars
    min_size = config.star_size_range[0]
    max_size = config.star_size_range[1]
    size_range = max_size - min_size
    stars = dwg.add(dwg.g(id='stars'))
    if config.star_random_seed != None:
        random.seed(config.star_random_seed)
    for i in range(0, config.star_count):
        # star size
        r = 1
        for j in range(0, config.star_size_random_count): r *= random.random()
        star_size = (r**config.star_size_distribution_power) * size_range + min_size
        
        circle = dwg.circle(center = (random.random()*box_width*pt, 
                                      random.random()*box_height*pt), 
                            r = star_size*pt, 
                            fill = config.star_color.hex_value)
        stars.add(circle)
    # 
    # # override the 'fill' attribute of the parent group 'shapes'
    # shapes.add(dwg.rect(insert=(5*cm, 5*cm), size=(45*mm, 45*mm),
    #                     fill='blue', stroke='red', stroke_width=3))
    # 
    # # or set presentation attributes by helper functions of the Presentation-Mixin
    # ellipse = shapes.add(dwg.ellipse(center=(10*cm, 15*cm), r=('5cm', '10mm')))
    # ellipse.fill('green', opacity=0.5).stroke('black', width=5).dasharray([20, 20])
    
    log.info("Writting file")
    dwg.save()
