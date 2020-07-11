from .log_stuff import init_logger
from .stars import Star
from .constellations_common import *
from .constellation_algorithms.algorithms import call_algorithm
import random
import operator
import math
import os

log = init_logger()

_my_path = os.path.abspath(os.path.dirname(__file__))
_default_constellation_names_file = os.path.join(_my_path, "..", "doc", "constellation_names.txt")

def get_constellations(config, master_stars, quadrants):
    sorted_stars = list(sorted(master_stars, key=operator.attrgetter('size')))
    
    if config.constellation_random_seed != None:
        random.seed(config.constellation_random_seed)
    
    log.info("Constellations algorithm: %s"%(config.constellation_algorithm, ))
    constellations = call_algorithm(config.constellation_algorithm, config, sorted_stars, quadrants)
    
    # name constellations
    const_names = ConstellationNames(filename = _default_constellation_names_file if config.constellation_name_custom_source == None else config.constellation_name_custom_source)
    if config.constellation_name_random_seed != None:
        random.seed(config.constellation_name_random_seed)
    for const in constellations:
        const.name = const_names.get_random_constellation_name()

    log.info("Creating constellation copies")
    constellation_copies = []
    for constellation in constellations:
        constellation_copies.extend(constellation.get_copies())
    
    constellations.extend(constellation_copies)

    return constellations        
        
