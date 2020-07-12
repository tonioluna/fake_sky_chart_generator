import os
import sys
import logging
import time
import colorama

colorama.init()
    
class LoggerWrapper:
    
    def __init__(self, parent_logger):
        self._parent_logger = parent_logger
        self._last_method = None

    def __getattr__(self, key):
        if key == "debug":
            sys.stdout.write(colorama.Fore.CYAN)
        elif key == "warning":
            sys.stdout.write(colorama.Fore.YELLOW)
        elif key in ("error", "fatal"):
            sys.stdout.write(colorama.Fore.RED)
        else:
            sys.stdout.write(colorama.Fore.RESET)
        
        self._last_method = getattr(self._parent_logger, key)
        return self._handler
        
    def _handler(self, *arg, **kwargs):
        rv = self._last_method(*arg, **kwargs)
        self._last_method = None
        sys.stdout.write(colorama.Fore.RESET)
        return rv
        
def init_logger():
    _me = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    
    log = logging.getLogger(_me)
    if not log.hasHandlers():
        
        log.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        filename = _me + ".log"
        with open(filename, "w") as fh:
            fh.write("Starting on %s running from %s\n"%(time.ctime(), repr(sys.argv)))
        fh = logging.FileHandler(filename = filename)
        fh.setLevel(logging.DEBUG)
        
        # create formatter
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        
        log.addHandler(ch)
        log.addHandler(fh)
    
    #log = LoggerWrapper(log)
    
    return log