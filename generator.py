import sys
import os
import traceback
import argparse
from fake_libs.config_file import ConfigFile
from fake_libs.log_stuff import init_logger
from fake_libs.charts import generate_chart
from fake_libs.svg_to_png import KNOWN_SVG_TO_PNG_METHODS, convert

log = init_logger()

_default_png_resolution = 400
_my_path = os.path.abspath(os.path.dirname(sys.argv[0]))
DEFAULT_CFG_FILE = os.path.join(_my_path, "charts", "default_config.ini")

def _get_args():

    parser = argparse.ArgumentParser(description='Fake sky chart generator')
    parser.add_argument('ini_files', metavar='N', type=str, nargs='*',
                        help='One or more ini files to describe the chart to generate.')
    parser.add_argument('-f', '--svg_filename', dest='svg_filename', metavar='<FILENAME>',
                        default=None, help='Custom filename for the SVG file.')
    parser.add_argument('-e', '--export_parameters', dest='export_parameters', metavar='<FILENAME>',
                        default=None, help='Export parameters in text format.')
    parser.add_argument('-p', '--convert_to_png', dest='convert_to_png', metavar='<METHOD>',
                        default=None, help='Convert the generated SVG to PNG using the specified method.')
    parser.add_argument('-r', '--png_resolution', dest='png_resolution', metavar='<int>(dpi)',
                        default=_default_png_resolution, help='DPI resolution for PNG conversion. Default: %(default)s.')
    parser.add_argument('-O', '--open_png', dest='open_png', action="store_true",
                        default=False, help='Open PNG file when done')
    parser.add_argument('-o', '--open_svg', dest='open_svg', action="store_true",
                        default=False, help='Open SVG file when done')
    
    args = parser.parse_args()
    
    if len(args.ini_files) == 0:
        log.info("Using default config file: %s"%(DEFAULT_CFG_FILE,))
        args.ini_files = [DEFAULT_CFG_FILE]
    args.ini_files = [os.path.abspath(f) for f in args.ini_files]
    
    if args.svg_filename == None:
        args.svg_filename = "chart.%s.svg"%(".".join([os.path.splitext(os.path.basename(f))[0] for f in args.ini_files]))
    else:
        assert os.path.splitext(args.svg_filename)[1].lower() == ".svg", "--svg_filename must have .svg extension: %s"%(args.svg_filename,)

    if args.convert_to_png != None:
        assert args.convert_to_png in KNOWN_SVG_TO_PNG_METHODS, "--KNOWN_SVG_TO_PNG_METHODS must be one of %s, not %s"%(",".join(KNOWN_SVG_TO_PNG_METHODS), args.convert_to_png)
        
    if args.export_parameters == "AUTO":
        args.export_parameters = os.path.splitext(args.svg_filename)[0] + ".txt"
        
    return args
        
def main():
    try:
        args = _get_args()
        
        for file in args.ini_files:
            assert os.path.isfile(file), "Config file does not exist: %s"%(file,)
        
        config = ConfigFile(args.ini_files)
        
        if args.export_parameters:
            config.log(file = args.export_parameters)
        
        generate_chart(args.svg_filename, config)
        
        if args.convert_to_png:
            png_file = convert(method = args.convert_to_png, svg_file = args.svg_filename, resolution = args.png_resolution)
            
        if args.open_svg:
            log.info("Opening SVG")
            os.system(args.svg_filename)
        if args.convert_to_png and args.open_png:
            log.info("Opening PNG")
            os.system(png_file)
    
    except Exception as ex:
        log.fatal("Caught top level error: %s"%(ex,))
        log.debug(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())