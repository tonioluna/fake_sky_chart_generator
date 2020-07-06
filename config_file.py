import os
import configparser
import re
from log_stuff import init_logger

log = init_logger()

COLOR_STARS_COMMON = "stars_common"
_known_colors = (COLOR_STARS_COMMON,
                )
_re_rgb_color = re.compile("^#(?P<red>[0-9a-fA-F]{2})"
                             "(?P<green>[0-9a-fA-F]{2})"
                             "(?P<blue>[0-9a-fA-F]{2})?")

class Color:
    def __init__(self, color_txt):
        self._color_txt = color_txt
        m = _re_rgb_color.match(self._color_txt)
        if m != None:
            self.is_rgb = True
            self.hex_value = self._color_txt.upper()
            self.red   = int(m.groupdict()["red"]  , 16) 
            self.green = int(m.groupdict()["green"], 16)
            self.blue  = int(m.groupdict()["blue"] , 16)
        else:
            assert self._color_txt in _known_colors, "Invalid color: %s"%(self._color_txt,)
            self.is_rgb = False
            self.color_name = self._color_txt
                             
class ConfigFile:
    def __init__(self, filename):
        self._filename = filename
        self._read()
    
    def _read(self):
        config = configparser.ConfigParser()
        log.info("Reading config parameters from %s"%(self._filename,))
        config.read(self._filename)
        
        # Star parameters
        # star_count
        self.star_count = config.getint("parameters", "star_count")
        # star_color
        self.star_color = Color(config.get("parameters", "star_color").strip())
        # star_size_distribution_power
        self.star_size_distribution_power = config.getfloat("parameters", "star_size_distribution_power")
        assert self.star_size_distribution_power >= 1.0, "star_size_distribution_power must be >= 1.0, not %i"%(self.star_size_distribution_power,)
        # star_size_random_count
        self.star_size_random_count = config.getint("parameters", "star_size_random_count")
        assert self.star_size_random_count >= 1, "star_size_random_count must be >= 1, not %i"%(self.star_size_distribution_power,)
        # star_size_range
        self.star_size_range = [float(v.strip()) for v in config.get("parameters", "star_size_range").split(",")]
        self.star_size_range.sort()
        self.star_size_range.sort()
        assert len(self.star_size_range) == 2, "star_size_range must contain 2 items, not %i"%(len(self.star_size_range))
        #star_random_seed
        star_random_seed = config.get("parameters", "star_random_seed").strip().lower()
        if star_random_seed == "none":
            self.star_random_seed = None
        else:
            self.star_random_seed = int(star_random_seed)
        
        # box parameters
        # box_size
        self.box_size = [int(v.strip()) for v in config.get("parameters", "box_size").split(",")]
        assert len(self.box_size) == 2, "box_size must contain 2 items, not %i"%(len(self.box_size))
        # box_stroke_width
        self.box_stroke_width = config.getfloat("parameters", "box_stroke_width")
        #box_stroke_color
        self.box_stroke_color = Color(config.get("parameters", "box_stroke_color").strip())
        #box_fill_color
        self.box_fill_color = Color(config.get("parameters", "box_fill_color").strip())

        # grid parameters
        # grid_stroke_width
        self.grid_stroke_width = config.getfloat("parameters", "grid_stroke_width")
        # grid_stroke_color
        self.grid_stroke_color = Color(config.get("parameters", "grid_stroke_color").strip())
        # grid_line_count_horizontal
        self.grid_line_count_horizontal = config.getint("parameters", "grid_line_count_horizontal")
        assert self.grid_line_count_horizontal >= 0, "grid_line_count_horizontal must be >= 0, not %i"%(self.grid_line_count_horizontal,)
        # grid_line_count_vertical
        self.grid_line_count_vertical = config.getint("parameters", "grid_line_count_vertical")
        assert self.grid_line_count_vertical >= 0, "grid_line_count_vertical must be >= 0, not %i"%(self.grid_line_count_vertical,)
        