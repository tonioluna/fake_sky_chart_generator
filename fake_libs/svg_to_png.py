import sys
import os
from fake_libs.log_stuff import init_logger

log = init_logger()

SVG_TO_PNG_METHOD_WAND = "wand"
KNOWN_SVG_TO_PNG_METHODS = (SVG_TO_PNG_METHOD_WAND,)

def convert(method, svg_file, png_file = None, resolution = 72):
    assert method in KNOWN_SVG_TO_PNG_METHODS
    if png_file == None:
        png_file = os.path.splitext(svg_file)[0] + ".png"
    
    log.info("Exporting %s to PNG as %s using method %s, resolution: %s"%(svg_file, png_file, method, resolution))
    
    if method == SVG_TO_PNG_METHOD_WAND:
        # do imports here, in case these modules are not installed import error won't happen unless user attempts to run this code
        from wand.api import library
        import wand.color
        import wand.image

        with open(svg_file, "r") as svg_file:
            with wand.image.Image() as image:
                with wand.color.Color('transparent') as background_color:
                    library.MagickSetBackgroundColor(image.wand, 
                                                     background_color.resource) 
                svg_blob = svg_file.read().encode('utf-8')
                image.read(blob=svg_blob, resolution = resolution)
                png_image = image.make_blob("png32")

        with open(png_file, "wb") as out:
            out.write(png_image)
    else:
        raise Exception("Internal error, unimplemented method: %s"%(method, ))
    
    return png_file