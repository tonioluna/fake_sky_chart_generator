import re
from .log_stuff import init_logger

log = init_logger()

COLOR_RANDOM_COLOR_INDEX = "random_color_index"
_known_colors = (COLOR_RANDOM_COLOR_INDEX,
                )
_re_rgb_color = re.compile("^#(?P<red>[0-9a-fA-F]{2})"
                             "(?P<green>[0-9a-fA-F]{2})"
                             "(?P<blue>[0-9a-fA-F]{2})"
                             "(?P<alpha>[0-9a-fA-F]{2})?$")

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
    
    def __str__(self):
        c = ["Color"]
        if self.color_name != None: c.append("%s"%(repr(self.color_name)))
        if self.has_rgb != None: 
            c.append("RBGA: %02X%02X%02X%02X"%(self.red, self.green, self.blue, self.alpha))
        else:
            c.append("(RGB[A] not defined")
        return " ".join(c)
