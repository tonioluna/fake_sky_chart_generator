import sys
import os
import traceback
import svgwrite
from svgwrite import cm, mm   
from fake_libs.config_file import ConfigFile
from fake_libs.log_stuff import init_logger
from fake_libs.charts import generate_chart

log = init_logger()

_my_path = os.path.abspath(os.path.dirname(sys.argv[0]))
DEFAULT_CFG_FILE = os.path.join(_my_path, "charts", "default_config.ini")

def main():
    try:
        # Read config file info
        if len(sys.argv) == 1:
            log.info("Using default config file: %s"%(DEFAULT_CFG_FILE,))
            config_filenames = [DEFAULT_CFG_FILE]
        else:
            assert len(sys.argv) == 2, "Only one argument is supported, not multiple"
            config_filenames = sys.argv[1].split(",")
            log.info("Using user'defined config files: %s"%(config_filenames,))
        
        for file in config_filenames:
            assert os.path.isfile(file), "Config file does not exist: %s"%(file,)
        
        config = ConfigFile(config_filenames)
        
        generate_chart("chart.%s.svg"%(os.path.splitext(os.path.basename(config_filenames[0]))[0], ), config)
    
    except Exception as ex:
        log.fatal("Caught top level error: %s"%(ex,))
        log.debug(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())