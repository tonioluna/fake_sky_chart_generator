import re
from .log_stuff import init_logger

log = init_logger()

COLOR_RANDOM_COLOR_INDEX = "random_color_index"
COLOR_RANDOM_COLOR_INDEX_INVERTED = "random_color_index_inverted"
COLOR_RANDOM_COLOR_INDEX_INVERTED_LIGHT = "random_color_index_inverted_light"
_known_colors = (COLOR_RANDOM_COLOR_INDEX,
                 COLOR_RANDOM_COLOR_INDEX_INVERTED,
                 COLOR_RANDOM_COLOR_INDEX_INVERTED_LIGHT
                )
COLORS_FROM_START_INDEX = (COLOR_RANDOM_COLOR_INDEX,
                           COLOR_RANDOM_COLOR_INDEX_INVERTED,
                           COLOR_RANDOM_COLOR_INDEX_INVERTED_LIGHT
                          )
_re_rgb_color = re.compile("^#(?P<red>[0-9a-fA-F]{2})"
                             "(?P<green>[0-9a-fA-F]{2})"
                             "(?P<blue>[0-9a-fA-F]{2})"
                             "(?P<alpha>[0-9a-fA-F]{2})?$")

debug_colors = ("#FF0000FF",
                "#00FF00FF",
                "#0000FFFF",
                "#FF8000FF",
                "#FF0080FF",
                "#80FF00FF",
                "#00FF80FF",
                "#8000FFFF",
                "#0080FFFF",
                )
                             
class Color:
    def __init__(self, color_txt):
        self._color_txt = color_txt
        if self._color_txt in _known_colors:
            self.has_rgb = False
            self.color_name = self._color_txt
        else:
            self.set_rgb_val(self._color_txt)
            self.color_name = None
    
    def set_rgb_val(self, rgb_str_hex):
        m = _re_rgb_color.match(rgb_str_hex)
        
        assert m != None, "Invalid star color: %s"%(rgb_str_hex,)
        
        self.has_rgb = True
        d = m.groupdict()
        self.red   = int(d["red"]  , 16) 
        self.green = int(d["green"], 16)
        self.blue  = int(d["blue"] , 16)
        alpha = d["alpha"]
        self.alpha = int(alpha, 16) if alpha != None else 0xFF
    
    def get_hex_rgb(self):
        return self.get_hex(False)
    
    def get_hex_rgba(self):
        return self.get_hex(True)
    
    def get_hex(self, with_alpha):
        if self.has_rgb:
            txt = "#%02X%02X%02X"%(self.red, self.green, self.blue)
            if with_alpha:
                txt += "%02X"%(self.alpha)
            return txt
        raise Exception("No hex value defined for color %s"%(repr(self.color_name), ))
    
    def get_100_alpha(self):
        return int(self.alpha / 2.55)
    
    def get_float_alpha(self):
        return self.alpha / 255.0
    
    def get_svg_color(self):
        return svgwrite.solidcolor.SolidColor(color = self.get_hex_rgb(), 
                                              opacity = self.get_float_alpha())
    
    def clone(self):
        new_color = Color(self._color_txt)
        if self.has_rgb:
            new_color.has_rgb = True
            new_color.set_rgb_val(self.get_hex_rgba())
        return new_color
    
    def __repr__(self):
        return "<%s>"%(self.__str__())
    
    def __str__(self):
        c = ["Color"]
        if self.color_name != None: c.append("%s"%(repr(self.color_name)))
        if self.has_rgb: 
            c.append("RBGA: %02X%02X%02X%02X"%(self.red, self.green, self.blue, self.alpha))
        else:
            c.append("(RGB[A] not defined")
        return " ".join(c)

    def set_star_color_index(self, color_index):
        # color_index <-0.4,+2.0> 
        assert type(color_index) in (int, float)
        assert self.color_name in COLORS_FROM_START_INDEX
        ci = float(color_index)
        if (ci < -0.4): 
            ci = -0.4 
        if (ci > 2.0):
            ci =  2.0
        # R
        if (( ci >= -0.40 ) and ( ci < 0.00 )):
            t = (ci + 0.40) / (0.00 + 0.40)
            r = 0.61 + (0.11 * t) + ( 0.1 * t * t)
        elif ((ci >= 0.00 ) and ( ci < 0.40)):
            t = (ci - 0.00) / (0.40 - 0.00)
            r = 0.83 + (0.17 * t)
        elif ((ci >= 0.40 ) and ( ci <= 2.10)):
            t = (ci - 0.40) / (2.10 - 0.40)
            r = 1.00
        #G
        if (( ci >= -0.40 ) and ( ci < 0.00 )):
            t = (ci + 0.40) / (0.00 + 0.40)
            g = 0.70 + (0.07 * t) + (0.1 * t * t )
        elif (( ci >= 0.00) and ( ci < 0.40)):
            t = (ci - 0.00) / (0.40 - 0.00)
            g = 0.87 + (0.11 * t)
        elif (( ci >= 0.40) and ( ci < 1.60)):
            t = (ci - 0.40) / (1.60 - 0.40)
            g = 0.98 - (0.16 * t)
        elif (( ci >= 1.60 ) and ( ci <= 2.00)):
            t = (ci - 1.60) / (2.00 - 1.60)
            g = 0.82 - (0.5 * t * t)
        # B     
        if (( ci >= -0.40) and ( ci < 0.40)):
            t = (ci + 0.40) /(0.40 + 0.40)
            b = 1.00
        elif (( ci >= 0.40) and ( ci <1.50)):
            t = (ci - 0.40) / (1.50 - 0.40)
            b = 1.00 - (0.47 * t) + (0.1 * t * t )
        elif (( ci >= 1.50) and ( ci <=1.94)):
            t = (ci - 1.50) / (1.94 - 1.50)
            b = 0.63 - (0.6 * t * t )
        else:
            b = 0
        #return (r, g, b)
        
        if self.color_name == COLOR_RANDOM_COLOR_INDEX:        
            color = "#%02X%02X%02X"%(int(r*255),
                                     int(g*255),
                                     int(b*255))
        elif self.color_name == COLOR_RANDOM_COLOR_INDEX_INVERTED:        
            color = "#%02X%02X%02X"%(int(r*255) ^ 0xFF,
                                     int(g*255) ^ 0xFF,
                                     int(b*255) ^ 0xFF)
        elif self.color_name == COLOR_RANDOM_COLOR_INDEX_INVERTED_LIGHT: 
            v = []
            for c in (r, g, b):
                c = (int(r*255) ^ 0xFF)
                c = int( 255 - ((255-c) * 0.3))
                v.append(c)

            color = "#%02X%02X%02X"%(tuple(v))
        else:
            raise Exception("Internal error")
        self.set_rgb_val(color)
    
