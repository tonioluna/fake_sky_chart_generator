import os
import configparser
import re
import collections
import random
from .log_stuff import init_logger
from .constellations import KNOWN_ALGORITHMS

log = init_logger()

COLOR_RANDOM_COLOR_INDEX = "random_color_index"
_known_colors = (COLOR_RANDOM_COLOR_INDEX,
                )
_re_rgb_color = re.compile("^#(?P<red>[0-9a-fA-F]{2})"
                             "(?P<green>[0-9a-fA-F]{2})"
                             "(?P<blue>[0-9a-fA-F]{2})$")

_BoxSize = collections.namedtuple("BoxSize", ("width", "height"))

class Color:
    def __init__(self, color_txt):
        self._color_txt = color_txt
        if self._color_txt in _known_colors:
            self.has_rgb = False
            self.color_name = self._color_txt
        else:
            self.set_rgb_val(self._color_txt)
    
    def set_rgb_val(self, rgb_str_hex):
        m = _re_rgb_color.match(rgb_str_hex)
        
        assert m != None, "Invalid star color: %s"%(rgb_str_hex,)
        
        self.has_rgb = True
        self._hex_value = rgb_str_hex.upper()
        self.red   = int(m.groupdict()["red"]  , 16) 
        self.green = int(m.groupdict()["green"], 16)
        self.blue  = int(m.groupdict()["blue"] , 16)
    
    def get_hex_value(self):
        if self.has_rgb:
            return self._hex_value
        raise Exception("No hex value defined for color %s"%(repr(self.color_name), ))
    
    def clone(self):
        new_color = Color(self._color_txt)
        if self.has_rgb:
            new_color.has_rgb = True
            new_color._hex_value = self._hex_value
        return new_color
             
class Font:
    def __init__(self, config, alias = None, section = None):
        assert (alias == None and section != None) or (alias != None and section == None)
        if alias != None:
            assert alias.startswith("@")
            section = alias[1:]
        assert section.startswith("font_"), "font sections must start with 'font_' (%s)"%(section, )
        assert config.has_section(section), "font section %s does not exist: %s"%(section, )
         
        self.color = Color(config.get(section, "color").strip())
        self.font_family = config.get(section, "font_family").strip()
        self.size = config.getint(section, "size")
        
             
class ConfigFile:
    def __init__(self, filename):
        self._filename = filename
        self._read()
    
    def _read(self):
        config = configparser.ConfigParser()
        log.info("Reading config parameters from %s"%(self._filename,))
        config.read(self._filename)
        
        # main parameters
        self.add_grid = config.getboolean("main", "add_grid")
        self.add_constellations = config.getboolean("main", "add_constellations")
        self.add_neighbor_quadrants = config.getboolean("main", "add_neighbor_quadrants")
        
        # Star parameters
        # star_count
        self.star_count = config.getint("star", "count")
        # star_color
        self.star_color = Color(config.get("star", "color").strip())
        # star_size_distribution_power
        self.star_size_distribution_power = config.getfloat("star", "size_distribution_power")
        assert self.star_size_distribution_power >= 1.0, "star.size_distribution_power must be >= 1.0, not %i"%(self.star_size_distribution_power,)
        # star_size_random_count
        self.star_size_random_count = config.getint("star", "size_random_count")
        assert self.star_size_random_count >= 1, "star.size_random_count must be >= 1, not %i"%(self.star_size_distribution_power,)
        # star_size_range
        self.star_size_range = [float(v.strip()) for v in config.get("star", "size_range").split(",")]
        self.star_size_range.sort()
        self.star_size_range.sort()
        assert len(self.star_size_range) == 2, "star.size_range must contain 2 items, not %i"%(len(self.star_size_range))
        #star_random_seed
        star_random_seed = config.get("star", "random_seed").strip().lower()
        if star_random_seed == "none":
            self.star_random_seed = random.randint(0, 1000000)
            log.info("Setting star_random_seed = %i"%(self.star_random_seed))
        else:
            self.star_random_seed = int(star_random_seed)
        
        # box parameters
        # box_size
        box_size = [int(v.strip()) for v in config.get("box", "size").split(",")]
        assert len(box_size) == 2, "box.size must contain 2 items, not %i"%(len(box_size))
        self.box_size = _BoxSize(*box_size)
        # box_stroke_width
        self.box_stroke_width = config.getfloat("box", "stroke_width")
        #box_stroke_color
        self.box_stroke_color = Color(config.get("box", "stroke_color").strip())
        #box_fill_color
        self.box_fill_color = Color(config.get("box", "fill_color").strip())

        # constellation parameters
        if self.add_constellations:
            self.constellation_count = config.getint("constellation", "count")
            self.constellation_star_count = [int(v.strip()) for v in config.get("constellation", "star_count").split(",")]
            assert len(self.constellation_star_count) in (1,2), "constellation.star_count must contain 1 or 2 items, not %i"%(len(self.box_size))
            #star_random_seed
            constellation_random_seed = config.get("constellation", "random_seed").strip().lower()
            if constellation_random_seed == "none":
                self.constellation_random_seed = random.randint(0, 1000000)
                log.info("Setting constellation_random_seed = %i"%(self.constellation_random_seed))
            else:
                self.constellation_random_seed = int(constellation_random_seed)
            # constellation_stroke_width
            self.constellation_stroke_width = config.getfloat("constellation", "stroke_width")
            # constellation_stroke_color
            self.constellation_stroke_color = Color(config.get("constellation", "stroke_color").strip())
            # algorithm
            self.constellation_algorithm = config.get("constellation", "algorithm").strip()
            assert self.constellation_algorithm in KNOWN_ALGORITHMS, "Invalid value for constellation.algorithm: %s. Valid: %s"%(self.constellation_algorithm, ", ".join(KNOWN_ALGORITHMS))
            
            self.constellation_name_enable = config.getboolean("constellation", "name_enable")
            if self.constellation_name_enable:
                constellation_name_random_seed = config.get("constellation", "name_random_seed").strip().lower()
                if constellation_name_random_seed == "none":
                    self.constellation_name_random_seed = random.randint(0, 1000000)
                    log.info("Setting constellation_name_random_seed = %i"%(self.constellation_name_random_seed))
                else:
                    self.constellation_name_random_seed = int(constellation_name_random_seed)
                self.constellation_name_font = Font(config, alias = config.get("constellation", "name_font"))
            
        # grid parameters
        if self.add_grid:
            # grid_stroke_width
            self.grid_stroke_width = config.getfloat("grid", "stroke_width")
            # grid_stroke_color
            self.grid_stroke_color = Color(config.get("grid", "stroke_color").strip())
            # grid_line_count_horizontal
            self.grid_line_count_horizontal = config.getint("grid", "line_count_horizontal")
            assert self.grid_line_count_horizontal >= 0, "grid.line_count_horizontal must be >= 0, not %i"%(self.grid_line_count_horizontal,)
            # grid_line_count_vertical
            self.grid_line_count_vertical = config.getint("grid", "line_count_vertical")
            assert self.grid_line_count_vertical >= 0, "grid.line_count_vertical must be >= 0, not %i"%(self.grid_line_count_vertical,)
            