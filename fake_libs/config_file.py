import os
import configparser
import collections
import random
from .log_stuff import init_logger
from .constellation_algorithms.algorithms import KNOWN_ALGORITHMS
from .constellations_common import KNOWN_NAME_DISPLAY_STYLES
from .color import Color, COLOR_RANDOM_COLOR_INDEX
import svgwrite

log = init_logger()

_BoxSize = collections.namedtuple("BoxSize", ("width", "height"))
             
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
    
    def __repr__(self):
        return "<%s>"%(self.__str__())
    
    def __str__(self):
        return "Font, family: %s, size: %i, color: %s"%(self.font_family, self.size, self.color)
             
class ConfigFile:
    def __init__(self, filenames):
        self._filenames = filenames
        self._read()
        self.log()

    def log(self, file = None):
        attribs = dir(self)
        attribs.sort()
        lines = []
        for a in attribs:
            if a.startswith("_"): continue
            attr = getattr(self, a)
            if callable(attr): continue
            n = a + ("."*(max(0, 40 - len(a))))
            lines.append("%s: %s"%(n, repr(getattr(self, a))))
        
        if file == None:
            log.debug("Config file values:")
            for line in lines:
                log.debug(line)
        else:
            log.info("Exporting parameters to %s"%(file,))
            with open(file, "w") as fh:
                fh.write("Config file values:\n")
                for line in lines:
                    fh.write(line + "\n")
    
    def _read_int_range(self, config, section, option, l = 2):
        val = [int(v.strip()) for v in config.get(section, option).split(",")]
        assert len(val) == l, "%s.%s must contain %i items, not %i"%(l, len(val))
        return val
    
    def _read_float_range(self, config, section, option, l = 2):
        val = [float(v.strip()) for v in config.get(section, option).split(",")]
        assert len(val) == l, "%s.%s must contain %i items, not %i"%(l, len(val))
        return val
    
    def _read_int_none(self, config, section, option):
        v = config.get(section, option).strip().lower()
        if v == "none":
            v = random.randint(0, 1000000)
            log.info("Setting %s.%s = %i"%(section, option, v))
        else:
            v = int(v)
        return v
    
    def _read_file_none(self, config, section, option):
        v = config.get(section, option).strip().lower()
        if v == "none":
            return None
        v = v.replace("\\", os.path.sep).replace("/", os.path.sep)
        v = os.path.abspath(os.path.join(os.path.dirname(self._filenames[0]), v))
        return v
    
    def _read(self):
        config = configparser.ConfigParser()
        log.info("Reading config parameters from %s"%(",".join(self._filenames,)))
        config.read(self._filenames)
        
        # main parameters
        self.add_grid = config.getboolean("main", "add_grid")
        self.add_galaxies = config.getboolean("main", "add_galaxies")
        self.add_open_clusters = config.getboolean("main", "add_open_clusters")
        self.add_globular_clusters = config.getboolean("main", "add_globular_clusters")
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
        self.star_size_range = self._read_float_range(config, "star", "size_range")
        self.star_size_range.sort()
        #star_random_seed
        self.star_random_seed = self._read_int_none(config, "star", "random_seed")
        
        # box parameters
        # box_size
        self.box_size = _BoxSize(*self._read_int_range(config, "box", "size"))
        # box_stroke_width
        self.box_stroke_width = config.getfloat("box", "stroke_width")
        #box_stroke_color
        self.box_stroke_color = Color(config.get("box", "stroke_color").strip())
        #box_fill_color
        self.box_fill_color = Color(config.get("box", "fill_color").strip())
        
        # constellation parameters
        if self.add_constellations:
            self.constellation_count_range = self._read_int_range(config, "constellation", "count_range")
            self.constellation_star_count_range = self._read_int_range(config, "constellation", "star_count_range")
            #star_random_seed
            self.constellation_random_seed = self._read_int_none(config, "constellation", "random_seed")
            # constellation_stroke_width
            self.constellation_stroke_width = config.getfloat("constellation", "stroke_width")
            # constellation_stroke_color
            self.constellation_stroke_color = Color(config.get("constellation", "stroke_color").strip())
            # algorithm
            self.constellation_algorithm = config.get("constellation", "algorithm").strip()
            assert self.constellation_algorithm in KNOWN_ALGORITHMS, "Invalid value for constellation.algorithm: %s. Valid: %s"%(self.constellation_algorithm, ", ".join(KNOWN_ALGORITHMS))
            # name_display_style
            self.constellation_name_display_style = name = config.get("constellation", "name_display_style").strip()
            assert self.constellation_name_display_style in KNOWN_NAME_DISPLAY_STYLES, "Invalid value for constellation.name_display_style: %s. Valid: %s"%(self.constellation_name_display_style, ", ".join(KNOWN_NAME_DISPLAY_STYLES))
            
            self.constellation_name_enable = config.getboolean("constellation", "name_enable")
            if self.constellation_name_enable:
                self.constellation_name_random_seed = self._read_int_none(config, "constellation", "name_random_seed")
                self.constellation_name_font = Font(config, alias = config.get("constellation", "name_font"))
                self.constellation_name_custom_source = self._read_file_none(config, "constellation", "name_custom_source")
            
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
        
        # galaxy parameters
        if self.add_galaxies:
            # galaxies_stroke_width
            self.galaxies_stroke_width = config.getfloat("galaxies", "stroke_width")
            # galaxies_stroke_color
            self.galaxies_stroke_color = Color(config.get("galaxies", "stroke_color").strip())
            # galaxies_fill_color
            self.galaxies_fill_color = Color(config.get("galaxies", "fill_color").strip())
            #galaxies_random_seed
            self.galaxies_random_seed = self._read_int_none(config, "galaxies", "random_seed")
            # galaxies_size_range
            self.galaxies_size_range = self._read_float_range(config, "galaxies", "size_range")
            # galaxies_count_range
            self.galaxies_count_range = self._read_int_range(config, "galaxies", "count_range")
            # eccentricity range
            self.galaxies_eccentricity_range = self._read_float_range(config, "galaxies", "eccentricity_range")
            self.galaxies_eccentricity_range.sort()
            assert min(self.galaxies_eccentricity_range) > 0 and max(self.galaxies_eccentricity_range) < 1, "galaxies.eccentricity_range must be > 0 and < 1, not %s"%(repr(self.galaxies_eccentricity_range),)
        
        # open clusters parameters
        if self.add_open_clusters:
            # open_clusters_stroke_width
            self.open_clusters_stroke_width = config.getfloat("open_clusters", "stroke_width")
            # open_clusters_stroke_color
            self.open_clusters_stroke_color = Color(config.get("open_clusters", "stroke_color").strip())
            # open_clusters_fill_color
            self.open_clusters_fill_color = Color(config.get("open_clusters", "fill_color").strip())
            #open_clusters_random_seed
            self.open_clusters_random_seed = self._read_int_none(config, "open_clusters", "random_seed")
            # open_clusters_size_range
            self.open_clusters_size_range = self._read_float_range(config, "open_clusters", "size_range")
            # open_clusters_count_range
            self.open_clusters_count_range = self._read_int_range(config, "open_clusters", "count_range")
            # open_clusters_stroke_dash_size
            self.open_clusters_stroke_dash_size = config.getfloat("open_clusters", "stroke_dash_size")
        
        # globular clusters parameters
        if self.add_globular_clusters:
            # globular_clusters_stroke_width
            self.globular_clusters_stroke_width = config.getfloat("globular_clusters", "stroke_width")
            # globular_clusters_stroke_color
            self.globular_clusters_stroke_color = Color(config.get("globular_clusters", "stroke_color").strip())
            # globular_clusters_fill_color
            self.globular_clusters_fill_color = Color(config.get("globular_clusters", "fill_color").strip())
            #globular_clusters_random_seed
            self.globular_clusters_random_seed = self._read_int_none(config, "globular_clusters", "random_seed")
            # globular_clusters_size_range
            self.globular_clusters_size_range = self._read_float_range(config, "globular_clusters", "size_range")
            # globular_clusters_count_range
            self.globular_clusters_count_range = self._read_int_range(config, "globular_clusters", "count_range")
            # globular_clusters_stroke_dash_size
            self.globular_clusters_stroke_dash_size = config.getfloat("globular_clusters", "stroke_dash_size")
            