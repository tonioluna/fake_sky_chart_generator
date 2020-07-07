import os
import sys
import logging
import time

def init_logger():
    _me = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    
    log = logging.getLogger(_me)
    if not log.hasHandlers():
        
        log.setLevel(logging.DEBUG)
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        filename = _me + ".log"
        with open(filename, "w") as fh:
            fh.write("Starting on %s running from %s"%(time.ctime(), repr(sys.argv)))
        fh = logging.FileHandler(filename = filename)
        fh.setLevel(logging.DEBUG)
        
        # create formatter
        formatter = logging.Formatter('%(levelname)s - %(message)s')
        
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        
        log.addHandler(ch)
        log.addHandler(fh)
    return log