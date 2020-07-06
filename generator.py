import sys
import os
import traceback
import svgwrite
from svgwrite import cm, mm   
import config_file
from log_stuff import init_logger
from svg_support import generate_chart

log = init_logger()

_my_path = os.path.abspath(os.path.dirname(sys.argv[0]))
DEFAULT_CFG_FILE = os.path.join(_my_path, "default_config.ini")

def main():
    try:
        # Read config file info
        if len(sys.argv) == 1:
            log.info("Using default config file: %s"%(DEFAULT_CFG_FILE,))
            config_filename = DEFAULT_CFG_FILE
        else:
            assert len(sys.argv) == 2, "Only one argument is supported, not multiple"
            config_filename = sys.argv[1]
            log.info("Using user'defined config file: %s"%(config_filename,))
        
        assert os.path.isfile(config_filename), "Config file does not exist: %s"%(config_filename,)
        
        config = config_file.ConfigFile(config_filename)
        
        generate_chart("chart.svg", config)
        
    
    except Exception as ex:
        log.fatal("Caught top level error: %s"%(ex,))
        log.debug(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())